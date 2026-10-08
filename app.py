import os
from io import BytesIO, StringIO

import dash
import pandas as pd
from dash import Input, Output, State, dcc, html
import plotly.graph_objects as go
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

DATA_PATH = 'data/sample_vehicle_data.csv'

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
app = dash.Dash(__name__)
app.title = 'EV Vehicle Testing Dashboard'

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


def compute_faults(dfx):
    if dfx.empty:
        return pd.DataFrame(columns=['timestamp', 'severity', 'code', 'message'])

    faults = []
    for _, row in dfx.iterrows():
        ts = row['timestamp']
        if pd.notna(row.get('battery_soc_percent')) and row['battery_soc_percent'] < 20:
            faults.append({'timestamp': ts, 'severity': 'Critical', 'code': 'LOW_SOC', 'message': f"SOC low at {row['battery_soc_percent']:.1f}%"})
        if pd.notna(row.get('battery_temperature_c')) and row['battery_temperature_c'] > 55:
            faults.append({'timestamp': ts, 'severity': 'Warning', 'code': 'BAT_TEMP_HIGH', 'message': f"Battery temp {row['battery_temperature_c']:.1f}°C"})
        if pd.notna(row.get('motor_temperature_c')) and row['motor_temperature_c'] > 75:
            faults.append({'timestamp': ts, 'severity': 'Warning', 'code': 'MOTOR_TEMP_HIGH', 'message': f"Motor temp {row['motor_temperature_c']:.1f}°C"})
        if pd.notna(row.get('inverter_temperature_c')) and row['inverter_temperature_c'] > 80:
            faults.append({'timestamp': ts, 'severity': 'Critical', 'code': 'INVERTER_TEMP_HIGH', 'message': f"Inverter temp {row['inverter_temperature_c']:.1f}°C"})
        if pd.notna(row.get('battery_voltage_v')) and row['battery_voltage_v'] < 300:
            faults.append({'timestamp': ts, 'severity': 'Critical', 'code': 'BAT_VOLT_LOW', 'message': f"Battery voltage {row['battery_voltage_v']:.1f}V"})
        if pd.notna(row.get('battery_voltage_v')) and row['battery_voltage_v'] > 400:
            faults.append({'timestamp': ts, 'severity': 'Critical', 'code': 'BAT_VOLT_HIGH', 'message': f"Battery voltage {row['battery_voltage_v']:.1f}V"})
        if pd.notna(row.get('battery_current_a')) and row['battery_current_a'] > 180:
            faults.append({'timestamp': ts, 'severity': 'Warning', 'code': 'CURRENT_HIGH', 'message': f"Current {row['battery_current_a']:.1f}A"})
        if pd.notna(row.get('regenerative_braking_kw')) and row['regenerative_braking_kw'] > 50:
            faults.append({'timestamp': ts, 'severity': 'Info', 'code': 'REGEN_HIGH', 'message': f"Regen power {row['regenerative_braking_kw']:.1f}kW"})
        if pd.notna(row.get('vehicle_speed_kmh')) and row['vehicle_speed_kmh'] > 120:
            faults.append({'timestamp': ts, 'severity': 'Warning', 'code': 'SPEED_HIGH', 'message': f"Speed {row['vehicle_speed_kmh']:.1f} km/h"})

    return pd.DataFrame(faults)


