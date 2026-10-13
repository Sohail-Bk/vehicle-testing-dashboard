from io import BytesIO, StringIO

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from dash import Input, Output, State, dcc, html
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .data_utils import get_filtered_data


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


def _chart_image(fig, width=260, height=160):
    png_bytes = pio.to_image(fig, format='png', width=width * 3, height=height * 3, engine='kaleido')
    return Image(BytesIO(png_bytes), width=width, height=height)


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
    story.append(Spacer(1, 14))

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
    story.append(Paragraph('Key Trend Charts', styles['Heading2']))
    story.append(Spacer(1, 8))

    chart_specs = [
        ('Vehicle Speed', make_line_chart(dfx['timestamp'], dfx['vehicle_speed_kmh'], 'Vehicle Speed', 'km/h', '#2563eb')),
        ('Battery SOC', make_line_chart(dfx['timestamp'], dfx['battery_soc_percent'], 'Battery SOC', '%', '#9333ea')),
        ('Battery Temperature', make_line_chart(dfx['timestamp'], dfx['battery_temperature_c'], 'Battery Temperature', '°C', '#f59e0b')),
        ('Battery Current', make_line_chart(dfx['timestamp'], dfx['battery_current_a'], 'Battery Current', 'A', '#ef4444')),
    ]

    chart_rows = []
    for title, fig in chart_specs:
        if fig.data and len(fig.data[0].y) > 0:
            chart_rows.append([Paragraph(title, styles['Heading3']), _chart_image(fig, width=250, height=150)])

    if chart_rows:
        for i in range(0, len(chart_rows), 2):
            row = chart_rows[i:i+2]
            while len(row) < 2:
                row.append('')
            table = Table(row, colWidths=[150, 300])
            table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(table)
            story.append(Spacer(1, 12))

    story.append(Spacer(1, 18))
    story.append(Paragraph('Data Preview', styles['Heading2']))
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
    story.append(preview_table)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def build_report_download(vehicle_id, start_date, end_date, report_format):
    if vehicle_id is None:
        return None

    dfx = get_filtered_data(vehicle_id, start_date, end_date)
    if dfx.empty:
        return None

    timestamp = pd.Timestamp.today().strftime('%Y%m%d_%H%M%S')
    filename_base = f'{vehicle_id}_report_{timestamp}'

    if report_format == 'pdf':
        pdf_bytes = export_report_pdf(dfx, vehicle_id, start_date, end_date)
        return dcc.send_bytes(pdf_bytes, filename=f'{filename_base}.pdf')

    csv_buffer = StringIO()
    dfx.to_csv(csv_buffer, index=False)
    return dcc.send_string(csv_buffer.getvalue(), filename=f'{filename_base}.csv')
