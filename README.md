# Vehicle Testing Dashboard

A simple Dash-Plotly based automotive vehicle testing reporting solution for time-series EV data.

## Features
- Vehicle selector and date-range filtering
- KPI cards for critical test metrics
- Fault detection cards and fault log for critical/warning conditions
- Time-series charts for speed, RPM, voltage, SOC, temperatures, throttle, and regenerative braking
- Upload support for real CSV files with automatic column mapping
- Summary table with Min / Average / Max values

## Project structure
```text
vehicle-testing-dashboard/
├── data/
│   ├── .gitkeep
│   ├── generate_sample_data.py
│   └── sample_vehicle_data.csv
├── viz/
│   ├── __init__.py
│   └── app.py
├── app.py
├── generate_sample_data.py
├── requirements.txt
└── README.md
```

## Quick start

```bash
pip install -r requirements.txt
python generate_sample_data.py
python app.py
```

Then open:

```text
http://localhost:8050
```

## Fault detection logic
The dashboard flags the following conditions:
- Low SOC (< 20%)
- High battery temperature (> 55°C)
- High motor temperature (> 75°C)
- High inverter temperature (> 80°C)
- Battery voltage under 300V or over 400V
- Battery current above 180A
- High regenerative braking (> 50kW)
- Speed above 120 km/h

## Data columns
- timestamp
- timestamp_unix
- vehicle_id
- vehicle_speed_kmh
- e_motor_speed_rpm
- odometer_km
- ignition_state
- battery_voltage_v
- battery_current_a
- battery_temperature_c
- battery_soc_percent
- motor_temperature_c
- motor_current_a
- inverter_temperature_c
- coolant_temperature_c
- throttle_position_pct
- brake_pressure_bar
- steering_angle_deg
- acceleration_ms2
- gear_position
- cabin_temperature_c
- ambient_temperature_c
- tire_pressure_psi
- gps_latitude
- gps_longitude
- test_cycle
- test_status
- regenerative_braking_kw
