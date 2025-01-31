import os
from dataclasses import dataclass
import pandas as pd
from airflow.decorators import task, task_group
from parts.helpers import inject_vars_into_env
from utils import connect_to_db_from_env, select_pois_from_db, GeoClustering, GeoRouting, connect_to_neo4j, \
  import_clusters, import_routes


@dataclass
class ClusterDefinition:
  category: str
  min_cluster_size: int
  expand_threshold: int
  edge_threshold: int
  shortcut_factor: int


cluster_definitions = [
  ClusterDefinition(
    category='CulturalSite', min_cluster_size=5, expand_threshold=15000, edge_threshold=50000, shortcut_factor=3
  ),
  ClusterDefinition(
    category='CulturalEvent', min_cluster_size=5, expand_threshold=15000, edge_threshold=50000, shortcut_factor=3
  ),
  # ClusterDefinition(
  #   category='SportsAndLeisurePlace', min_cluster_size=10, expand_threshold=15000, edge_threshold=50000, shortcut_factor=3
  # ),
  # ClusterDefinition(
  #   category='EntertainmentAndEvent', min_cluster_size=10, expand_threshold=15000, edge_threshold=50000, shortcut_factor=3
  # ),
  # ClusterDefinition(
  #   category='WalkingTour', min_cluster_size=5, expand_threshold=15000, edge_threshold=50000, shortcut_factor=3
  # ),
  ClusterDefinition(
    category='SportsEvent', min_cluster_size=5, expand_threshold=15000, edge_threshold=50000, shortcut_factor=3
  ),
  ClusterDefinition(
    category='Museum', min_cluster_size=3, expand_threshold=15000, edge_threshold=150000, shortcut_factor=3
  ),
  ClusterDefinition(
    category='ThemePark', min_cluster_size=2, expand_threshold=5000, edge_threshold=150000, shortcut_factor=3
  ),
  ClusterDefinition(
    category='NaturalHeritage', min_cluster_size=2, expand_threshold=5000, edge_threshold=150000, shortcut_factor=3
  ),
  ClusterDefinition(
    category='TechnicalHeritage', min_cluster_size=2, expand_threshold=5000, edge_threshold=150000, shortcut_factor=3
  ),
  ClusterDefinition(
    category='RemembranceSite', min_cluster_size=2, expand_threshold=5000, edge_threshold=150000, shortcut_factor=3
  ),
  ClusterDefinition(
    category='Church', min_cluster_size=2, expand_threshold=5000, edge_threshold=150000, shortcut_factor=3
  ),
  ClusterDefinition(
    category='Castle', min_cluster_size=2, expand_threshold=5000, edge_threshold=150000, shortcut_factor=3
  ),
]


@task(pool="clusters_pool")
@inject_vars_into_env(
  'POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DATATOURISME_DB',
  'NEO4J_USER', 'NEO4J_PASSWORD', 'NEO4J_URL'
)
def create_cluster(definition: ClusterDefinition):
  os.environ['POSTGRES_DB'] = os.environ['POSTGRES_DATATOURISME_DB']
  with connect_to_db_from_env() as pg_conn:
    pois = select_pois_from_db(pg_conn, definition.category)
    print(f'Extracted {len(pois)} POIs for category {definition.category}')
    pois_data = [{'id': poi.id, 'lat': poi.latitude, 'lon': poi.longitude} for poi in pois]
    df_pois = pd.DataFrame(pois_data)
    clustering = GeoClustering(df_pois)
    clustering.create_clusters(min_cluster_size=definition.min_cluster_size)
    clustering.increase_clusters(threshold_in_meters=definition.expand_threshold)
    clustering.transform_unclustered_into_clusters()
    df_clusters = clustering.clusters
    df_vicinities = clustering.pois
    print(f'Computed {len(df_clusters)} clusters for category {definition.category}')
    routing = GeoRouting(df_clusters)
    routing.increase(threshold_in_meters=definition.edge_threshold, shortcut_factor=definition.shortcut_factor)
    routes = routing.edges
    print(f'Computed {len(routes)} routes between clusters for category {definition.category}')
    with connect_to_neo4j() as n4j_conn:
      print(f'Starting import of clusters and routes into neo4j')
      import_clusters(n4j_conn, definition.category, df_clusters, df_vicinities)
      print(f'Import of clusters into neo4j is complete')
      import_routes(n4j_conn, definition.category, routes)
      print(f'Import of routes into neo4j is complete')


@task_group(group_id="clusters_creation")
def create_cluster_tasks():
  return [
    create_cluster.override(task_id=f'create_cluster_{definition.category}')(definition)
    for definition in cluster_definitions
  ]
