#!/bin/bash
# Start Smart Meter Simulator
cd /Users/chanthawat/Developments/gridtokenx-platform/gridtokenx-smartmeter-simulator
python3 -m smart_meter_simulator.main > simulator.log 2>&1 &
echo $! > simulator.pid
echo "Smart Meter Simulator started with PID: $(cat simulator.pid)"
