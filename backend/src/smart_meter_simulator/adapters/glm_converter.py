"""
GLM ↔ Pandapower Converter for GridTokenX Smart Meter Simulator.

Parses GridLAB-D .glm model files and converts them to pandapower Networks,
enabling TESP feeder topologies without requiring the GridLAB-D binary.

Supports the GLM object subset relevant to power flow analysis:
  node/substation → bus, load → load, overhead_line/underground_line → line,
  transformer + transformer_configuration → trafo, regulator → trafo, switch → switch.

Reference: https://gridlab-d.shoutwiki.com/wiki/Power_Flow_User_Guide
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import pandapower as pp

logger = logging.getLogger(__name__)

# ── GLM tokenizer ──────────────────────────────────────────────────────────


class GLMToken:
    """A parsed GLM object with its type, name, and properties."""

    __slots__ = ("obj_type", "name", "properties", "children", "parent")

    def __init__(self, obj_type: str, name: str = ""):
        self.obj_type = obj_type
        self.name = name
        self.properties: Dict[str, Any] = {}
        self.children: List["GLMToken"] = []
        self.parent: Optional[str] = None

    def __repr__(self) -> str:
        return f"GLMToken({self.obj_type}, name={self.name!r})"


class GLMParser:
    """
    Minimal GLM file parser.

    Handles:
    - ``object <type> { ... }`` blocks (with nesting)
    - ``#define VAR=value`` and ``#include`` directives (skipped)
    - ``#ifdef / #else / #endif`` conditional blocks (flattened)
    - ``#set`` directives (skipped)
    - C-style ``//`` comments
    - ``module <name> { ... }`` blocks (skipped)

    Returns a flat list of :class:`GLMToken` objects.
    """

    # Regex for parsing a property line like:  key value;
    _PROP_RE = re.compile(r"^\s*(\w[\w_-]*)\s+(.+?)\s*;\s*$")
    # Regex for name annotations:  name <value>;
    _NAME_RE = re.compile(r'^\s*name\s+(.+?)\s*;\s*$')
    # Regex for parent annotations:  parent <value>;
    _PARENT_RE = re.compile(r'^\s*parent\s+(.+?)\s*;\s*$')

    def __init__(self):
        self._defines: Dict[str, str] = {}

    def parse(self, glm_path: Path) -> List[GLMToken]:
        """Parse a GLM file and return a list of top-level GLMTokens."""
        text = Path(glm_path).read_text(encoding="utf-8", errors="replace")
        # Strip C-style comments
        text = re.sub(r"//[^\n]*", "", text)
        tokens = self._parse_block_iter(text)
        return tokens

    # ── internal ────────────────────────────────────────────────────────────

    def _expand(self, value: str) -> str:
        """Expand ${VAR} references using known #defines."""
        def _repl(m: re.Match) -> str:
            key = m.group(1)
            return self._defines.get(key, m.group(0))

        return re.sub(r"\$\{(\w+)\}", _repl, value)

    def _parse_block_iter(self, text: str) -> List[GLMToken]:
        """Tokenize GLM text into GLMToken objects."""
        tokens: List[GLMToken] = []
        stack: List[Tuple[str, GLMToken | None]] = []  # (context, token_or_none)
        i = 0
        n = len(text)

        while i < n:
            # skip whitespace
            while i < n and text[i] in " \t\r\n":
                i += 1
            if i >= n:
                break

            # ── preprocessor directives ──────────────────────────────────────
            if text[i] == "#":
                # Find end of line
                eol = text.find("\n", i)
                if eol == -1:
                    eol = n
                directive = text[i:eol].strip()

                if directive.startswith("#define"):
                    m = re.match(r"#define\s+(\w+)\s*=\s*(.+)", directive)
                    if m:
                        self._defines[m.group(1)] = m.group(2).strip()
                # Skip #include, #set, #ifdef, #else, #endif
                i = eol + 1
                continue

            # ── module blocks (skip entirely) ────────────────────────────────
            if text[i:].startswith("module"):
                j = i + 6
                while j < n and text[j] in " \t":
                    j += 1
                # Find opening brace
                brace = text.find("{", j)
                if brace != -1:
                    close = self._find_matching_brace(text, brace)
                    i = close + 1 if close != -1 else n
                    continue

            # ── object blocks ────────────────────────────────────────────────
            if text[i:].startswith("object"):
                j = i + 6
                while j < n and text[j] in " \t":
                    j += 1
                # Read object type until '{' or whitespace
                k = j
                while k < n and text[k] not in " \t\n{":
                    k += 1
                obj_type = text[j:k]
                # Find opening brace
                brace = text.find("{", k)
                if brace == -1:
                    i = k
                    continue

                token = GLMToken(obj_type)
                # Parse contents until matching '}'
                close = self._find_matching_brace(text, brace)
                if close == -1:
                    i = brace + 1
                    continue

                inner = text[brace + 1 : close]
                self._parse_properties(inner, token)
                tokens.append(token)
                i = close + 1
                continue

            # ── clock { ... } (skip) ─────────────────────────────────────────
            if text[i:].startswith("clock"):
                brace = text.find("{", i)
                if brace != -1:
                    close = self._find_matching_brace(text, brace)
                    i = close + 1 if close != -1 else n
                    continue

            # ── class blocks (skip) ──────────────────────────────────────────
            if text[i:].startswith("class"):
                brace = text.find("{", i)
                if brace != -1:
                    close = self._find_matching_brace(text, brace)
                    i = close + 1 if close != -1 else n
                    continue

            # skip unknown tokens until next line
            eol = text.find("\n", i)
            i = eol + 1 if eol != -1 else n

        return tokens

    def _find_matching_brace(self, text: str, start: int) -> int:
        """Find the closing brace matching the opening brace at *start*."""
        depth = 0
        i = start
        n = len(text)
        while i < n:
            ch = text[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        return -1

    def _parse_properties(self, inner: str, token: GLMToken):
        """Parse key-value pairs and nested objects from a GLM block body."""
        # First, extract nested object blocks
        i = 0
        n = len(inner)
        while i < n:
            # skip whitespace
            while i < n and inner[i] in " \t\r\n":
                i += 1
            if i >= n:
                break

            if inner[i:].startswith("object"):
                j = i + 6
                while j < n and inner[j] in " \t":
                    j += 1
                k = j
                while k < n and inner[k] not in " \t\n{":
                    k += 1
                obj_type = inner[j:k]
                brace = inner.find("{", k)
                if brace != -1:
                    close = self._find_matching_brace(inner, brace)
                    if close != -1:
                        child = GLMToken(obj_type)
                        child_inner = inner[brace + 1 : close]
                        self._parse_properties(child_inner, child)
                        token.children.append(child)
                        i = close + 1
                        continue
                i = k
                continue

            # Property line — find semicolon
            semi = inner.find(";", i)
            if semi == -1:
                break
            line = inner[i:semi].strip()
            i = semi + 1

            if not line:
                continue

            # Parse key value
            parts = line.split(None, 1)
            if len(parts) == 2:
                key, val = parts[0], parts[1].strip()
                val = self._expand(val)
                if key == "name":
                    token.name = val
                elif key == "parent":
                    token.parent = val
                else:
                    token.properties[key] = val


# ── Converter ───────────────────────────────────────────────────────────────


# Default pandapower line types for when GLM conductor data is sparse
_DEFAULT_LINE_STD_TYPE = "NAYY 4x50 SE"
_DEFAULT_UG_LINE_STD_TYPE = "NAYY 4x50 SE"

# Mapping from GLM bustype to pandapower bus type
_BUS_TYPE_MAP = {
    "SWING": "b",  # slack bus
    "PV": "b",     # PV bus (generator)
    "PQ": "b",     # PQ bus (load)
}


def _parse_complex(s: str) -> complex:
    """Parse a GLM complex value like '7200.00' or '-3600.00-6235.38j'."""
    s = s.strip()
    if not s:
        return 0j
    # Handle cases like "+0j" or just a number
    s = s.replace(" ", "")
    # Replace 'j' with 'j' (already correct for Python)
    try:
        return complex(s.replace("i", "j")) if "i" in s else complex(s)
    except ValueError:
        # Try adding 'j' at end if it looks like an imaginary-only value
        try:
            return complex(s + "j")
        except ValueError:
            return 0j


def _parse_float(s: str, default: float = 0.0) -> float:
    """Parse a GLM float value, stripping units."""
    s = s.strip()
    # Remove common unit suffixes
    for suffix in ("MVA", "kVA", "VA", "kV", "V", "A", "ohm", "m", "ft", "in"):
        s = s.replace(suffix, "")
    s = s.strip()
    try:
        return float(s)
    except ValueError:
        return default


class GLMPandapowerConverter:
    """
    Converts GridLAB-D .glm files into pandapower Networks.

    The converter handles the most common GLM object types for power flow:

    +-----------------------------------+---------------------------+
    | GLM Object                        | Pandapower Element        |
    +===================================+===========================+
    | ``node`` / ``substation``         | ``bus``                   |
    | ``load``                          | ``load``                  |
    | ``overhead_line`` / ``underground`` | ``line``              |
    | ``transformer`` + config          | ``trafo``                 |
    | ``regulator`` + config            | ``trafo`` (with tap)      |
    | ``switch``                        | ``switch``                |
    | ``meter``                         | ``bus`` (junction node)   |
    +-----------------------------------+---------------------------+

    Usage::

        converter = GLMPandapowerConverter()
        net = converter.convert("path/to/feeder.glm")
        pp.runpp(net)
    """

    def __init__(self):
        self._nodes: Dict[str, int] = {}      # GLM name → pandapower bus idx
        self._configs: Dict[str, dict] = {}    # config name → parsed params
        self._conductors: Dict[str, dict] = {} # conductor name → params
        self._spacings: Dict[str, dict] = {}   # spacing name → params

    def parse_glm(self, glm_path: str | Path) -> List[GLMToken]:
        """Parse a GLM file into structured tokens.

        Args:
            glm_path: Path to the .glm file.

        Returns:
            List of GLMToken objects representing the parsed GLM objects.
        """
        parser = GLMParser()
        tokens = parser.parse(Path(glm_path))
        logger.info(f"Parsed {len(tokens)} GLM objects from {glm_path}")
        return tokens

    def to_pandapower(self, tokens: List[GLMToken], name: str = "GLM_Network") -> pp.pandapowerNet:
        """Convert parsed GLM tokens into a pandapower Network.

        Args:
            tokens: List of GLMToken objects from :meth:`parse_glm`.
            name: Name for the resulting pandapower network.

        Returns:
            A pandapower Network ready for power flow analysis.
        """
        net = pp.create_empty_network(name=name)
        net.bus_geodata = pd.DataFrame(columns=["x", "y"])
        net.line_geodata = pd.DataFrame(columns=["coords"])

        # Reset internal state
        self._nodes = {}
        self._configs = {}
        self._conductors = {}
        self._spacings = {}

        # Pass 1: Collect configurations (must be processed before objects that reference them)
        self._collect_configurations(tokens)

        # Pass 1b: Collect all referenced names from lines/transformers/switches
        # In GLM, lines connect named objects (nodes, loads, meters — anything with a name).
        # We need to know ALL names that serve as topological connection points.
        endpoint_names = self._collect_endpoint_names(tokens)

        # Pass 2: Create buses from all objects that serve as network nodes
        self._create_buses(net, tokens, endpoint_names)

        # Pass 3: Create lines from overhead_line/underground_line objects
        self._create_lines(net, tokens)

        # Pass 4: Create transformers from transformer objects
        self._create_transformers(net, tokens)

        # Pass 5: Create regulators as transformers
        self._create_regulators(net, tokens)

        # Pass 6: Create switches
        self._create_switches(net, tokens)

        # Pass 6b: Connect parented objects (meters with parent reference)
        self._connect_parented_objects(net, tokens)

        # Pass 7: Create loads from load objects
        self._create_loads(net, tokens)

        # Ensure at least one external grid (slack) bus exists
        self._ensure_ext_grid(net)

        logger.info(
            f"Converted GLM → pandapower: {len(net.bus)} buses, "
            f"{len(net.line)} lines, {len(net.trafo)} trafos, "
            f"{len(net.load)} loads, {len(net.switch)} switches"
        )
        return net

    def convert(self, glm_path: str | Path, name: str = "GLM_Network") -> pp.pandapowerNet:
        """Parse a GLM file and convert it to a pandapower Network.

        Convenience method combining :meth:`parse_glm` and :meth:`to_pandapower`.

        Args:
            glm_path: Path to the .glm file.
            name: Name for the resulting pandapower network.

        Returns:
            A pandapower Network ready for power flow analysis.
        """
        tokens = self.parse_glm(glm_path)
        return self.to_pandapower(tokens, name=name)

    # ── Pass 1: Configuration collection ────────────────────────────────────

    def _collect_configurations(self, tokens: List[GLMToken]):
        """Collect transformer_configuration, line_configuration, conductor, and spacing objects."""
        for t in tokens:
            if t.obj_type == "transformer_configuration":
                self._configs[t.name] = {
                    "connect_type": t.properties.get("connect_type", "WYE_WYE"),
                    "power_rating": _parse_float(t.properties.get("power_rating", "0"), 0),
                    "primary_voltage": _parse_float(t.properties.get("primary_voltage", "0"), 0),
                    "secondary_voltage": _parse_float(t.properties.get("secondary_voltage", "0"), 0),
                    "resistance": _parse_float(t.properties.get("resistance", "0"), 0),
                    "reactance": _parse_float(t.properties.get("reactance", "0"), 0),
                    "install_type": t.properties.get("install_type", ""),
                }
            elif t.obj_type == "regulator_configuration":
                self._configs[t.name] = {
                    "connect_type": t.properties.get("connect_type", "1"),
                    "band_center": _parse_float(t.properties.get("band_center", "120"), 120),
                    "band_width": _parse_float(t.properties.get("band_width", "2"), 2),
                    "raise_taps": int(_parse_float(t.properties.get("raise_taps", "16"), 16)),
                    "lower_taps": int(_parse_float(t.properties.get("lower_taps", "16"), 16)),
                    "regulation": _parse_float(t.properties.get("regulation", "0.1"), 0.1),
                    "tap_pos_A": int(_parse_float(t.properties.get("tap_pos_A", "0"), 0)),
                    "tap_pos_B": int(_parse_float(t.properties.get("tap_pos_B", "0"), 0)),
                    "tap_pos_C": int(_parse_float(t.properties.get("tap_pos_C", "0"), 0)),
                }
            elif t.obj_type in ("overhead_line_conductor", "underground_line_conductor"):
                self._conductors[t.name] = {
                    "resistance": _parse_float(t.properties.get("resistance", "0"), 0),
                    "geometric_mean_radius": _parse_float(
                        t.properties.get("geometric_mean_radius",
                                        t.properties.get("conductor_gmr", "0")), 0
                    ),
                    "diameter": _parse_float(
                        t.properties.get("diameter", "0"), 0
                    ),
                }
            elif t.obj_type == "line_spacing":
                spacing = {}
                for prop, val in t.properties.items():
                    spacing[prop] = _parse_float(val, 0)
                self._spacings[t.name] = spacing
            elif t.obj_type == "line_configuration":
                self._configs[t.name] = {
                    "conductor_A": t.properties.get("conductor_A", ""),
                    "conductor_B": t.properties.get("conductor_B", ""),
                    "conductor_C": t.properties.get("conductor_C", ""),
                    "conductor_N": t.properties.get("conductor_N", ""),
                    "spacing": t.properties.get("spacing", ""),
                }

        logger.debug(
            f"Collected {len(self._configs)} configs, "
            f"{len(self._conductors)} conductors, "
            f"{len(self._spacings)} spacings"
        )

    # ── Pass 1b: Collect endpoint names ─────────────────────────────────────

    def _collect_endpoint_names(self, tokens: List[GLMToken]) -> set:
        """Collect all GLM object names that appear as line/transformer/switch endpoints.

        In GridLAB-D, lines connect named objects — these can be node, load, meter,
        or any named object. We collect all such endpoint names so we can ensure they
        all become pandapower buses.
        """
        endpoints = set()
        for t in tokens:
            if t.obj_type in ("overhead_line", "underground_line", "transformer", "regulator", "switch"):
                for key in ("from", "to"):
                    name = t.properties.get(key, "")
                    if name:
                        endpoints.add(name)
        return endpoints

    # ── Pass 2: Bus creation ────────────────────────────────────────────────

    def _create_buses(self, net: pp.pandapowerNet, tokens: List[GLMToken],
                      endpoint_names: set):
        """Create pandapower buses from all GLM objects that are network nodes.

        This includes:
        - Explicit node/substation objects (always buses)
        - Meter objects (junction nodes in GLM topology)
        - Load objects whose names appear as line/transformer endpoints
        - Any named object referenced in a from/to connection
        """
        # Build a name → token lookup for resolving voltages
        token_by_name: Dict[str, GLMToken] = {}
        for t in tokens:
            if t.name:
                token_by_name[t.name] = t

        # Create buses for all node/substation/meter objects first
        for t in tokens:
            if t.obj_type in ("node", "substation", "meter"):
                name = t.name or f"{t.obj_type}_{len(self._nodes)}"
                nom_v = _parse_float(t.properties.get("nominal_voltage", "2400"), 2400)
                # GLM nominal_voltage is typically L-N voltage in volts.
                # Convert to pandapower L-L voltage in kV.
                if nom_v > 500:
                    if 2000 < nom_v < 3000:
                        vn_kv = nom_v * 1.732 / 1000.0  # ~2.4kV L-N → 4.16kV L-L
                    elif nom_v > 10000:
                        vn_kv = nom_v / 1000.0  # Already HV L-L
                    else:
                        vn_kv = nom_v * 1.732 / 1000.0  # Treat as L-N
                elif nom_v > 100:
                    vn_kv = nom_v / 1000.0
                else:
                    vn_kv = nom_v

                if name in self._nodes:
                    continue

                idx = pp.create_bus(net, vn_kv=vn_kv, name=name)
                self._nodes[name] = idx

                bustype = t.properties.get("bustype", "")
                if t.obj_type == "substation" or bustype == "SWING":
                    net.bus.at[idx, "marker"] = "swing"

        # Create buses for endpoint names that aren't yet buses
        # These are typically load objects used as junction nodes
        for name in endpoint_names:
            if name in self._nodes:
                continue

            # Determine voltage: look up the token if it exists
            t = token_by_name.get(name)
            if t:
                nom_v = _parse_float(t.properties.get("nominal_voltage", "2400"), 2400)
                # GLM nominal_voltage is often L-N. Convert to L-L if needed.
                # Heuristic: values > 500 are likely in volts; < 100 are likely in kV
                if nom_v > 500:
                    vn_kv = nom_v / 1000.0
                    # Check if this looks like L-N (if ~2400V in a 4.16kV system)
                    # L-L = L-N * sqrt(3) for 3-phase
                    if 2000 < nom_v < 3000:
                        vn_kv = nom_v * 1.732 / 1000.0  # L-N to L-L, then to kV
                elif nom_v > 100:
                    vn_kv = nom_v / 1000.0
                else:
                    vn_kv = nom_v
            else:
                # Infer voltage from already-created connected buses
                # Find any existing bus connected via a line to this name
                vn_kv = None
                for t2 in tokens:
                    if t2.obj_type in ("overhead_line", "underground_line", "transformer", "regulator"):
                        for key in ("from", "to"):
                            if t2.properties.get(key) == name:
                                other_key = "to" if key == "from" else "from"
                                other_name = t2.properties.get(other_key, "")
                                other_idx = self._nodes.get(other_name)
                                if other_idx is not None:
                                    vn_kv = net.bus.at[other_idx, "vn_kv"]
                                    break
                    if vn_kv is not None:
                        break

                if vn_kv is None:
                    vn_kv = 4.16  # Default distribution voltage

            idx = pp.create_bus(net, vn_kv=vn_kv, name=name)
            self._nodes[name] = idx

        logger.debug(f"Created {len(self._nodes)} buses")

    def _get_bus_idx(self, name: str) -> Optional[int]:
        """Look up a pandapower bus index by GLM object name."""
        return self._nodes.get(name)

    # ── Pass 3: Line creation ───────────────────────────────────────────────

    def _create_lines(self, net: pp.pandapowerNet, tokens: List[GLMToken]):
        """Create pandapower lines from GLM overhead_line and underground_line objects."""
        for t in tokens:
            if t.obj_type not in ("overhead_line", "underground_line"):
                continue

            from_name = t.properties.get("from", "")
            to_name = t.properties.get("to", "")
            if not from_name or not to_name:
                continue

            from_bus = self._get_bus_idx(from_name)
            to_bus = self._get_bus_idx(to_name)
            if from_bus is None or to_bus is None:
                # Try creating missing buses as junction nodes
                from_bus = self._ensure_bus(net, from_name, vn_kv=4.16)
                to_bus = self._ensure_bus(net, to_name, vn_kv=4.16)

            name = t.name or f"line_{from_name}_{to_name}"
            length_m = _parse_float(t.properties.get("length", "100"), 100)
            length_km = length_m / 1000.0 if length_m > 1 else length_m  # GLM uses feet sometimes

            # Try to compute impedance from line_configuration → conductor → spacing
            r_ohm_per_km, x_ohm_per_km, c_nf_per_km = self._compute_line_impedance(
                t.properties.get("configuration", ""), length_m
            )

            # If we couldn't compute impedance, use a default std_type
            config_name = t.properties.get("configuration", "")
            if config_name in self._configs or r_ohm_per_km > 0:
                max_i_ka = 0.4  # Default 400A thermal limit
                # Ensure minimum values for convergence to prevent singular matrix
                r_ohm_per_km = max(r_ohm_per_km, 0.001)
                x_ohm_per_km = max(x_ohm_per_km, 0.001)
                
                pp.create_line_from_parameters(
                    net,
                    from_bus=from_bus,
                    to_bus=to_bus,
                    length_km=length_km,
                    r_ohm_per_km=r_ohm_per_km,
                    x_ohm_per_km=x_ohm_per_km,
                    c_nf_per_km=c_nf_per_km,
                    max_i_ka=max_i_ka,
                    name=name,
                )
            else:
                pp.create_line(
                    net,
                    from_bus=from_bus,
                    to_bus=to_bus,
                    length_km=length_km,
                    std_type=_DEFAULT_LINE_STD_TYPE,
                    name=name,
                )

    def _compute_line_impedance(
        self, config_name: str, length_m: float
    ) -> Tuple[float, float, float]:
        """Compute R, X, C per km from GLM line_configuration + conductor + spacing."""
        if config_name not in self._configs:
            # No configuration — use a reasonable default for distribution feeders
            return 0.6, 0.4, 0.0

        config = self._configs[config_name]
        conductor_name = config.get("conductor_A", "") or config.get("conductor_B", "") or config.get("conductor_C", "")
        if not conductor_name or conductor_name not in self._conductors:
            # Configuration found but no conductor data — use defaults
            return 0.6, 0.4, 0.0

        cond = self._conductors[conductor_name]
        resistance = cond.get("resistance", 0)
        gmr = cond.get("geometric_mean_radius", 0.001)

        # Resistance per km (GLM resistance is per mile or per 1000ft depending on context)
        # Assume per-mile if value > 0.01, per km otherwise
        if resistance > 0:
            r_ohm_per_km = resistance / 1.60934 if resistance < 10 else resistance
        else:
            r_ohm_per_km = 0.0

        # Reactance from GMR and spacing (simplified Carson's equation)
        # X = 2πf × 10⁻⁷ × ln(D_eq / GMR) Ω/m
        # Using default equivalent spacing of 1m if no spacing data
        spacing_name = config.get("spacing", "")
        d_eq = 1.0  # Default 1m equivalent spacing
        if spacing_name in self._spacings:
            sp = self._spacings[spacing_name]
            # Calculate geometric mean distance from available distances
            distances = [v for k, v in sp.items() if k.startswith("distance_") and v > 0]
            if len(distances) >= 2:
                d_eq = np.prod(distances) ** (1.0 / len(distances))
            elif distances:
                d_eq = distances[0]
            # Convert from feet to meters if values > 0.5 (heuristic)
            if d_eq > 0.5:
                d_eq *= 0.3048

        f = 60.0  # Default 60 Hz (US); Thai grid uses 50 Hz
        x_ohm_per_km = 2 * np.pi * f * 1e-7 * 1000 * np.log(d_eq / max(gmr, 1e-6)) if gmr > 0 else 0.0
        c_nf_per_km = 0.0  # Capacitance negligible for distribution feeders

        return r_ohm_per_km, x_ohm_per_km, c_nf_per_km

    # ── Pass 4: Transformer creation ────────────────────────────────────────

    def _create_transformers(self, net: pp.pandapowerNet, tokens: List[GLMToken]):
        """Create pandapower transformers from GLM transformer objects."""
        for t in tokens:
            if t.obj_type != "transformer":
                continue

            from_name = t.properties.get("from", "")
            to_name = t.properties.get("to", "")
            config_name = t.properties.get("configuration", "")

            from_bus = self._get_bus_idx(from_name)
            to_bus = self._get_bus_idx(to_name)
            if from_bus is None or to_bus is None:
                continue

            config = self._configs.get(config_name, {})
            if not config:
                continue

            sn_mva = config.get("power_rating", 500) / 1000.0  # kVA → MVA
            hv_kv = config.get("primary_voltage", 4160) / 1000.0  # V → kV
            lv_kv = config.get("secondary_voltage", 480) / 1000.0  # V → kV
            vk_percent = config.get("reactance", 0.02) * 100  # per-unit → %
            vkr_percent = config.get("resistance", 0.011) * 100  # per-unit → %
            # Ensure minimum values for convergence
            sn_mva = max(sn_mva, 0.01)
            vkr_percent = max(vkr_percent, 0.01)
            vk_percent = max(vk_percent, vkr_percent + 0.1)

            name = t.name or f"trafo_{from_name}_{to_name}"
            pp.create_transformer_from_parameters(
                net,
                hv_bus=from_bus,
                lv_bus=to_bus,
                sn_mva=sn_mva,
                vn_hv_kv=max(hv_kv, 0.1),
                vn_lv_kv=max(lv_kv, 0.1),
                vk_percent=vk_percent,
                vkr_percent=vkr_percent,
                pfe_kw=0,
                i0_percent=0,
                name=name,
            )

    # ── Pass 5: Regulator creation ──────────────────────────────────────────

    def _create_regulators(self, net: pp.pandapowerNet, tokens: List[GLMToken]):
        """Create pandapower transformers (with tap settings) from GLM regulator objects."""
        for t in tokens:
            if t.obj_type != "regulator":
                continue

            from_name = t.properties.get("from", "")
            to_name = t.properties.get("to", "")
            config_name = t.properties.get("configuration", "")

            from_bus = self._get_bus_idx(from_name)
            to_bus = self._get_bus_idx(to_name)
            if from_bus is None or to_bus is None:
                continue

            config = self._configs.get(config_name, {})
            if not config:
                continue

            # Regulators are essentially tap-changing transformers
            regulation = config.get("regulation", 0.1)
            taps = config.get("raise_taps", 16)

            # Get voltage levels from the connected buses
            hv_kv = net.bus.at[from_bus, "vn_kv"]
            lv_kv = net.bus.at[to_bus, "vn_kv"]
            # Regulators often connect buses at the same voltage level
            if abs(hv_kv - lv_kv) < 0.01:
                lv_kv = hv_kv * (1 - regulation)

            sn_mva = 10.0  # Default for regulators
            vk_percent = max(regulation * 100, 0.5)
            vkr_percent = 0.5

            name = t.name or f"reg_{from_name}_{to_name}"
            tap_pos = config.get("tap_pos_A", 0)
            tap_neutral = taps
            tap_max = tap_neutral + taps
            tap_min = tap_neutral - config.get("lower_taps", 16)

            pp.create_transformer_from_parameters(
                net,
                hv_bus=from_bus,
                lv_bus=to_bus,
                sn_mva=sn_mva,
                vn_hv_kv=max(hv_kv, 0.1),
                vn_lv_kv=max(lv_kv, 0.1),
                vk_percent=vk_percent,
                vkr_percent=vkr_percent,
                pfe_kw=0,
                i0_percent=0,
                tap_pos=tap_pos,
                tap_neutral=tap_neutral,
                tap_max=tap_max,
                tap_min=tap_min,
                tap_step_percent=regulation * 100 / taps if taps > 0 else 1.0,
                name=name,
            )

    # ── Pass 6: Switch creation ─────────────────────────────────────────────

    def _create_switches(self, net: pp.pandapowerNet, tokens: List[GLMToken]):
        """Create pandapower switches from GLM switch objects."""
        for t in tokens:
            if t.obj_type != "switch":
                continue

            from_name = t.properties.get("from", "")
            to_name = t.properties.get("to", "")
            status = t.properties.get("status", "CLOSED")

            from_bus = self._get_bus_idx(from_name)
            to_bus = self._get_bus_idx(to_name)
            if from_bus is None or to_bus is None:
                continue

            closed = status.upper() in ("CLOSED", "1", "TRUE")
            name = t.name or f"sw_{from_name}_{to_name}"
            pp.create_switch(net, bus=from_bus, element=to_bus, et="b",
                             closed=closed, name=name)

    # ── Pass 6b: Parented object connectivity ────────────────────────────────

    def _connect_parented_objects(self, net: pp.pandapowerNet, tokens: List[GLMToken]):
        """Connect GLM objects that have a ``parent`` reference to their parent bus.

        In GLM, a meter or load with ``parent l675`` is connected to the same
        electrical node as l675. We model this as a closed bus-bus switch (zero
        impedance connection).
        """
        for t in tokens:
            if not t.parent:
                continue
            parent_bus = self._get_bus_idx(t.parent)
            own_bus = self._get_bus_idx(t.name)
            if parent_bus is None or own_bus is None:
                continue
            if parent_bus == own_bus:
                continue
            # Only create switch if these buses are at the same voltage level
            parent_vn = net.bus.at[parent_bus, "vn_kv"]
            own_vn = net.bus.at[own_bus, "vn_kv"]
            if abs(parent_vn - own_vn) < 0.01:
                name = f"parent_{t.name}_to_{t.parent}"
                pp.create_switch(net, bus=own_bus, element=parent_bus, et="b",
                                 closed=True, name=name)

    # ── Pass 7: Load creation ───────────────────────────────────────────────

    def _create_loads(self, net: pp.pandapowerNet, tokens: List[GLMToken]):
        """Create pandapower loads from GLM load objects.

        In GLM, loads can be:
        1. Standalone topology nodes (e.g., l645 with lines connecting to it)
        2. Child objects with a ``parent`` reference to another node

        For case 1, the load's power is injected at the bus that was already
        created from the endpoint name. For case 2, the load is attached to
        its parent bus.
        """
        for t in tokens:
            if t.obj_type != "load":
                continue

            # Determine which bus this load belongs to
            bus_idx = None
            if t.parent:
                # Load has an explicit parent — attach to parent bus
                bus_idx = self._get_bus_idx(t.parent)
            if bus_idx is None:
                # Load might be its own topology node (e.g., l645)
                bus_idx = self._get_bus_idx(t.name)

            if bus_idx is None:
                continue

            # Sum all constant_power phases for total P and Q
            p_w = 0.0
            q_w = 0.0
            for phase in ("A", "B", "C"):
                cp = t.properties.get(f"constant_power_{phase}", "")
                if cp:
                    z = _parse_complex(cp)
                    p_w += z.real
                    q_w += z.imag

                ci = t.properties.get(f"constant_impedance_{phase}", "")
                if ci:
                    z = _parse_complex(ci)
                    # Approximate impedance load at nominal voltage
                    nom_v = _parse_float(t.properties.get("nominal_voltage", "2400"), 2400)
                    v_sq = nom_v ** 2
                    if abs(z) > 0:
                        p_w += v_sq * z.real / (abs(z) ** 2)
                        q_w += v_sq * z.imag / (abs(z) ** 2)

                cc = t.properties.get(f"constant_current_{phase}", "")
                if cc:
                    z = _parse_complex(cc)
                    # Approximate current load at nominal voltage
                    nom_v = _parse_float(t.properties.get("nominal_voltage", "2400"), 2400)
                    p_w += z.real * nom_v
                    q_w += z.imag * nom_v

            p_mw = p_w / 1e6
            q_mvar = q_w / 1e6

            if abs(p_mw) > 1e-12 or abs(q_mvar) > 1e-12:
                name = t.name or f"load_{bus_idx}"
                pp.create_load(
                    net,
                    bus=bus_idx,
                    p_mw=p_mw,
                    q_mvar=q_mvar,
                    name=name,
                )

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _ensure_bus(self, net: pp.pandapowerNet, name: str, vn_kv: float = 4.16) -> int:
        """Get or create a bus for the given GLM object name."""
        if name in self._nodes:
            return self._nodes[name]
        idx = pp.create_bus(net, vn_kv=vn_kv, name=name)
        self._nodes[name] = idx
        return idx

    def _ensure_ext_grid(self, net: pp.pandapowerNet):
        """Ensure at least one external grid (slack) exists."""
        if len(net.ext_grid) > 0:
            return

        # Find the SWING/substation bus
        swing_bus = None
        for idx in net.bus.index:
            marker = net.bus.at[idx, "marker"] if "marker" in net.bus.columns else ""
            if marker == "swing":
                swing_bus = idx
                break

        if swing_bus is None:
            # Use the first bus
            swing_bus = net.bus.index[0] if len(net.bus) > 0 else None

        if swing_bus is not None:
            pp.create_ext_grid(net, bus=swing_bus, vm_pu=1.0, name="GLM_Slack")
            logger.info(f"Created external grid at bus {swing_bus} ({net.bus.at[swing_bus, 'name']})")
        else:
            logger.warning("No buses found — cannot create external grid")

        # Clean up marker column
        if "marker" in net.bus.columns:
            net.bus.drop(columns=["marker"], inplace=True)
