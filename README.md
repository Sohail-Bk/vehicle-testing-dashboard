# Vehicle Testing Dashboard

A simple Dash-Plotly based automotive vehicle testing reporting solution for time-series EV data.

## Features
- Vehicle selector and date-range filtering
- KPI cards for critical test metrics
- Time-series charts for speed, RPM, voltage, SOC, temperatures, throttle, and regen braking
- Summary table with Min / Average / Max values
- Synthetic sample data generator for realistic EV testing scenarios

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

## Project structure

```text
vehicle-testing-dashboard/
├── app.py
├── generate_sample_data.py
├── requirements.txt
├── README.md
├── .gitignore
└── data/
    └── sample_vehicle_data.csv
```
