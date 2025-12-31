
import sys
import os

print("--- Python Forensic Probe ---")
print(f"Python Executable: {sys.executable}")
print(f"CWD: {os.getcwd()}")
print("Path:")
for p in sys.path:
    print(f"  {p}")

ledger_file = "/Users/chanthawat/Developments/gridtokenx-platform-infa/gridtokenx-smartmeter-simulator/src/smart_meter_simulator/services/ledger_service.py"
if os.path.exists(ledger_file):
    print(f"\nContent of {ledger_file} (Line 7):")
    with open(ledger_file, 'r') as f:
        lines = f.readlines()
        if len(lines) >= 7:
            print(f"  '{lines[6].strip()}'")
        else:
            print("  [File too short]")
else:
    print(f"\n{ledger_file} NOT FOUND ON DISK")

matching_file = "/Users/chanthawat/Developments/gridtokenx-platform-infa/gridtokenx-smartmeter-simulator/src/smart_meter_simulator/simulation/quantum_matching.py"
print(f"\n{matching_file} exists: {os.path.exists(matching_file)}")

optimizer_file = "/Users/chanthawat/Developments/gridtokenx-platform-infa/gridtokenx-smartmeter-simulator/src/smart_meter_simulator/simulation/quantum_optimizer.py"
print(f"{optimizer_file} exists: {os.path.exists(optimizer_file)}")
