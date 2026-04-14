"""
Simulation constants and magic numbers
Centralized configuration for simulation parameters
"""

# Time constants
SIMULATION_INTERVAL_SECONDS = 900  # 15 minutes (default interval)
REAL_TIME_TICK_SECONDS = 5  # Real seconds between ticks
REQUEST_TIMEOUT_SECONDS = 10  # HTTP request timeout

# Frequency constants
FREQUENCY_NOMINAL_HZ = 50.0  # Nominal grid frequency
FREQUENCY_DEADBAND_PU = 0.001  # Frequency deadband (0.1%)
FREQUENCY_DEVIATION_THRESHOLD = 0.02  # 2% deviation threshold for AFRR
FREQUENCY_CRITICAL_LOW = 47.0  # Critical low frequency (black start trigger)

# Droop control constants
DROOP_GAIN = 20.0  # Frequency-Watt droop gain (1/0.05)
DROOP_SETTING = 0.05  # 5% droop setting

# Accuracy and measurement
ACCURACY_SIGMA_FACTOR = 3  # 3σ bound for 99.7% confidence
MIN_STD_DEV_FLOOR = 0.001  # Minimum std dev floor for power measurements
VOLTAGE_STD_DEV_FLOOR = 0.005  # Minimum std dev floor for voltage (0.5% pu)

# Bad data detection
BAD_DATA_NORM_RESIDUAL_THRESHOLD = 3.0  # Normalized residual threshold
BAD_DATA_COMPROMISED_THRESHOLD = 4.0  # Threshold for marking meter as compromised
EWMA_COMPROMISED_THRESHOLD = 2.0  # EWMA residual threshold

# Power system
DEFAULT_POWER_FACTOR = 0.3  # Default reactive power ratio (Q = P * 0.3)
DEFAULT_VOLTAGE_PU = 1.0  # Nominal voltage per unit
SLACK_BUS_VOLTAGE_PU = 1.0  # Slack bus voltage magnitude

# Retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BACKOFF_SECONDS = 1.0

# Market and pricing
DEFAULT_ELECTRICITY_PRICE = 0.25  # Default electricity price ($/kWh)
DEFAULT_AUCTION_BATCH_ID = "8S2e2p4ghqMJuzTz5AkAKSka7jqsjgBH7eWDcCHzXPND"

# Weather
DEFAULT_WEATHER_CONDITION = "Sunny"

# Grid analytics
VOLTAGE_UPPER_LIMIT_PU = 1.05  # Overvoltage threshold
VOLTAGE_LOWER_LIMIT_PU = 0.95  # Undervoltage threshold
LINE_LOADING_CRITICAL_PERCENT = 90.0  # Critical line loading threshold

# Battery
DEFAULT_BATTERY_EFFICIENCY = 0.90  # Default round-trip efficiency

# Solar
DEFAULT_SOLAR_EFFICIENCY = 0.85  # Default solar panel efficiency

# VPP
VPP_FLEXIBILITY_FACTOR = 0.2  # 20% of flexibility dispatched during ADR

# Security
FDI_ATTACK_DETECTION_ENABLED = True  # Enable FDI attack detection
