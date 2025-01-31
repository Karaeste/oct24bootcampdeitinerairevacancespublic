import os
import unittest
import json
import pandas as pd
from testcontainers.neo4j import Neo4jContainer
import utils.neo4j_helper as nh
import utils.json_helper_functions as jhf


class TestNeo4jIntegration(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    user = "neo4j"
    password = "password"
    cls.neo4j_container = Neo4jContainer("neo4j:5")
    cls.neo4j_container.with_env("NEO4J_AUTH", f"{user}/{password}")
    cls.neo4j_container.start()
    os.environ["NEO4J_URL"] = cls.neo4j_container.get_connection_url()
    os.environ["NEO4J_USER"] = user
    os.environ["NEO4J_PASSWORD"] = password
    cls.driver = nh.connect_to_neo4j()

  @classmethod
  def tearDownClass(cls):
    cls.driver.close()
    cls.neo4j_container.stop()

  def test_neo4j_connection(self):
    with self.driver.session() as session:
      session.run("CREATE (a:Greeting {message: 'Hello, World'}) RETURN a")
      result = session.run("MATCH (a:Greeting) RETURN a.message AS message")
      record = result.single()
      self.assertEqual(record["message"], "Hello, World")

  def test_import_pois(self):
    nh.import_pois(self.driver, [
      self._create_poi('1/17/33-17098a45-4a4d-31c3-a9ad-37991f14d5e0.json'),
      self._create_poi('3/31/33-3106eeed-0b75-3acf-a5a9-6fb1a59a8cfe.json')
    ])
    with self.driver.session() as session:
      self.assertEqual(
        {'id': 'FMAMID031V50XVYF', 'name': 'MEURTRE AUX JACOBINS', 'x': 574007, 'y': 6279539},
        session.run("MATCH (poi:POI) WHERE poi.id='FMAMID031V50XVYF' RETURN poi").single().data()['poi']
      )
      self.assertEqual(
        {'id': 'FMAMID031V50RLX8', 'name': 'MARCHE DE NOEL PLACE DU CAPITOLE', 'x': 574298, 'y': 6279554},
        session.run("MATCH (poi:POI) WHERE poi.id='FMAMID031V50RLX8' RETURN poi").single().data()['poi']
      )

  def test_update_pois(self):
    poi = self._create_poi('1/17/33-17098a45-4a4d-31c3-a9ad-37991f14d5e0.json')
    nh.import_pois(self.driver, [
      poi,
      self._create_poi('3/31/33-3106eeed-0b75-3acf-a5a9-6fb1a59a8cfe.json')
    ])
    poi.name = 'MEURTRE AU COUVENT DES JACOBINS'
    poi.latitude = 43.603
    nh.import_pois(self.driver, [
      poi,
      self._create_poi('4/42/41-42ea9b5e-3fbf-3f57-8e31-0bc91ae4c0ec.json')
    ])
    with self.driver.session() as session:
      self.assertEqual(
        {'id': 'FMAMID031V50XVYF', 'name': 'MEURTRE AU COUVENT DES JACOBINS', 'x': 574005, 'y': 6279460},
        session.run("MATCH (poi:POI) WHERE poi.id='FMAMID031V50XVYF' RETURN poi").single().data()['poi']
      )
      self.assertEqual(
        {'id': 'FMAMID031V50RLX8', 'name': 'MARCHE DE NOEL PLACE DU CAPITOLE', 'x': 574298, 'y': 6279554},
        session.run("MATCH (poi:POI) WHERE poi.id='FMAMID031V50RLX8' RETURN poi").single().data()['poi']
      )
      self.assertEqual(
        {'id': 'PCULAR0110000002', 'name': 'CHÂTEAU ET REMPARTS DE LA CITÉ DE CARCASSONNE',
         'x': 648209, 'y': 6234412},
        session.run("MATCH (poi:POI) WHERE poi.id='PCULAR0110000002' RETURN poi").single().data()['poi']
      )

  def test_import_clusters_from_dataframe(self):
    nh.import_pois(self.driver, [
      self._create_poi('1/17/33-17098a45-4a4d-31c3-a9ad-37991f14d5e0.json'),
      self._create_poi('3/31/33-3106eeed-0b75-3acf-a5a9-6fb1a59a8cfe.json'),
      self._create_poi('4/42/41-42ea9b5e-3fbf-3f57-8e31-0bc91ae4c0ec.json')
    ])
    self.util_import_clusters()
    with self.driver.session() as session:
      self.assertEqual([
        {
          'id': 0, 'x': 1000, 'y': 666, 'category': 'Culture',
          'radius': 5666, 'count': 6, 'density': 2,
        }, {
          'id': 1, 'x': 2000, 'y': 777, 'category': 'Culture',
          'radius': 9777, 'count': 17, 'density': 5,
        }
      ], [
        record.data()['c'] for record
        in session.run("MATCH (c:Cluster) WHERE c.category='Culture' RETURN c ORDER BY c.id").fetch(2)
      ])
      self.assertEqual([
        {'id': 'FMAMID031V50XVYF', 'name': 'MEURTRE AUX JACOBINS', 'x': 574007, 'y': 6279539},
        {'id': 'PCULAR0110000002', 'name': 'CHÂTEAU ET REMPARTS DE LA CITÉ DE CARCASSONNE',
         'x': 648209, 'y': 6234412},
      ], [
        record.data()['p'] for record
        in session.run("MATCH (c:Cluster)-[v:VICINITY]-(p:POI) WHERE c.id=1 RETURN p ORDER BY p.id").fetch(2)
      ])

  def test_import_routes(self):
    nh.import_pois(self.driver, [
      self._create_poi('1/17/33-17098a45-4a4d-31c3-a9ad-37991f14d5e0.json'),
      self._create_poi('3/31/33-3106eeed-0b75-3acf-a5a9-6fb1a59a8cfe.json'),
      self._create_poi('4/42/41-42ea9b5e-3fbf-3f57-8e31-0bc91ae4c0ec.json')
    ])
    self.util_import_clusters()
    nh.import_routes(
      self.driver, "Culture", {
        (0, 1): 954
      }
    )
    with self.driver.session() as session:
      self.assertEqual([{'c.id': 0, 'r.distance': 954}, {'c.id': 1, 'r.distance': 954}], [
        record.data() for record
        in session.run("MATCH (c:Cluster)-[r:ROUTE]->(:Cluster) RETURN c.id, r.distance ORDER BY c.id").fetch(5)
      ])

  @staticmethod
  def _create_poi(path):
    base_path = os.path.join(os.path.dirname(__file__), 'dt_feed_example')
    file_path = os.path.join(base_path, "data", "objects", path)
    with open(file_path, 'r') as file:
      json_data = json.load(file)
      return jhf.parse_poi_from_json(json_data)

  def util_import_clusters(self):
    nh.import_clusters(
      self.driver, "Culture",
      pd.DataFrame(index=[0, 1], data={
        'x': [1000, 2000],
        'y': [666, 777],
        'radius': [5666, 9777],
        'count': [6, 17],
        'density': [2, 5],
      }), pd.DataFrame({
        'id': ['FMAMID031V50XVYF', 'FMAMID031V50RLX8', 'PCULAR0110000002'],
        'cluster': [1, 0, 1],
      })
    )


if __name__ == "__main__":
  unittest.main()
