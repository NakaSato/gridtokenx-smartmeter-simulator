#!/bin/bash
# Set 200 meters with balanced ratios
curl -X PUT http://localhost:8082/api/v1/meters/count \
     -H "Content-Type: application/json" \
     -d '{
       "count": 200,
       "solar_ratio": 0.2,
       "consumer_ratio": 0.5,
       "hybrid_ratio": 0.1,
       "battery_ratio": 0.1,
       "ev_ratio": 0.1
     }'
