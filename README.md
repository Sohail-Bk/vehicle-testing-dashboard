import os
import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go


df = None

def load_data():
    global df
    path = 'data/sample_vehicle_data.csv'
    if not os.path.exists(path):
        import generate_sample_data
        generate_sample_data.main()
    df = pd.read_csv(path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df


df = load_data()
vehicles = sorted(df['vehicle_id'].unique().tolist())

app = dash.Dash(__name__)
app.title = 'Vehicle Testing Dashboard'

app.layout = html.Div([
    html.Div([
        html.H1('🚗 Vehicle Testing Dashboard', style={'color': 'white', 'margin': 0}),
        html.P('EV time-series reporting and diagnostics', style={'color': '#dfefff', 'margin': '6px 0 0 0'})
    ], style={'backgroundColor': '#0f4c81', 'padding': '20px 24px', 'borderBottom': '4px solid #f59e0b'}),

    html.Div([
        html.Div([
            html.Label('Vehicle ID', style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='vehicle-dropdown',
                options=[{'label': v, 'value': v} for v in vehicles],
                value=vehicles[0],
                clearable=False,
                style={'marginTop': '6px'}
            )
        ], style={'flex': '1', 'paddingRight': '10px'}),

        html.Div([
            html.Label('Date range', style={'fontWeight': 'bold'}),
            dcc.DatePickerRange(
                id='date-range',
                start_date=df['timestamp'].min().date(),
                end_date=df['timestamp'].max().date(),
                display_format='YYYY-MM-DD'
            )
        ], style={'flex': '1', 'paddingLeft': '10px'})
    ], style={'display': 'flex', 'padding': '20px', 'backgroundColor': '#f5f7fb'}),

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
        html.H3('Summary Table', style={'marginBottom': '10px'}),
        html.Div(id='summary-table')
    ], style={'padding': '20px'})
], style={'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#ffffff'})


def get_filtered_data(vehicle_id, start_date, end_date):
    filtered = df[df['vehicle_id'] == vehicle_id].copy()
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
        hovermode='x unified'
    )
    fig.update_xaxes(title_text='Time')
    fig.update_yaxes(title_text=yaxis_title)
    return fig


