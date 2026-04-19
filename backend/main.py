import sys
import os

# Ensure src is in the path for smart_meter_simulator to be importable
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from smart_meter_simulator.app import app
