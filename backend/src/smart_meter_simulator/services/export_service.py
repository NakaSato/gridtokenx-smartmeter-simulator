"""
Grid Export Service (Simplified)
"""

import logging

logger = logging.getLogger(__name__)


class GridExportService:
    """
    Service for exporting grid data.
    """

    @staticmethod
    def generate_cim_rdf(engine) -> str:
        """CIM RDF generation disabled."""
        return '<?xml version="1.0" encoding="UTF-8"?><rdf:RDF xmlns:cim="http://iec.ch/TC57/CIM100#" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"></rdf:RDF>'