@app.callback(
    Output('kpi-cards', 'children'),
    Input('vehicle-dropdown', 'value'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date')
)
def update_kpis(vehicle_id, start_date, end_date):
    dfx = get_filtered_data(vehicle_id, start_date, end_date)
    if dfx.empty:
        return []

    kpis = [
        ('Max Speed', f"{dfx['vehicle_speed_kmh'].max():.1f} km/h", '#2563eb'),
        ('Avg Speed', f"{dfx['vehicle_speed_kmh'].mean():.1f} km/h", '#0ea5e9'),
        ('Distance', f"{dfx['odometer_km'].iloc[-1] - dfx['odometer_km'].iloc[0]:.1f} km", '#16a34a'),
        ('Final SOC', f"{dfx['battery_soc_percent'].iloc[-1]:.1f}%", '#9333ea'),
        ('Max Battery Temp', f"{dfx['battery_temperature_c'].max():.1f} °C", '#f97316'),
        ('Peak RPM', f"{dfx['e_motor_speed_rpm'].max():.0f}", '#ef4444'),
        ('Status', dfx['test_status'].mode().iloc[0], '#f59e0b'),
        ('Total Regen', f"{dfx['regenerative_braking_kw'].sum():.1f} kW", '#10b981')
    ]

    cards = []
    for title, value, color in kpis:
        cards.append(html.Div([
            html.Div(title, style={'fontSize': '13px', 'color': '#667085', 'marginBottom': '8px'}),
            html.Div(value, style={'fontSize': '28px', 'fontWeight': 'bold', 'color': color})
        ], style={'padding': '18px 16px', 'backgroundColor': '#f8fafc', 'borderLeft': f'4px solid {color}', 'borderRadius': '8px'}))
    return cards


@app.callback(Output('speed-chart', 'figure'), Input('vehicle-dropdown', 'value'), Input('date-range', 'start_date'), Input('date-range', 'end_date'))
def update_speed(vehicle_id, start_date, end_date):
    dfx = get_filtered_data(vehicle_id, start_date, end_date)
    return make_line_chart(dfx['timestamp'], dfx['vehicle_speed_kmh'], 'Vehicle Speed', 'km/h', '#2563eb')


@app.callback(Output('rpm-chart', 'figure'), Input('vehicle-dropdown', 'value'), Input('date-range', 'start_date'), Input('date-range', 'end_date'))
def update_rpm(vehicle_id, start_date, end_date):
    dfx = get_filtered_data(vehicle_id, start_date, end_date)
    return make_line_chart(dfx['timestamp'], dfx['e_motor_speed_rpm'], 'E-Motor Speed', 'RPM', '#f97316')


@app.callback(Output('battery-voltage-chart', 'figure'), Input('vehicle-dropdown', 'value'), Input('date-range', 'start_date'), Input('date-range', 'end_date'))
def update_voltage(vehicle_id, start_date, end_date):
    dfx = get_filtered_data(vehicle_id, start_date, end_date)
    return make_line_chart(dfx['timestamp'], dfx['battery_voltage_v'], 'Battery Voltage', 'V', '#16a34a')


@app.callback(Output('battery-current-chart', 'figure'), Input('vehicle-dropdown', 'value'), Input('date-range', 'start_date'), Input('date-range', 'end_date'))
def update_current(vehicle_id, start_date, end_date):
    dfx = get_filtered_data(vehicle_id, start_date, end_date)
    return make_line_chart(dfx['timestamp'], dfx['battery_current_a'], 'Battery Current', 'A', '#ef4444')


@app.callback(Output('soc-chart', 'figure'), Input('vehicle-dropdown', 'value'), Input('date-range', 'start_date'), Input('date-range', 'end_date'))
def update_soc(vehicle_id, start_date, end_date):
    dfx = get_filtered_data(vehicle_id, start_date, end_date)
    return make_line_chart(dfx['timestamp'], dfx['battery_soc_percent'], 'Battery SOC', '%', '#9333ea')


@app.callback(Output('battery-temp-chart', 'figure'), Input('vehicle-dropdown', 'value'), Input('date-range', 'start_date'), Input('date-range', 'end_date'))
def update_battery_temp(vehicle_id, start_date, end_date):
    dfx = get_filtered_data(vehicle_id, start_date, end_date)
    return make_line_chart(dfx['timestamp'], dfx['battery_temperature_c'], 'Battery Temperature', '°C', '#f59e0b')


@app.callback(Output('motor-temp-chart', 'figure'), Input('vehicle-dropdown', 'value'), Input('date-range', 'start_date'), Input('date-range', 'end_date'))
def update_motor_temp(vehicle_id, start_date, end_date):
    dfx = get_filtered_data(vehicle_id, start_date, end_date)
    return make_line_chart(dfx['timestamp'], dfx['motor_temperature_c'], 'Motor Temperature', '°C', '#ec4899')


@app.callback(Output('regen-chart', 'figure'), Input('vehicle-dropdown', 'value'), Input('date-range', 'start_date'), Input('date-range', 'end_date'))
def update_regen(vehicle_id, start_date, end_date):
    dfx = get_filtered_data(vehicle_id, start_date, end_date)
    return make_line_chart(dfx['timestamp'], dfx['regenerative_braking_kw'], 'Regenerative Braking', 'kW', '#10b981')


@app.callback(Output('coolant-chart', 'figure'), Input('vehicle-dropdown', 'value'), Input('date-range', 'start_date'), Input('date-range', 'end_date'))
def update_coolant(vehicle_id, start_date, end_date):
    dfx = get_filtered_data(vehicle_id, start_date, end_date)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dfx['timestamp'], y=dfx['coolant_temperature_c'], mode='lines', name='Coolant', line={'color': '#0ea5e9'}))
    fig.add_trace(go.Scatter(x=dfx['timestamp'], y=dfx['inverter_temperature_c'], mode='lines', name='Inverter', line={'color': '#f97316'}))
    fig.update_layout(title='Coolant vs Inverter Temperature', template='plotly_white', height=300, hovermode='x unified')
    fig.update_xaxes(title_text='Time')
    fig.update_yaxes(title_text='°C')
    return fig


