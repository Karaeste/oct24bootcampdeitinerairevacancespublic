import os
import unittest
import json
from testcontainers.postgres import PostgresContainer
import utils.database_helper as dh
import utils.json_helper_functions as jhf


class TestDatabase(unittest.TestCase):

  def setUp(self):
    self.postgres_container = PostgresContainer("postgres:latest")
    self.postgres_container.start()
    os.environ["POSTGRES_USER"] = self.postgres_container.username
    os.environ["POSTGRES_PASSWORD"] = self.postgres_container.password
    os.environ["POSTGRES_DB"] = self.postgres_container.dbname
    os.environ["POSTGRES_PORT"] = self.postgres_container.get_exposed_port(5432)
    os.environ["POSTGRES_HOST"] = self.postgres_container.get_container_host_ip()
    self.engine = dh.connect_to_db_from_env()

  def tearDown(self):
    self.postgres_container.stop()

  def test_database_connection(self):
    with self.engine.cursor() as cursor:
      cursor.execute("SELECT 1, 2, 3")
      results = cursor.fetchall()
      self.assertEqual([(1, 2, 3)], results)

  def test_get_pois(self):
    self._initialize_db()
    pois = dh.get_all_pois_from_db(self.engine)
    self.assertEqual(3, len(pois))
    self.assertEqual("Le chat, la goutte d'eau et le frigo (titre provisoire)", pois[0].name)
    self.assertEqual('MEURTRE AUX JACOBINS', pois[1].name)
    self.assertEqual('MARCHE DE NOEL PLACE DU CAPITOLE', pois[2].name)

  def test_select_pois_for_category(self):
    self._initialize_db()
    pois = dh.select_pois_from_db(self.engine, 'CulturalEvent')
    self.assertEqual(2, len(pois))
    self.assertEqual("Le chat, la goutte d'eau et le frigo (titre provisoire)", pois[0].name)
    self.assertEqual('MARCHE DE NOEL PLACE DU CAPITOLE', pois[1].name)

  def _initialize_db(self):
    init_script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database_create.sql')
    with open(init_script_path, 'r') as file:
      init_script = file.read()
      with self.engine.cursor() as cursor:
        cursor.execute(init_script)
        self.engine.commit()
    pois = [self._poi1, self._poi2, self._poi3]
    for poi in pois:
      dh.add_poi_to_db(self.engine, poi)

  @property
  def _poi1(self):
    return self._create_poi('0/0a/49-0a1a7c7e-b2b1-3bb8-b4a2-0be8c160333a.json')

  @property
  def _poi2(self):
    return self._create_poi('1/17/33-17098a45-4a4d-31c3-a9ad-37991f14d5e0.json')

  @property
  def _poi3(self):
    return self._create_poi('3/31/33-3106eeed-0b75-3acf-a5a9-6fb1a59a8cfe.json')

  def _create_poi(self, path):
    base_path = os.path.join(os.path.dirname(__file__), 'dt_feed_example')
    file_path = os.path.join(base_path, "data", "objects", path)
    with open(file_path, 'r') as file:
      json_data = json.load(file)
      return jhf.parse_poi_from_json(json_data)


if __name__ == '__main__':
  unittest.main()
