#!/bin/bash
# Start Smart Meter Simulator
cd /Users/chanthawat/Developments/gridtokenx-platform-infa/gridtokenx-smartmeter-simulator
source .venv/bin/activate
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
python3 -u -m app.main > simulator.log 2>&1 &
echo $! > simulator.pid
echo "Smart Meter Simulator started with PID: $(cat simulator.pid)"
