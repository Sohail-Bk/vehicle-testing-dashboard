from io import BytesIO, StringIO
from pathlib import Path

import pandas as pd

from data.generate_sample_data import generate_all_data

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT_DIR / 'data' / 'sample_vehicle_data.csv'

COLUMN_ALIASES = {
    'timestamp': ['timestamp', 'time', 'date_time', 'datetime'],
    'vehicle_id': ['vehicle_id', 'vehicle', 'veh_id', 'unit_id', 'test_vehicle'],
    'vehicle_speed_kmh': ['vehicle_speed_kmh', 'speed_kmh', 'speed', 'vehicle_speed'],
    'e_motor_speed_rpm': ['e_motor_speed_rpm', 'motor_speed_rpm', 'emotor_rpm', 'motor_rpm'],
    'odometer_km': ['odometer_km', 'odometer', 'distance_km'],
    'ignition_state': ['ignition_state', 'ignition', 'ignition_on'],
    'battery_voltage_v': ['battery_voltage_v', 'battery_voltage', 'voltage_v'],
    'battery_current_a': ['battery_current_a', 'battery_current', 'current_a'],
    'battery_temperature_c': ['battery_temperature_c', 'battery_temp_c', 'battery_temp'],
    'battery_soc_percent': ['battery_soc_percent', 'soc_percent', 'soc', 'state_of_charge'],
    'motor_temperature_c': ['motor_temperature_c', 'motor_temp_c', 'motor_temp'],
    'motor_current_a': ['motor_current_a', 'motor_current', 'phase_current_a'],
    'inverter_temperature_c': ['inverter_temperature_c', 'inverter_temp_c', 'inverter_temp'],
    'coolant_temperature_c': ['coolant_temperature_c', 'coolant_temp_c', 'coolant_temp'],
    'throttle_position_pct': ['throttle_position_pct', 'throttle_pct', 'throttle'],
    'brake_pressure_bar': ['brake_pressure_bar', 'brake_pressure', 'brake_bar'],
    'steering_angle_deg': ['steering_angle_deg', 'steering_angle', 'steering_deg'],
    'acceleration_ms2': ['acceleration_ms2', 'accel_ms2', 'acceleration'],
    'gear_position': ['gear_position', 'gear', 'gear_state'],
    'cabin_temperature_c': ['cabin_temperature_c', 'cabin_temp_c', 'cabin_temp'],
    'ambient_temperature_c': ['ambient_temperature_c', 'ambient_temp_c', 'ambient_temp'],
    'tire_pressure_psi': ['tire_pressure_psi', 'tire_pressure', 'pressure_psi'],
    'gps_latitude': ['gps_latitude', 'lat', 'latitude'],
    'gps_longitude': ['gps_longitude', 'lon', 'longitude'],
    'test_cycle': ['test_cycle', 'cycle_name', 'drive_cycle'],
    'test_status': ['test_status', 'status', 'result'],
    'regenerative_braking_kw': ['regenerative_braking_kw', 'regen_kw', 'regeneration_kw'],
}


def ensure_sample_data():
    if not DATA_PATH.exists():
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        generate_all_data()


def normalize_columns(df):
    lower_map = {str(c).strip().lower(): c for c in df.columns}
    mapped = df.copy()
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias.lower() in lower_map:
                source_col = lower_map[alias.lower()]
                mapped[canonical] = mapped[source_col]
                break
    return mapped


def coerce_data(df):
    result = normalize_columns(df)
    if 'timestamp' in result.columns:
        result['timestamp'] = pd.to_datetime(result['timestamp'], errors='coerce')
    if 'vehicle_id' in result.columns:
        result['vehicle_id'] = result['vehicle_id'].fillna('UNKNOWN').astype(str)
    numeric_cols = [
        'vehicle_speed_kmh', 'e_motor_speed_rpm', 'odometer_km', 'battery_voltage_v', 'battery_current_a',
        'battery_temperature_c', 'battery_soc_percent', 'motor_temperature_c', 'motor_current_a',
        'inverter_temperature_c', 'coolant_temperature_c', 'throttle_position_pct', 'brake_pressure_bar',
        'steering_angle_deg', 'acceleration_ms2', 'gear_position', 'cabin_temperature_c',
        'ambient_temperature_c', 'tire_pressure_psi', 'gps_latitude', 'gps_longitude', 'regenerative_braking_kw'
    ]
    for col in numeric_cols:
        if col in result.columns:
            result[col] = pd.to_numeric(result[col], errors='coerce')
    return result


def load_sample_df():
    ensure_sample_data()
    df = pd.read_csv(DATA_PATH)
    return coerce_data(df)


sample_df = load_sample_df()
uploaded_df = None


def get_current_df():
    return uploaded_df if uploaded_df is not None else sample_df


def get_filtered_data(vehicle_id, start_date, end_date):
    frame = get_current_df()
    if frame.empty:
        return frame
    filtered = frame[frame['vehicle_id'] == vehicle_id].copy()
    if start_date is not None:
        filtered = filtered[filtered['timestamp'] >= pd.Timestamp(start_date)]
    if end_date is not None:
        filtered = filtered[filtered['timestamp'] <= pd.Timestamp(end_date) + pd.Timedelta(days=1)]
    return filtered


def get_filtered_data_for_vehicles(vehicle_ids, start_date, end_date):
    if not vehicle_ids:
        return pd.DataFrame(columns=get_current_df().columns)
    frame = get_current_df()
    filtered = frame[frame['vehicle_id'].isin(vehicle_ids)].copy()
    if start_date is not None:
        filtered = filtered[filtered['timestamp'] >= pd.Timestamp(start_date)]
    if end_date is not None:
        filtered = filtered[filtered['timestamp'] <= pd.Timestamp(end_date) + pd.Timedelta(days=1)]
    return filtered
