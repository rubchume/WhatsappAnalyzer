import dash
import dash_core_components as dcc
import dash_html_components as html

from django_plotly_dash import DjangoDash


def create_app_layout(plotly_figure=None):
    return html.Div(
        [
            dcc.Graph(figure=plotly_figure),
        ],
        id="network-graph"
    )


def create_app(plotly_figure=None):
    app = DjangoDash('NetworkGraphInline')
    app.layout = create_app_layout(plotly_figure)
    return app


app = DjangoDash('NetworkGraph')
app.layout = create_app_layout()
