from typing import Tuple, Dict, List
import os
import re
import neo4j as neo4j
import pandas as pd
from pyproj import Transformer
from .point_of_interest_helper import Poi


def connect_to_neo4j() -> neo4j.Driver:
  """
  Connexion à Neo4j
  :return: driver : driver de connexion à Neo4j
  """
  return neo4j.GraphDatabase.driver(
    os.environ['NEO4J_URL'],
    auth=(os.environ['NEO4J_USER'], os.environ['NEO4J_PASSWORD'])
  )


# EPSG:9794 est le code EPSG pour la projection "RGF93 v2b / Lambert-93" utilisée en France
# cf https://fr.wikipedia.org/wiki/Projection_conique_conforme_de_Lambert#Lambert_93
transformer = Transformer.from_crs("EPSG:4326", "EPSG:9794", always_xy=True)


def _encode_poi(poi: Poi) -> dict | None:
  try:
    x, y = transformer.transform(poi.longitude, poi.latitude)
    return {'id': poi.id, 'name': poi.name, 'x': int(x), 'y': int(y)}
  except OverflowError:
    return None


def import_pois(driver: neo4j.Driver, pois: List[Poi]):
  '''
  Importe une liste de POIS dans neo4j
  Si le POI n'existe pas, il est créé. S'il existe déjà avec le même identifiant, il est modifié.
  Les coordonnées x,y de chaque POI sont calculées et importées à partir des latitude et longitude

  :param driver:
  :param pois: Les POIs à importer
  :return:
  '''
  with driver.session() as session:
    try:
      session.run("CREATE INDEX IF NOT EXISTS FOR (poi:POI) ON (poi.id)")
    except Exception as e:
      print('Ignoring Exception', e)
    session.run("""
            UNWIND $pois AS poi
            MERGE (p:POI {id: poi.id})
            SET p = poi
        """, pois=[d for poi in pois if (d := _encode_poi(poi)) is not None])


def _sanitize(text: str) -> str:
  """
  Sanitize to prevent injection.
  """
  if re.match(r"^[A-Za-z0-9_]+$", text):
    return text
  raise ValueError("Invalid text: must be alphanumeric and underscores only.")


def import_clusters(driver: neo4j.Driver, category: str, df_clusters: pd.DataFrame, df_vicinities: pd.DataFrame):
  """
  Importe un DataFrame de clusters dans neo4j et connecte chaque cluster à ses POIs
  Tous les clusters de la catégorie concernée sont effacés avant l'import.

  :param driver:
  :param category: La catégorie associé à tous les clusters importés
  :param df_clusters: Le dataframe des clusters
  :param df_vicinities: Les rattachements cluster-POI
  :return:
  """
  category = _sanitize(category)
  clusters = [
    {
      "id": index, "x": row["x"], "y": row["y"], "category": category,
      "radius": row["radius"], "count": row["count"], "density": row["density"]
    }
    for index, row in df_clusters.iterrows()
  ]
  vicinities = df_vicinities.to_dict(orient="records")
  with driver.session() as session:
    try:
      session.run("CREATE INDEX IF NOT EXISTS FOR (cluster:Cluster) ON (cluster.category)")
    except Exception as e:
      print('Ignoring Exception', e)
    session.run("MATCH (cluster:Cluster {category: $category}) DETACH DELETE cluster", category=category)
    session.run("UNWIND $clusters AS cluster CREATE (c:Cluster) SET c = cluster", clusters=clusters)
    session.run("""
        UNWIND $vicinities AS v
        MATCH (c:Cluster {id: v.cluster, category: $category}), (p:POI {id: v.id})
        CREATE (c)-[:VICINITY]->(p)
    """, vicinities=vicinities, category=category)


def import_routes(driver: neo4j.Driver, category: str, routes: Dict[Tuple[int, int], int]):
  """
  Importe des routes entre les clusters
  :param driver:
  :param category: La catégorie associé à tous les clusters reliés
  :param routes: dictionnaire des distances pour chaque route entre 2 clusters
  :return:
  """
  with driver.session() as session:
    session.run("""
        UNWIND $routes AS r
        MATCH (c1:Cluster {id: r.a, category: $category}), (c2:Cluster {id: r.b, category: $category})
        CREATE (c1)-[:ROUTE {distance: r.distance}]->(c2)
        CREATE (c2)-[:ROUTE {distance: r.distance}]->(c1)
    """, category=category, routes=[
      {"a": a, "b": b, "distance": distance}
      for ((a, b), distance) in routes.items()
    ])
