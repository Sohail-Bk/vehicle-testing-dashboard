import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


def generate_vehicle_data(vehicle_id='VEH-001', num_points=2000):
    np.random.seed(42)
    start = datetime(2024, 1, 1, 8, 0, 0)
    timestamps = [start + timedelta(seconds=i * 2) for i in range(num_points)]

    # Smooth speed profile with acceleration, cruise, deceleration cycles
    t = np.linspace(0, 100, num_points)
    base = np.sin(t / 10) * 18 + 55
    speed = np.clip(base + np.random.normal(0, 4, num_points), 0, 130)
    speed = np.clip(speed, 0, 120)

    # Cumulative odometer
    delta_km = (speed / 3.6) * (2 / 3600)
    odometer = np.concatenate(([0.0], np.cumsum(delta_km[:-1])))

    battery_voltage = np.clip(360 + np.random.normal(0, 4, num_points), 300, 400)
    battery_current = np.clip(40 + speed * 0.8 + np.random.normal(0, 10, num_points), 0, 220)

    battery_temp = np.clip(28 + (speed / 120) * 25 + np.random.normal(0, 2, num_points), 20, 65)
    soc = np.clip(100 - np.linspace(0, 32, num_points) + np.random.normal(0, 1.5, num_points), 5, 100)

    e_motor_speed = np.clip(speed * 85 + np.random.normal(0, 35, num_points), 0, 12000)
    motor_temp = np.clip(35 + (e_motor_speed / 1000) * 8 + np.random.normal(0, 2.5, num_points), 25, 95)
    inverter_temp = np.clip(30 + (battery_current / 8) + np.random.normal(0, 2, num_points), 25, 90)
    coolant_temp = np.clip(40 + (motor_temp - 30) * 0.45 + np.random.normal(0, 1.2, num_points), 30, 80)

    throttle = np.clip((speed / 130) * 100 + np.random.normal(0, 7, num_points), 0, 100)
    brake_pressure = np.clip((130 - speed) * 0.55 + np.random.normal(0, 3, num_points), 0, 85)
    steering_angle = np.clip(np.sin(t / 10) * 12 + np.random.normal(0, 2, num_points), -30, 30)

    acceleration = np.gradient(speed, 2.0)
    gear = np.where(speed < 10, 1, np.where(speed < 25, 2, np.where(speed < 45, 3, np.where(speed < 65, 4, 5)))).astype(int)
    ignition = np.ones(num_points, dtype=int)
    ambient_temp = np.full(num_points, 24.0)
    cabin_temp = np.clip(ambient_temp + np.random.normal(0, 2.5, num_points), 18, 32)
    tire_pressure = np.clip(32 + np.random.normal(0, 0.6, num_points), 28, 36)
    gps_lat = 12.9716 + np.linspace(0.0, 0.003, num_points)
    gps_lon = 77.5946 + np.linspace(0.0, 0.004, num_points)

    test_status = []
    for i in range(num_points):
        if soc[i] < 15 or battery_temp[i] > 60 or motor_temp[i] > 85:
            test_status.append('FAIL')
        elif soc[i] < 25 or battery_temp[i] > 50 or motor_temp[i] > 70:
            test_status.append('WARNING')
        else:
            test_status.append('PASS')

    regen = np.clip(np.maximum(-acceleration, 0) * 24 + np.random.normal(0, 3, num_points), 0, 60)

    df = pd.DataFrame({
        'timestamp': timestamps,
        'timestamp_unix': [int(ts.timestamp()) for ts in timestamps],
        'vehicle_id': vehicle_id,
        'vehicle_speed_kmh': speed,
        'e_motor_speed_rpm': e_motor_speed,
        'odometer_km': odometer,
        'ignition_state': ignition,
        'battery_voltage_v': battery_voltage,
        'battery_current_a': battery_current,
        'battery_temperature_c': battery_temp,
        'battery_soc_percent': soc,
        'motor_temperature_c': motor_temp,
        'motor_current_a': battery_current * 0.85,
        'inverter_temperature_c': inverter_temp,
        'coolant_temperature_c': coolant_temp,
        'throttle_position_pct': throttle,
        'brake_pressure_bar': brake_pressure,
        'steering_angle_deg': steering_angle,
        'acceleration_ms2': acceleration,
        'gear_position': gear,
        'cabin_temperature_c': cabin_temp,
        'ambient_temperature_c': ambient_temp,
        'tire_pressure_psi': tire_pressure,
        'gps_latitude': gps_lat,
        'gps_longitude': gps_lon,
        'test_cycle': 'urban_cycle',
        'test_status': test_status,
        'regenerative_braking_kw': regen,
    })
    return df


def main():
    os.makedirs('data', exist_ok=True)
    vehicles = ['VEH-001', 'VEH-002', 'VEH-003']
    final_df = pd.concat([generate_vehicle_data(v, 2000) for v in vehicles], ignore_index=True)
    final_df.to_csv('data/sample_vehicle_data.csv', index=False)
    print(f'Generated {len(final_df)} rows for {len(vehicles)} vehicles.')
    print(final_df.head())


if __name__ == '__main__':
    main()