def get_kpi_rows(dfx):
    rows = []
    if 'vehicle_speed_kmh' in dfx.columns:
        rows.append(('Max Speed', f"{dfx['vehicle_speed_kmh'].max():.1f} km/h"))
        rows.append(('Avg Speed', f"{dfx['vehicle_speed_kmh'].mean():.1f} km/h"))
    if 'odometer_km' in dfx.columns and len(dfx) > 0:
        rows.append(('Distance', f"{dfx['odometer_km'].iloc[-1] - dfx['odometer_km'].iloc[0]:.1f} km"))
    if 'battery_soc_percent' in dfx.columns:
        rows.append(('Final SOC', f"{dfx['battery_soc_percent'].iloc[-1]:.1f}%"))
    if 'battery_temperature_c' in dfx.columns:
        rows.append(('Max Battery Temp', f"{dfx['battery_temperature_c'].max():.1f} °C"))
    if 'e_motor_speed_rpm' in dfx.columns:
        rows.append(('Peak RPM', f"{dfx['e_motor_speed_rpm'].max():.0f}"))
    if 'test_status' in dfx.columns:
        rows.append(('Status', dfx['test_status'].mode().iloc[0] if not dfx['test_status'].empty else 'N/A'))
    if 'regenerative_braking_kw' in dfx.columns:
        rows.append(('Total Regen', f"{dfx['regenerative_braking_kw'].sum():.1f} kW"))
    return rows


def export_report_pdf(dfx, vehicle_id, start_date, end_date):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph('EV Vehicle Testing Dashboard Report', styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f'Vehicle: {vehicle_id}', styles['Heading2']))
    story.append(Paragraph(f'Date range: {start_date or "All"} to {end_date or "All"}', styles['Normal']))
    story.append(Paragraph(f'Generated: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")}', styles['Normal']))
    story.append(Spacer(1, 16))

    kpi_rows = [['Metric', 'Value']] + get_kpi_rows(dfx)
    kpi_table = Table(kpi_rows, colWidths=[200, 220])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f4c81')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 18))

    faults = compute_faults(dfx)
    fault_rows = [['Time', 'Severity', 'Code', 'Message']]
    for _, row in faults.head(10).iterrows():
        fault_rows.append([
            pd.to_datetime(row['timestamp']).strftime('%Y-%m-%d %H:%M:%S') if pd.notna(row['timestamp']) else 'N/A',
            row['severity'],
            row['code'],
            row['message']
        ])

    if len(fault_rows) == 1:
        story.append(Paragraph('No active faults detected in the selected time range.', styles['Normal']))
    else:
        fault_table = Table(fault_rows, colWidths=[90, 65, 75, 275])
        fault_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#cbd5e1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ]))
        story.append(fault_table)

    story.append(Spacer(1, 18))
    preview_rows = [['Timestamp', 'Speed (km/h)', 'SOC (%)', 'Battery Temp (°C)', 'Status']]
    for _, row in dfx.head(12).iterrows():
        preview_rows.append([
            pd.to_datetime(row['timestamp']).strftime('%Y-%m-%d %H:%M:%S') if pd.notna(row.get('timestamp')) else 'N/A',
            f"{row['vehicle_speed_kmh']:.1f}" if pd.notna(row.get('vehicle_speed_kmh')) else 'N/A',
            f"{row['battery_soc_percent']:.1f}" if pd.notna(row.get('battery_soc_percent')) else 'N/A',
            f"{row['battery_temperature_c']:.1f}" if pd.notna(row.get('battery_temperature_c')) else 'N/A',
            str(row['test_status']) if pd.notna(row.get('test_status')) else 'N/A'
        ])
    preview_table = Table(preview_rows, colWidths=[90, 80, 65, 95, 160])
    preview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
    ]))
    story.append(Paragraph('Data Preview', styles['Heading2']))
    story.append(preview_table)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


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
            dcc.Dropdown(id='vehicle-dropdown', options=[], value=None, clearable=False, style={'marginTop': '6px'})
        ], style={'flex': '1.1', 'paddingRight': '10px'}),

        html.Div([
            html.Label('Date range', style={'fontWeight': 'bold'}),
            dcc.DatePickerRange(id='date-range', start_date=None, end_date=None, display_format='YYYY-MM-DD')
        ], style={'flex': '1', 'paddingLeft': '10px'})
    ], style={'display': 'flex', 'padding': '20px', 'backgroundColor': '#f5f7fb'}),

    html.Div([
        html.Div([
            html.Label('Compare vehicles', style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='comparison-vehicles',
                options=[],
                value=[],
                multi=True,
                style={'marginTop': '6px'}
            )
        ], style={'padding': '0 20px 20px', 'maxWidth': '60%'}),
    ]),

    html.Div(id='status-message', style={'padding': '0 20px', 'color': '#0f766e', 'fontWeight': 'bold'}),
    html.Div([
        html.Div([
            html.Label('Export format', style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='report-format',
                options=[
                    {'label': 'PDF', 'value': 'pdf'},
                    {'label': 'CSV', 'value': 'csv'}
                ],
                value='pdf',
                clearable=False,
                style={'marginTop': '6px', 'width': '160px'}
            )
        ], style={'margin': '0 20px 20px 20px'}),
        html.Button('Export current report', id='export-report-btn', n_clicks=0, style={
            'margin': '0 20px 20px 0',
            'padding': '10px 18px',
            'backgroundColor': '#0f4c81',
            'color': 'white',
            'border': 'none',
            'borderRadius': '8px',
            'cursor': 'pointer',
            'fontWeight': 'bold'
        }),
        dcc.Download(id='download-report')
    ], style={'display': 'flex', 'alignItems': 'flex-end', 'flexWrap': 'wrap'}),

    html.Div(id='fault-cards', style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(200px, 1fr))', 'gap': '16px', 'padding': '0 20px 20px'}),
    html.Div(id='kpi-cards', style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(200px, 1fr))', 'gap': '16px', 'padding': '0 20px 20px'}),

    html.Div([
        html.H3('Vehicle Comparison', style={'marginLeft': '20px'}),
        html.Div(id='comparison-kpis', style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(220px, 1fr))', 'gap': '16px', 'padding': '0 20px 20px'}),
        html.Div([dcc.Graph(id='comparison-speed-chart')], style={'padding': '10px'}),
        html.Div([dcc.Graph(id='comparison-soc-chart')], style={'padding': '10px'}),
        html.Div([dcc.Graph(id='comparison-temp-chart')], style={'padding': '10px'}),
        html.Div(id='comparison-table', style={'padding': '20px'})
    ]),

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
        html.H3('Fault Log', style={'marginBottom': '10px'}),
        html.Div(id='fault-table')
    ], style={'padding': '20px'})
], style={'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#ffffff'})


