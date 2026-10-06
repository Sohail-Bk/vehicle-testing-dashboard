import os
import pandas as pd
import dash
from dash import dcc, html, Input, Output, State, ctx
import plotly.graph_objects as go
from io import StringIO


DATA_PATH = 'data/sample_vehicle_data.csv'

# canonical field names for flexible CSV import
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
    if not os.path.exists(DATA_PATH):
        os.makedirs('data', exist_ok=True)
        import generate_sample_data
        generate_sample_data.generate_all_data()


def normalize_columns(df):
    lower_map = {str(c).strip().lower(): c for c in df.columns}
    mapped = df.copy()
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            low_alias = alias.lower()
            if low_alias in lower_map:
                mapped[canonical] = pd.to_datetime(mapped[lower_map[low_alias]], errors='coerce') if canonical == 'timestamp' else mapped[lower_map[low_alias]]
                break
    return mapped


def coerce_data(df):
    result = normalize_columns(df)
    if 'timestamp' in result.columns:
        result['timestamp'] = pd.to_datetime(result['timestamp'], errors='coerce')
    if 'vehicle_id' in result.columns:
        result['vehicle_id'] = result['vehicle_id'].fillna('UNKNOWN').astype(str)
    # fill missing numeric columns with safe defaults
    for col in ['vehicle_speed_kmh', 'e_motor_speed_rpm', 'odometer_km', 'battery_voltage_v', 'battery_current_a', 'battery_temperature_c',
                'battery_soc_percent', 'motor_temperature_c', 'motor_current_a', 'inverter_temperature_c', 'coolant_temperature_c',
                'throttle_position_pct', 'brake_pressure_bar', 'steering_angle_deg', 'acceleration_ms2', 'gear_position',
                'cabin_temperature_c', 'ambient_temperature_c', 'tire_pressure_psi', 'gps_latitude', 'gps_longitude', 'regenerative_braking_kw']:
        if col in result.columns:
            result[col] = pd.to_numeric(result[col], errors='coerce')
    return result


def load_sample_df():
    ensure_sample_data()
    df = pd.read_csv(DATA_PATH)
    return coerce_data(df)


sample_df = load_sample_df()

app = dash.Dash(__name__)
app.title = 'EV Vehicle Testing Dashboard'


# Global state for uploaded data
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


def make_line_chart(x, y, title, yaxis_title, color='#2563eb'):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode='lines', line={'color': color, 'width': 2}, name=title))
    fig.update_layout(
        title=title,
        template='plotly_white',
        paper_bgcolor='white',
        plot_bgcolor='#f8fafc',
        margin=dict(l=20, r=20, t=40, b=20),
        height=300,
        hovermode='x unified',
    )
    fig.update_xaxes(title_text='Time')
    fig.update_yaxes(title_text=yaxis_title)
    return fig


