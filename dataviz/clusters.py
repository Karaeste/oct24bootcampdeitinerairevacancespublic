from collections import defaultdict
import pandas as pd
from utils import connect_to_neo4j
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go


@callback(
  Output('clusters-category', 'options'),
  Input('reload-button', 'n_clicks'),
)
def update_dropdown(n_clicks):
  with connect_to_neo4j() as driver:
    with driver.session() as session:
      result = session.run('''
      MATCH (c:Cluster)
      WITH c.category AS category, COUNT(c) AS clusterCount
      MATCH (c)-[r:ROUTE]->(c2)
      WHERE c.category = c2.category AND c.category = category
      RETURN category, clusterCount, COUNT(r) AS routeCount
      ''')
      categories = [(r['category'], r['clusterCount'], r['routeCount']) for r in result]
      return [
        {'label': f'{category} ({clusterCount} clusters, {routeCount} routes)', 'value': category}
        for category, clusterCount, routeCount in sorted(categories)
      ]


page_layout = html.Div([
  html.H1("Clusters"),
  html.Button("Reload", id="reload-button", n_clicks=0),
  dcc.Dropdown(
    id='clusters-category',
    options=[],
    value=''
  ),
  dcc.Graph(id='clusters-map'),
])


@callback(
  Output('clusters-map', 'figure'),
  [Input('clusters-category', 'value')]
)
def update_graph_and_labels(category):
  fig = go.Figure()
  fig.update_layout(
    width=800,
    height=800,
  )
  if not category:
    fig.update_layout(
      title=f"Choose a category",
    )
    print('no category', flush=True)
    return fig
  clusters = load_clusters_from_neo4j(category)
  if len(clusters) == 0:
    fig.update_layout(
      title=f"No cluster in category {category}",
    )
    print('no clusters', flush=True)
    return fig
  routes = load_routes_from_neo4j(category)
  draw_clusters(fig, clusters)
  draw_routes(fig, routes)
  fig.update_layout(
    title=f"Clusters {category}",
    xaxis_title="Lambert X",
    yaxis_title="Lambert Y",
    showlegend=False,
  )
  return fig


def draw_clusters(fig, clusters):
  df_clusters = pd.DataFrame(clusters)
  fig.add_trace(
    go.Scatter(
      x=df_clusters["x"],
      y=df_clusters["y"],
      mode="markers",
      customdata=clusters,
      hovertemplate=(
        "<b>Cluster Info</b><br>"
        "X: %{customdata.x}<br>"
        "Y: %{customdata.y}<br>"
        "ID: %{customdata.id}<br>"
        "POIs:<br>%{customdata.pois}<br>"
        "<extra></extra>"
      ),
      marker=dict(
        size=df_clusters["radius"] / 1000,
        color=df_clusters["density"],
        colorscale="Viridis_r",
        cmin=0,
        cmax=2,
        line=dict(color="black", width=1),
      )
    )
  )


def draw_routes(fig, routes):
  edge_x = []
  edge_y = []
  for (x1, y1), (x2, y2) in routes:
    edge_x.extend([x1, x2, None])
    edge_y.extend([y1, y2, None])
  fig.add_trace(go.Scatter(
    x=edge_x,
    y=edge_y,
    mode='lines',
    line=dict(color='gray', width=2)
  ))


def load_clusters_from_neo4j(category):
  with connect_to_neo4j() as driver:
    with driver.session() as session:
      result = session.run(
        "MATCH (c:Cluster {category:$category}) RETURN c",
        category=category
      )
      clusters = [dict(r["c"].items()) for r in result]
      print('clusters', category, len(clusters), flush=True)
      result = session.run(
        """
        MATCH (c:Cluster {category:$category})-[:VICINITY]->(p:POI)
        RETURN c.id AS cluster, p.name AS name
        """,
        category=category
      )
      names = defaultdict(list)
      for r in result:
        names[r['cluster']].append(r["name"])
  for cluster in clusters:
    cluster.update({'pois': '<br>'.join(names[cluster['id']])})
  return clusters


def load_routes_from_neo4j(category):
  with connect_to_neo4j() as driver:
    with driver.session() as session:
      result = session.run(
        """
        MATCH (c1:Cluster {category:$category})-[r:ROUTE]->(c2:Cluster {category:$category})
        RETURN c1.x AS x1, c1.y AS y1, c2.x AS x2, c2.y AS y2
        """,
        category=category
      )
      routes = {tuple(sorted(((r['x1'], r['y1']), (r['x2'], r['y2'])))) for r in result}
      print('routes', category, len(routes), flush=True)
  return routes