@app.callback(
    Output('vehicle-dropdown', 'options'),
    Output('vehicle-dropdown', 'value'),
    Output('comparison-vehicles', 'options'),
    Output('comparison-vehicles', 'value'),
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
        comparison_default = vehicles_list[: min(3, len(vehicles_list))]
        return (
            [{'label': v, 'value': v} for v in vehicles_list],
            default_value,
            [{'label': v, 'value': v} for v in vehicles_list],
            comparison_default,
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
        comparison_default = vehicles_list[: min(3, len(vehicles_list))]
        message = f'Loaded uploaded file: {filename}'
        return (
            [{'label': v, 'value': v} for v in vehicles_list],
            default_value,
            [{'label': v, 'value': v} for v in vehicles_list],
            comparison_default,
            frame['timestamp'].min().date() if not frame.empty else None,
            frame['timestamp'].max().date() if not frame.empty else None,
            message
        )

    frame = sample_df
    vehicles_list = sorted(frame['vehicle_id'].dropna().astype(str).unique().tolist())
    default_value = vehicles_list[0] if vehicles_list else None
    comparison_default = vehicles_list[: min(3, len(vehicles_list))]
    return (
        [{'label': v, 'value': v} for v in vehicles_list],
        default_value,
        [{'label': v, 'value': v} for v in vehicles_list],
        comparison_default,
        frame['timestamp'].min().date() if not frame.empty else None,
        frame['timestamp'].max().date() if not frame.empty else None,
        'No file uploaded yet. Sample data is active.'
    )


@app.callback(Output('upload-data', 'style'), Input('data-source', 'value'))
def show_upload_style(data_source):
    return {
        'width': '100%',
        'height': '40px',
        'lineHeight': '40px',
        'borderWidth': '1px',
        'borderStyle': 'dashed',
        'borderRadius': '5px',
        'textAlign': 'center',
        'marginTop': '10px',
        'display': 'block' if data_source == 'upload' else 'none'
    }


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


@app.callback(
    Output('comparison-kpis', 'children'),
    Input('comparison-vehicles', 'value'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date')
)
def update_comparison_kpis(vehicle_ids, start_date, end_date):
    if not vehicle_ids:
        return []
    frame = get_filtered_data_for_vehicles(vehicle_ids, start_date, end_date)
    if frame.empty:
        return []

    summary = []
    for vehicle in vehicle_ids:
        dfx = frame[frame['vehicle_id'] == vehicle].copy()
        if dfx.empty:
            continue
        summary.append({
            'vehicle': vehicle,
            'avg_speed': dfx['vehicle_speed_kmh'].mean() if 'vehicle_speed_kmh' in dfx.columns else 0,
            'final_soc': dfx['battery_soc_percent'].iloc[-1] if 'battery_soc_percent' in dfx.columns else 0,
            'max_temp': dfx['battery_temperature_c'].max() if 'battery_temperature_c' in dfx.columns else 0,
            'peak_rpm': dfx['e_motor_speed_rpm'].max() if 'e_motor_speed_rpm' in dfx.columns else 0,
        })

    cards = []
    for item in summary:
        cards.append(html.Div([
            html.Div(item['vehicle'], style={'fontSize': '13px', 'color': '#667085', 'marginBottom': '8px'}),
            html.Div(f"Avg {item['avg_speed']:.1f} km/h", style={'fontSize': '18px', 'fontWeight': 'bold'}),
            html.Div(f"SOC {item['final_soc']:.1f}%", style={'fontSize': '14px'}),
            html.Div(f"Max temp {item['max_temp']:.1f}°C", style={'fontSize': '14px'}),
            html.Div(f"Peak RPM {item['peak_rpm']:.0f}", style={'fontSize': '14px'})
        ], style={'padding': '18px 16px', 'backgroundColor': '#f8fafc', 'borderLeft': '4px solid #0f4c81', 'borderRadius': '8px'}))
    return cards


@app.callback(Output('comparison-speed-chart', 'figure'), Input('comparison-vehicles', 'value'), Input('date-range', 'start_date'), Input('date-range', 'end_date'))
def update_comparison_speed(vehicle_ids, start_date, end_date):
    if not vehicle_ids:
        return go.Figure()
    frame = get_filtered_data_for_vehicles(vehicle_ids, start_date, end_date)
    fig = go.Figure()
    for vehicle in vehicle_ids:
        dfx = frame[frame['vehicle_id'] == vehicle].copy()
        if 'vehicle_speed_kmh' in dfx.columns:
            fig.add_trace(go.Scatter(x=dfx['timestamp'], y=dfx['vehicle_speed_kmh'], mode='lines', name=vehicle))
    fig.update_layout(title='Vehicle Speed Comparison', template='plotly_white', height=300, hovermode='x unified')
    fig.update_xaxes(title_text='Time')
    fig.update_yaxes(title_text='km/h')
    return fig


@app.callback(Output('comparison-soc-chart', 'figure'), Input('comparison-vehicles', 'value'), Input('date-range', 'start_date'), Input('date-range', 'end_date'))
def update_comparison_soc(vehicle_ids, start_date, end_date):
    if not vehicle_ids:
        return go.Figure()
    frame = get_filtered_data_for_vehicles(vehicle_ids, start_date, end_date)
    fig = go.Figure()
    for vehicle in vehicle_ids:
        dfx = frame[frame['vehicle_id'] == vehicle].copy()
        if 'battery_soc_percent' in dfx.columns:
            fig.add_trace(go.Scatter(x=dfx['timestamp'], y=dfx['battery_soc_percent'], mode='lines', name=vehicle))
    fig.update_layout(title='SOC Comparison', template='plotly_white', height=300, hovermode='x unified')
    fig.update_xaxes(title_text='Time')
    fig.update_yaxes(title_text='%')
    return fig


@app.callback(Output('comparison-temp-chart', 'figure'), Input('comparison-vehicles', 'value'), Input('date-range', 'start_date'), Input('date-range', 'end_date'))
def update_comparison_temp(vehicle_ids, start_date, end_date):
    if not vehicle_ids:
        return go.Figure()
    frame = get_filtered_data_for_vehicles(vehicle_ids, start_date, end_date)
    fig = go.Figure()
    for vehicle in vehicle_ids:
        dfx = frame[frame['vehicle_id'] == vehicle].copy()
        if 'battery_temperature_c' in dfx.columns:
            fig.add_trace(go.Scatter(x=dfx['timestamp'], y=dfx['battery_temperature_c'], mode='lines', name=f'{vehicle} Battery'))
    fig.update_layout(title='Battery Temperature Comparison', template='plotly_white', height=300, hovermode='x unified')
    fig.update_xaxes(title_text='Time')
    fig.update_yaxes(title_text='°C')
    return fig


@app.callback(Output('comparison-table', 'children'), Input('comparison-vehicles', 'value'), Input('date-range', 'start_date'), Input('date-range', 'end_date'))
def update_comparison_table(vehicle_ids, start_date, end_date):
    if not vehicle_ids:
        return html.Div('Select vehicles to compare')
    frame = get_filtered_data_for_vehicles(vehicle_ids, start_date, end_date)
    if frame.empty:
        return html.Div('No data available')

    rows = []
    for vehicle in vehicle_ids:
        dfx = frame[frame['vehicle_id'] == vehicle].copy()
        if dfx.empty:
            continue
        rows.append({
            'Vehicle': vehicle,
            'Avg Speed': dfx['vehicle_speed_kmh'].mean() if 'vehicle_speed_kmh' in dfx.columns else 0,
            'Max Temp': dfx['battery_temperature_c'].max() if 'battery_temperature_c' in dfx.columns else 0,
            'Final SOC': dfx['battery_soc_percent'].iloc[-1] if 'battery_soc_percent' in dfx.columns else 0,
            'Peak RPM': dfx['e_motor_speed_rpm'].max() if 'e_motor_speed_rpm' in dfx.columns else 0,
        })

    table = html.Table([
        html.Thead(html.Tr([
            html.Th('Vehicle', style={'padding': '8px', 'backgroundColor': '#e2e8f0'}),
            html.Th('Avg Speed', style={'padding': '8px', 'backgroundColor': '#e2e8f0'}),
            html.Th('Max Temp', style={'padding': '8px', 'backgroundColor': '#e2e8f0'}),
            html.Th('Final SOC', style={'padding': '8px', 'backgroundColor': '#e2e8f0'}),
            html.Th('Peak RPM', style={'padding': '8px', 'backgroundColor': '#e2e8f0'})
        ])),
        html.Tbody([
            html.Tr([
                html.Td(row['Vehicle'], style={'padding': '8px'}),
                html.Td(f"{row['Avg Speed']:.1f}", style={'padding': '8px'}),
                html.Td(f"{row['Max Temp']:.1f}", style={'padding': '8px'}),
                html.Td(f"{row['Final SOC']:.1f}", style={'padding': '8px'}),
                html.Td(f"{row['Peak RPM']:.0f}", style={'padding': '8px'})
            ]) for row in rows
        ])
    ], style={'width': '100%', 'borderCollapse': 'collapse'})
    return table


@app.callback(Output('fault-cards', 'children'), Input('vehicle-dropdown', 'value'), Input('date-range', 'start_date'), Input('date-range', 'end_date'))
def update_fault_cards(vehicle_id, start_date, end_date):
    if vehicle_id is None:
        return []
    dfx = get_filtered_data(vehicle_id, start_date, end_date)
    if dfx.empty:
        return []

    faults = compute_faults(dfx)
    critical = len(faults[faults['severity'] == 'Critical'])
    warnings = len(faults[faults['severity'] == 'Warning'])
    info = len(faults[faults['severity'] == 'Info'])

    cards = [
        ('Critical', critical, '#dc2626'),
        ('Warnings', warnings, '#f59e0b'),
        ('Info', info, '#2563eb'),
        ('Total Faults', len(faults), '#7c3aed')
    ]

    result = []
    for title, value, color in cards:
        result.append(html.Div([
            html.Div(title, style={'fontSize': '12px', 'color': '#666', 'marginBottom': '8px'}),
            html.Div(str(value), style={'fontSize': '28px', 'fontWeight': 'bold', 'color': color})
        ], style={'padding': '18px 16px', 'backgroundColor': '#fff7ed', 'borderLeft': f'4px solid {color}', 'borderRadius': '8px'}))
    return result


@app.callback(Output('fault-table', 'children'), Input('vehicle-dropdown', 'value'), Input('date-range', 'start_date'), Input('date-range', 'end_date'))
def update_fault_table(vehicle_id, start_date, end_date):
    if vehicle_id is None:
        return html.Div('No vehicle selected')
    dfx = get_filtered_data(vehicle_id, start_date, end_date)
    faults = compute_faults(dfx)
    if faults.empty:
        return html.Div('No active faults detected in the selected time range.')

    severity_order = {'Critical': 0, 'Warning': 1, 'Info': 2}
    faults = faults.assign(__severity_rank=faults['severity'].map(severity_order)).sort_values(['timestamp', '__severity_rank'])
    rows = [
        html.Tr([
            html.Td(pd.to_datetime(row['timestamp']).strftime('%Y-%m-%d %H:%M:%S') if pd.notna(row['timestamp']) else 'N/A', style={'padding': '8px'}),
            html.Td(row['severity'], style={'padding': '8px', 'fontWeight': 'bold'}),
            html.Td(row['code'], style={'padding': '8px'}),
            html.Td(row['message'], style={'padding': '8px'})
        ]) for _, row in faults.iterrows()
    ]

    table = html.Table([
        html.Thead(html.Tr([
            html.Th('Time', style={'padding': '8px', 'backgroundColor': '#e2e8f0'}),
            html.Th('Severity', style={'padding': '8px', 'backgroundColor': '#e2e8f0'}),
            html.Th('Code', style={'padding': '8px', 'backgroundColor': '#e2e8f0'}),
            html.Th('Message', style={'padding': '8px', 'backgroundColor': '#e2e8f0'})
        ])),
        html.Tbody(rows)
    ], style={'width': '100%', 'borderCollapse': 'collapse'})
    return table


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


@app.callback(
    Output('download-report', 'data'),
    Input('export-report-btn', 'n_clicks'),
    State('vehicle-dropdown', 'value'),
    State('date-range', 'start_date'),
    State('date-range', 'end_date'),
    State('report-format', 'value'),
    prevent_initial_call=True
)
def export_report(n_clicks, vehicle_id, start_date, end_date, report_format):
    if vehicle_id is None:
        return dash.no_update
    dfx = get_filtered_data(vehicle_id, start_date, end_date)
    if dfx.empty:
        return dash.no_update

    timestamp = pd.Timestamp.today().strftime('%Y%m%d_%H%M%S')
    filename_base = f'{vehicle_id}_report_{timestamp}'

    if report_format == 'pdf':
        pdf_bytes = export_report_pdf(dfx, vehicle_id, start_date, end_date)
        return dcc.send_bytes(pdf_bytes, filename=f'{filename_base}.pdf')

    csv_buffer = StringIO()
    dfx.to_csv(csv_buffer, index=False)
    return dcc.send_string(csv_buffer.getvalue(), filename=f'{filename_base}.csv')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
