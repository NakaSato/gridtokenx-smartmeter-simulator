"""Parser for the GLM subset used by the simulator topology loader."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional


class GLMToken:
    """A parsed GLM object with type, name, properties, and children."""

    __slots__ = ("obj_type", "name", "properties", "children", "parent")

    def __init__(self, obj_type: str, name: str = "") -> None:
        self.obj_type = obj_type
        self.name = name
        self.properties: Dict[str, Any] = {}
        self.children: List["GLMToken"] = []
        self.parent: Optional[str] = None

    def __repr__(self) -> str:
        return f"GLMToken({self.obj_type}, name={self.name!r})"


class GLMParser:
    """Minimal GridLAB-D GLM object parser."""

    def __init__(self) -> None:
        self._defines: Dict[str, str] = {}

    def parse(self, glm_path: str | Path) -> List[GLMToken]:
        text = Path(glm_path).read_text(encoding="utf-8", errors="replace")
        text = re.sub(r"//[^\n]*", "", text)
        return self._parse_block_iter(text)

    def _expand(self, value: str) -> str:
        def replace(match: re.Match[str]) -> str:
            key = match.group(1)
            return self._defines.get(key, match.group(0))

        return re.sub(r"\$\{(\w+)\}", replace, value)

    def _parse_block_iter(self, text: str) -> List[GLMToken]:
        tokens: List[GLMToken] = []
        i = 0
        n = len(text)

        while i < n:
            while i < n and text[i] in " \t\r\n":
                i += 1
            if i >= n:
                break

            if text[i] == "#":
                eol = text.find("\n", i)
                if eol == -1:
                    eol = n
                directive = text[i:eol].strip()
                if directive.startswith("#define"):
                    match = re.match(r"#define\s+(\w+)\s*=\s*(.+)", directive)
                    if match:
                        self._defines[match.group(1)] = match.group(2).strip()
                i = eol + 1
                continue

            if text[i:].startswith("module"):
                i = self._skip_named_or_braced_block(text, i + 6)
                continue

            if text[i:].startswith("clock") or text[i:].startswith("class"):
                brace = text.find("{", i)
                if brace != -1:
                    close = self._find_matching_brace(text, brace)
                    i = close + 1 if close != -1 else n
                    continue

            if text[i:].startswith("object"):
                token, next_index = self._parse_object(text, i)
                if token is not None:
                    tokens.append(token)
                i = next_index
                continue

            eol = text.find("\n", i)
            i = eol + 1 if eol != -1 else n

        return tokens

    def _skip_named_or_braced_block(self, text: str, start: int) -> int:
        n = len(text)
        semi = text.find(";", start)
        brace = text.find("{", start)
        if semi != -1 and (brace == -1 or semi < brace):
            return semi + 1
        if brace != -1:
            close = self._find_matching_brace(text, brace)
            return close + 1 if close != -1 else n
        return n

    def _parse_object(self, text: str, start: int) -> tuple[Optional[GLMToken], int]:
        n = len(text)
        j = start + 6
        while j < n and text[j] in " \t":
            j += 1
        k = j
        while k < n and text[k] not in " \t\n{":
            k += 1
        obj_type = text[j:k]
        brace = text.find("{", k)
        if brace == -1:
            return None, k
        close = self._find_matching_brace(text, brace)
        if close == -1:
            return None, brace + 1

        token = GLMToken(obj_type)
        self._parse_properties(text[brace + 1 : close], token)
        return token, close + 1

    def _find_matching_brace(self, text: str, start: int) -> int:
        depth = 0
        for idx in range(start, len(text)):
            if text[idx] == "{":
                depth += 1
            elif text[idx] == "}":
                depth -= 1
                if depth == 0:
                    return idx
        return -1

    def _parse_properties(self, inner: str, token: GLMToken) -> None:
        i = 0
        n = len(inner)
        while i < n:
            while i < n and inner[i] in " \t\r\n":
                i += 1
            if i >= n:
                break

            if inner[i:].startswith("object"):
                child, next_index = self._parse_object(inner, i)
                if child is not None:
                    token.children.append(child)
                i = next_index
                continue

            semi = inner.find(";", i)
            if semi == -1:
                break
            line = inner[i:semi].strip()
            i = semi + 1
            if not line:
                continue

            parts = line.split(None, 1)
            if len(parts) != 2:
                continue
            key, value = parts[0], self._expand(parts[1].strip())
            if key == "name":
                token.name = value
            elif key == "parent":
                token.parent = value
            else:
                token.properties[key] = value
