import dash
from dash import dcc, html, Input, Output, callback
import clusters

pages = {
  "/clusters": clusters.page_layout
}

title = "Itinéraires de vacances - DataViz"

dash_app = dash.Dash(__name__, suppress_callback_exceptions=True)
dash_app.title = title
server = dash_app.server

dash_app.layout = html.Div([
  dcc.Location(id='url', refresh=False),
  html.Div(id='page-content')
])

main_page_layout = html.Div([
  html.H1(title),
  html.A("Clusters", href="/clusters", style={'fontSize': 24, 'color': 'blue', 'textDecoration': 'underline'})
])


@callback(
  Output('page-content', 'children'),
  [Input('url', 'pathname')]
)
def display_page(pathname):
  return pages.get(pathname, main_page_layout)


if __name__ == '__main__':
    dash_app.run_server(host='0.0.0.0', port=8050, debug=True)

