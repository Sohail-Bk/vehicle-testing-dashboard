from dash import dcc, html


def build_layout():
    return html.Div([
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
                html.H3('Report overview', style={'margin': '0 0 12px 0'}),
                html.Div(id='report-summary-panel', style={'padding': '12px', 'backgroundColor': '#f8fafc', 'borderRadius': '8px', 'border': '1px solid #e2e8f0'})
            ], style={'flex': '1', 'minWidth': '320px', 'padding': '0 20px 20px'}),
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
                ], style={'marginBottom': '12px'}),
                html.Button('Export current report', id='export-report-btn', n_clicks=0, style={
                    'padding': '10px 18px',
                    'backgroundColor': '#0f4c81',
                    'color': 'white',
                    'border': 'none',
                    'borderRadius': '8px',
                    'cursor': 'pointer',
                    'fontWeight': 'bold',
                    'marginRight': '10px'
                }),
                html.Button('Download PDF', id='report-view-btn', n_clicks=0, style={
                    'padding': '10px 18px',
                    'backgroundColor': '#0ea5e9',
                    'color': 'white',
                    'border': 'none',
                    'borderRadius': '8px',
                    'cursor': 'pointer',
                    'fontWeight': 'bold'
                }),
                dcc.Download(id='download-report'),
                dcc.Download(id='report-view-download')
            ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'flex-start', 'padding': '0 20px 20px', 'minWidth': '240px'})
        ], style={'display': 'flex', 'flexWrap': 'wrap', 'alignItems': 'stretch'}),

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