app.layout = html.Div([
    html.Div([
        html.H1('🚗 EV Vehicle Testing Dashboard', style={'color': 'white', 'margin': 0}),
        html.P('Automotive time-series reporting for battery, drivetrain, and thermal health',
               style={'color': '#dfefff', 'margin': '6px 0 0 0'})
    ], style={'backgroundColor': '#0f4c81', 'padding': '20px 24px', 'borderBottom': '4px solid #f59e0b'}),

    html.Div([
        html.Div([
            html.Label('Data source', style={'fontWeight': 'bold'}),
            dcc.RadioItems(
                id='data-source',
                options=[
                    {'label': 'Use sample data', 'value': 'sample'},
                    {'label': 'Upload CSV', 'value': 'upload'}
                ],
                value='sample',
                inline=True,
                style={'marginTop': '8px'}
            ),
            dcc.Upload(
                id='upload-data',
                children=html.Div(['Drag and Drop or ', html.A('Select CSV File')]),
                style={
                    'width': '100%',
                    'height': '40px',
                    'lineHeight': '40px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'marginTop': '10px',
                    'display': 'none'
                },
                multiple=False,
            )
        ], style={'flex': '0.9', 'paddingRight': '20px'}),

        html.Div([
            html.Label('Vehicle ID', style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='vehicle-dropdown',
                options=[],
                value=None,
                clearable=False,
                style={'marginTop': '6px'}
            )
        ], style={'flex': '1.1', 'paddingRight': '10px'}),

        html.Div([
            html.Label('Date range', style={'fontWeight': 'bold'}),
            dcc.DatePickerRange(
                id='date-range',
                start_date=None,
                end_date=None,
                display_format='YYYY-MM-DD'
            )
        ], style={'flex': '1', 'paddingLeft': '10px'})
    ], style={'display': 'flex', 'padding': '20px', 'backgroundColor': '#f5f7fb'}),

    html.Div(id='status-message', style={'padding': '0 20px', 'color': '#0f766e', 'fontWeight': 'bold'}),
    html.Div(id='kpi-cards', style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(200px, 1fr))', 'gap': '16px', 'padding': '0 20px 20px'}),

    html.Div([
        html.Div([dcc.Graph(id='speed-chart')], style={'flex': '1', 'padding': '10px'}),
        html.Div([dcc.Graph(id='rpm-chart')], style={'flex': '1', 'padding': '10px'})
    ], style={'display': 'flex', 'flexWrap': 'wrap'}),

    html.Div([
        html.Div([dcc.Graph(id='battery-voltage-chart')], style={'flex': '1', 'padding': '10px'}),
        html.Div([dcc.Graph(id='battery-current-chart')], style={'flex': '1', 'padding': '10px'})
    ], style={'display': 'flex', 'flexWrap': 'wrap'}),

    html.Div([
        html.Div([dcc.Graph(id='soc-chart')], style={'flex': '1', 'padding': '10px'}),
        html.Div([dcc.Graph(id='battery-temp-chart')], style={'flex': '1', 'padding': '10px'})
    ], style={'display': 'flex', 'flexWrap': 'wrap'}),

    html.Div([
        html.Div([dcc.Graph(id='motor-temp-chart')], style={'flex': '1', 'padding': '10px'}),
        html.Div([dcc.Graph(id='regen-chart')], style={'flex': '1', 'padding': '10px'})
    ], style={'display': 'flex', 'flexWrap': 'wrap'}),

    html.Div([
        html.Div([dcc.Graph(id='coolant-chart')], style={'flex': '1', 'padding': '10px'}),
        html.Div([dcc.Graph(id='throttle-chart')], style={'flex': '1', 'padding': '10px'})
    ], style={'display': 'flex', 'flexWrap': 'wrap'}),

    html.Div([
        html.H3('Summary Report', style={'marginBottom': '10px'}),
        html.Div(id='summary-table')
    ], style={'padding': '20px'})
], style={'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#ffffff'})


