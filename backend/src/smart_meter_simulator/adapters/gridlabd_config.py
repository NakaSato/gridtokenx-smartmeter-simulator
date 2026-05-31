"""
GridLAB-D Configuration Generator for Co-Simulation.

Generates GLM configuration snippets and HELICS message configuration files
for running GridLAB-D as a federate in a co-simulation environment.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class GridlabdConfig:
    """Generates GridLAB-D configuration files for co-simulation.

    Produces:
    - HELICS message configuration JSON (publications/subscriptions)
    - Modified GLM file snippets for federate integration
    """

    def __init__(self, federate_name: str = "gridlabdSimulator"):
        self.federate_name = federate_name

    def generate_helics_config(
        self,
        publications: Dict[str, str],
        subscriptions: Dict[str, str],
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a HELICS message configuration file for GridLAB-D.

        Args:
            publications: Dict mapping GLM property path → HELICS key.
                E.g., {"n650.distribution_load": "distribution_load"}
            subscriptions: Dict mapping HELICS key → GLM object property.
                E.g., {"loadshed/sw_status": "sw_loadshed.phase_A_state"}
            output_path: If provided, write the JSON config to this file.

        Returns:
            The HELICS config as a dictionary.
        """
        config = {
            "name": self.federate_name,
            "core_type": "zmq",
            "period": 900,
            "publications": [],
            "subscriptions": [],
        }

        for glm_prop, helics_key in publications.items():
            config["publications"].append({
                "key": helics_key,
                "type": "double",
                "global": True,
                "info": f"GLM:{glm_prop}",
            })

        for helics_key, glm_prop in subscriptions.items():
            config["subscriptions"].append({
                "key": helics_key,
                "type": "double",
                "global": True,
                "info": f"GLM:{glm_prop}",
            })

        if output_path:
            Path(output_path).write_text(json.dumps(config, indent=2))
            logger.info(f"Wrote HELICS GridLAB-D config to {output_path}")

        return config

    def generate_glm_wrapper(
        self,
        base_glm_path: str,
        helics_config_path: str,
        output_path: Optional[str] = None,
    ) -> str:
        """Generate a GLM wrapper that adds HELICS message object to a base GLM.

        Args:
            base_glm_path: Path to the original GLM file.
            helics_config_path: Path to the HELICS JSON config.
            output_path: If provided, write the wrapper GLM to this file.

        Returns:
            The wrapper GLM content as a string.
        """
        content = f"""// GridLAB-D wrapper for GridTokenX co-simulation
// Auto-generated — do not edit manually

#include "{base_glm_path}"

object helics_msg {{
  name {self.federate_name};
  configure {helics_config_path};
}}
"""
        if output_path:
            Path(output_path).write_text(content)
            logger.info(f"Wrote GLM wrapper to {output_path}")

        return content