@app.callback(Output('throttle-chart', 'figure'), Input('vehicle-dropdown', 'value'), Input('date-range', 'start_date'), Input('date-range', 'end_date'))
def update_throttle(vehicle_id, start_date, end_date):
    dfx = get_filtered_data(vehicle_id, start_date, end_date)
    return make_line_chart(dfx['timestamp'], dfx['throttle_position_pct'], 'Throttle Position', '%', '#6366f1')


@app.callback(Output('summary-table', 'children'), Input('vehicle-dropdown', 'value'), Input('date-range', 'start_date'), Input('date-range', 'end_date'))
def update_summary_table(vehicle_id, start_date, end_date):
    dfx = get_filtered_data(vehicle_id, start_date, end_date)
    if dfx.empty:
        return html.Div('No data available')

    summary_data = [
        ('Vehicle Speed (km/h)', dfx['vehicle_speed_kmh'].min(), dfx['vehicle_speed_kmh'].mean(), dfx['vehicle_speed_kmh'].max()),
        ('E-Motor Speed (RPM)', dfx['e_motor_speed_rpm'].min(), dfx['e_motor_speed_rpm'].mean(), dfx['e_motor_speed_rpm'].max()),
        ('Battery Voltage (V)', dfx['battery_voltage_v'].min(), dfx['battery_voltage_v'].mean(), dfx['battery_voltage_v'].max()),
        ('Battery Current (A)', dfx['battery_current_a'].min(), dfx['battery_current_a'].mean(), dfx['battery_current_a'].max()),
        ('Battery Temp (°C)', dfx['battery_temperature_c'].min(), dfx['battery_temperature_c'].mean(), dfx['battery_temperature_c'].max()),
        ('Motor Temp (°C)', dfx['motor_temperature_c'].min(), dfx['motor_temperature_c'].mean(), dfx['motor_temperature_c'].max()),
        ('SOC (%)', dfx['battery_soc_percent'].min(), dfx['battery_soc_percent'].mean(), dfx['battery_soc_percent'].max()),
        ('Odometer (km)', dfx['odometer_km'].min(), dfx['odometer_km'].mean(), dfx['odometer_km'].max()),
        ('Throttle (%)', dfx['throttle_position_pct'].min(), dfx['throttle_position_pct'].mean(), dfx['throttle_position_pct'].max()),
        ('Tire Pressure (psi)', dfx['tire_pressure_psi'].min(), dfx['tire_pressure_psi'].mean(), dfx['tire_pressure_psi'].max())
    ]

    table = html.Table([
        html.Thead(html.Tr([
            html.Th('Metric', style={'padding': '8px', 'backgroundColor': '#e2e8f0'}),
            html.Th('Min', style={'padding': '8px', 'backgroundColor': '#e2e8f0'}),
            html.Th('Average', style={'padding': '8px', 'backgroundColor': '#e2e8f0'}),
            html.Th('Max', style={'padding': '8px', 'backgroundColor': '#e2e8f0'})
        ])),
        html.Tbody([
            html.Tr([
                html.Td(row[0], style={'padding': '8px', 'borderBottom': '1px solid #e2e8f0'}),
                html.Td(f'{row[1]:.2f}', style={'padding': '8px', 'borderBottom': '1px solid #e2e8f0'}),
                html.Td(f'{row[2]:.2f}', style={'padding': '8px', 'borderBottom': '1px solid #e2e8f0'}),
                html.Td(f'{row[3]:.2f}', style={'padding': '8px', 'borderBottom': '1px solid #e2e8f0'})
            ]) for row in summary_data
        ])
    ], style={'width': '100%', 'borderCollapse': 'collapse'})
    return table


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