@app.callback(
    Output('vehicle-dropdown', 'options'),
    Output('vehicle-dropdown', 'value'),
    Output('date-range', 'start_date'),
    Output('date-range', 'end_date'),
    Output('status-message', 'children'),
    Input('data-source', 'value'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def update_data_source(source_value, contents, filename):
    global uploaded_df
    if source_value == 'sample':
        uploaded_df = None
        frame = sample_df
        vehicles_list = sorted(frame['vehicle_id'].dropna().astype(str).unique().tolist())
        default_value = vehicles_list[0] if vehicles_list else None
        return (
            [{'label': v, 'value': v} for v in vehicles_list],
            default_value,
            frame['timestamp'].min().date() if not frame.empty else None,
            frame['timestamp'].max().date() if not frame.empty else None,
            'Sample data loaded.'
        )

    if contents is not None:
        content_type, content_string = contents.split(',')
        decoded = StringIO(content_string.encode('utf-8').decode('utf-8'))
        df_upload = pd.read_csv(decoded)
        frame = coerce_data(df_upload)
        uploaded_df = frame
        vehicles_list = sorted(frame['vehicle_id'].dropna().astype(str).unique().tolist())
        default_value = vehicles_list[0] if vehicles_list else None
        message = f'Loaded uploaded file: {filename}'
        return (
            [{'label': v, 'value': v} for v in vehicles_list],
            default_value,
            frame['timestamp'].min().date() if not frame.empty else None,
            frame['timestamp'].max().date() if not frame.empty else None,
            message
        )

    # if upload mode but no file, keep sample fallback
    frame = sample_df
    vehicles_list = sorted(frame['vehicle_id'].dropna().astype(str).unique().tolist())
    default_value = vehicles_list[0] if vehicles_list else None
    return (
        [{'label': v, 'value': v} for v in vehicles_list],
        default_value,
        frame['timestamp'].min().date() if not frame.empty else None,
        frame['timestamp'].max().date() if not frame.empty else None,
        'No file uploaded yet. Sample data is active.'
    )


@app.callback(
    Output('upload-data', 'style'),
    Input('data-source', 'value')
)
def show_upload_style(data_source):
    style = {
        'width': '100%',
        'height': '40px',
        'lineHeight': '40px',
        'borderWidth': '1px',
        'borderStyle': 'dashed',
        'borderRadius': '5px',
        'textAlign': 'center',
        'marginTop': '10px'
    }
    if data_source == 'upload':
        style['display'] = 'block'
    else:
        style['display'] = 'none'
    return style


@app.callback(
    Output('kpi-cards', 'children'),
    Input('vehicle-dropdown', 'value'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date')
)
def update_kpis(vehicle_id, start_date, end_date):
    if vehicle_id is None:
        return []
    dfx = get_filtered_data(vehicle_id, start_date, end_date)
    if dfx.empty:
        return []

    stats = [
        ('Max Speed', f'{dfx["vehicle_speed_kmh"].max():.1f} km/h', '#2563eb'),
        ('Avg Speed', f'{dfx["vehicle_speed_kmh"].mean():.1f} km/h', '#0ea5e9'),
        ('Distance', f'{dfx["odometer_km"].iloc[-1] - dfx["odometer_km"].iloc[0]:.1f} km', '#16a34a'),
        ('Final SOC', f'{dfx["battery_soc_percent"].iloc[-1]:.1f}%', '#9333ea'),
        ('Max Battery Temp', f'{dfx["battery_temperature_c"].max():.1f} °C', '#f97316'),
        ('Peak RPM', f'{dfx["e_motor_speed_rpm"].max():.0f}', '#ef4444'),
        ('Status', dfx['test_status'].mode().iloc[0] if 'test_status' in dfx.columns else 'N/A', '#f59e0b'),
        ('Total Regen', f'{dfx["regenerative_braking_kw"].sum():.1f} kW', '#10b981')
    ]

    cards = []
    for title, value, color in stats:
        cards.append(html.Div([
            html.Div(title, style={'fontSize': '13px', 'color': '#667085', 'marginBottom': '8px'}),
            html.Div(value, style={'fontSize': '28px', 'fontWeight': 'bold', 'color': color})
        ], style={'padding': '18px 16px', 'backgroundColor': '#f8fafc', 'borderLeft': f'4px solid {color}', 'borderRadius': '8px'}))
    return cards


@app.callback(Output('speed-chart', 'figure'), Input('vehicle-dropdown', 'value'), Input('date-range', 'start_date'), Input('date-range', 'end_date'))
def update_speed(vehicle_id, start_date, end_date):
    if vehicle_id is None:
        return go.Figure()
    dfx = get_filtered_data(vehicle_id, start_date, end_date)
    if 'vehicle_speed_kmh' not in dfx.columns:
        return go.Figure()
    return make_line_chart(dfx['timestamp'], dfx['vehicle_speed_kmh'], 'Vehicle Speed', 'km/h', '#2563eb')


@app.callback(Output('rpm-chart', 'figure'), Input('vehicle-dropdown', 'value'), Input('date-range', 'start_date'), Input('date-range', 'end_date'))
def update_rpm(vehicle_id, start_date, end_date):
    if vehicle_id is None:
        return go.Figure()
    dfx = get_filtered_data(vehicle_id, start_date, end_date)
    if 'e_motor_speed_rpm' not in dfx.columns:
        return go.Figure()
    return make_line_chart(dfx['timestamp'], dfx['e_motor_speed_rpm'], 'E-Motor Speed', 'RPM', '#f97316')


@app.callback(Output('battery-voltage-chart', 'figure'), Input('vehicle-dropdown', 'value'), Input('date-range', 'start_date'), Input('date-range', 'end_date'))
def update_voltage(vehicle_id, start_date, end_date):
    if vehicle_id is None:
        return go.Figure()
    dfx = get_filtered_data(vehicle_id, start_date, end_date)
    if 'battery_voltage_v' not in dfx.columns:
        return go.Figure()
    return make_line_chart(dfx['timestamp'], dfx['battery_voltage_v'], 'Battery Voltage', 'V', '#16a34a')


@app.callback(Output('battery-current-chart', 'figure'), Input('vehicle-dropdown', 'value'), Input('date-range', 'start_date'), Input('date-range', 'end_date'))
def update_current(vehicle_id, start_date, end_date):
    if vehicle_id is None:
        return go.Figure()
    dfx = get_filtered_data(vehicle_id, start_date, end_date)
    if 'battery_current_a' not in dfx.columns:
        return go.Figure()
    return make_line_chart(dfx['timestamp'], dfx['battery_current_a'], 'Battery Current', 'A', '#ef4444')


@app.callback(Output('soc-chart', 'figure'), Input('vehicle-dropdown', 'value'), Input('date-range', 'start_date'), Input('date-range', 'end_date'))
def update_soc(vehicle_id, start_date, end_date):
    if vehicle_id is None:
        return go.Figure()
    dfx = get_filtered_data(vehicle_id, start_date, end_date)
    if 'battery_soc_percent' not in dfx.columns:
        return go.Figure()
    return make_line_chart(dfx['timestamp'], dfx['battery_soc_percent'], 'Battery SOC', '%', '#9333ea')


@app.callback(Output('battery-temp-chart', 'figure'), Input('vehicle-dropdown', 'value'), Input('date-range', 'start_date'), Input('date-range', 'end_date'))
def update_battery_temp(vehicle_id, start_date, end_date):
    if vehicle_id is None:
        return go.Figure()
    dfx = get_filtered_data(vehicle_id, start_date, end_date)
    if 'battery_temperature_c' not in dfx.columns:
        return go.Figure()
    return make_line_chart(dfx['timestamp'], dfx['battery_temperature_c'], 'Battery Temperature', '°C', '#f59e0b')


@app.callback(Output('motor-temp-chart', 'figure'), Input('vehicle-dropdown', 'value'), Input('date-range', 'start_date'), Input('date-range', 'end_date'))
def update_motor_temp(vehicle_id, start_date, end_date):
    if vehicle_id is None:
        return go.Figure()
    dfx = get_filtered_data(vehicle_id, start_date, end_date)
    if 'motor_temperature_c' not in dfx.columns:
        return go.Figure()
    return make_line_chart(dfx['timestamp'], dfx['motor_temperature_c'], 'Motor Temperature', '°C', '#ec4899')


@app.callback(Output('regen-chart', 'figure'), Input('vehicle-dropdown', 'value'), Input('date-range', 'start_date'), Input('date-range', 'end_date'))
def update_regen(vehicle_id, start_date, end_date):
    if vehicle_id is None:
        return go.Figure()
    dfx = get_filtered_data(vehicle_id, start_date, end_date)
    if 'regenerative_braking_kw' not in dfx.columns:
        return go.Figure()
    return make_line_chart(dfx['timestamp'], dfx['regenerative_braking_kw'], 'Regenerative Braking', 'kW', '#10b981')


@app.callback(Output('coolant-chart', 'figure'), Input('vehicle-dropdown', 'value'), Input('date-range', 'start_date'), Input('date-range', 'end_date'))
def update_coolant(vehicle_id, start_date, end_date):
    if vehicle_id is None:
        return go.Figure()
    dfx = get_filtered_data(vehicle_id, start_date, end_date)
    fig = go.Figure()
    if 'coolant_temperature_c' in dfx.columns:
        fig.add_trace(go.Scatter(x=dfx['timestamp'], y=dfx['coolant_temperature_c'], mode='lines', name='Coolant', line={'color': '#0ea5e9'}))
    if 'inverter_temperature_c' in dfx.columns:
        fig.add_trace(go.Scatter(x=dfx['timestamp'], y=dfx['inverter_temperature_c'], mode='lines', name='Inverter', line={'color': '#f97316'}))
    fig.update_layout(title='Coolant vs Inverter Temperature', template='plotly_white', height=300, hovermode='x unified')
    fig.update_xaxes(title_text='Time')
    fig.update_yaxes(title_text='°C')
    return fig


@app.callback(Output('throttle-chart', 'figure'), Input('vehicle-dropdown', 'value'), Input('date-range', 'start_date'), Input('date-range', 'end_date'))
def update_throttle(vehicle_id, start_date, end_date):
    if vehicle_id is None:
        return go.Figure()
    dfx = get_filtered_data(vehicle_id, start_date, end_date)
    if 'throttle_position_pct' not in dfx.columns:
        return go.Figure()
    return make_line_chart(dfx['timestamp'], dfx['throttle_position_pct'], 'Throttle Position', '%', '#6366f1')


@app.callback(Output('summary-table', 'children'), Input('vehicle-dropdown', 'value'), Input('date-range', 'start_date'), Input('date-range', 'end_date'))
def update_summary_table(vehicle_id, start_date, end_date):
    if vehicle_id is None:
        return html.Div('No vehicle selected')
    dfx = get_filtered_data(vehicle_id, start_date, end_date)
    if dfx.empty:
        return html.Div('No data available')

    rows = []
    metric_rows = [
        ('Vehicle Speed (km/h)', 'vehicle_speed_kmh'),
        ('E-Motor Speed (RPM)', 'e_motor_speed_rpm'),
        ('Battery Voltage (V)', 'battery_voltage_v'),
        ('Battery Current (A)', 'battery_current_a'),
        ('Battery Temp (°C)', 'battery_temperature_c'),
        ('Motor Temp (°C)', 'motor_temperature_c'),
        ('SOC (%)', 'battery_soc_percent'),
        ('Odometer (km)', 'odometer_km'),
        ('Throttle (%)', 'throttle_position_pct'),
        ('Tire Pressure (psi)', 'tire_pressure_psi')
    ]

    for label, col in metric_rows:
        if col in dfx.columns:
            rows.append((label, dfx[col].min(), dfx[col].mean(), dfx[col].max()))

    table = html.Table([
        html.Thead(html.Tr([
            html.Th('Metric', style={'padding': '8px', 'backgroundColor': '#e2e8f0'}),
            html.Th('Min', style={'padding': '8px', 'backgroundColor': '#e2e8f0'}),
            html.Th('Average', style={'padding': '8px', 'backgroundColor': '#e2e8f0'}),
            html.Th('Max', style={'padding': '8px', 'backgroundColor': '#e2e8f0'})
        ])),
        html.Tbody([
            html.Tr([
                html.Td(r[0], style={'padding': '8px', 'borderBottom': '1px solid #e2e8f0'}),
                html.Td(f'{r[1]:.2f}' if pd.notna(r[1]) else 'N/A', style={'padding': '8px', 'borderBottom': '1px solid #e2e8f0'}),
                html.Td(f'{r[2]:.2f}' if pd.notna(r[2]) else 'N/A', style={'padding': '8px', 'borderBottom': '1px solid #e2e8f0'}),
                html.Td(f'{r[3]:.2f}' if pd.notna(r[3]) else 'N/A', style={'padding': '8px', 'borderBottom': '1px solid #e2e8f0'})
            ]) for r in rows
        ])
    ], style={'width': '100%', 'borderCollapse': 'collapse'})
    return table


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
