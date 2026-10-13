import dash

from .callbacks import register_callbacks
from .layout import build_layout

app = dash.Dash(__name__)
app.title = 'EV Vehicle Testing Dashboard'
app.layout = build_layout()
register_callbacks(app)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
