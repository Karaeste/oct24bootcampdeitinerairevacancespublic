import unittest
import os
import utils.database_helper as dh


class TestsJsonHelperFunctions(unittest.TestCase):
  def setUp(self):
    base_path = os.path.join(os.path.dirname(__file__), 'dt_feed_example')
    index_path = os.path.join(base_path, 'data', 'index.json')
    self.parsed_index = dh.parse_index_datatourisme(index_path)
    self.urls = [os.path.join(base_path, path) for path in self.parsed_index]

  def test_parse_index_datatourisme(self):
    self.assertEqual([
      'data/objects/0/0a/49-0a1a7c7e-b2b1-3bb8-b4a2-0be8c160333a.json',
      'data/objects/1/17/33-17098a45-4a4d-31c3-a9ad-37991f14d5e0.json',
      'data/objects/3/31/33-3106eeed-0b75-3acf-a5a9-6fb1a59a8cfe.json',
      'data/objects/4/42/41-42ea9b5e-3fbf-3f57-8e31-0bc91ae4c0ec.json',
      'data/objects/c/ca/33-ca746a35-db9a-3b3b-ae1c-d42aec8dbc6a.json'
    ], self.parsed_index)

  def test_collect_region_information_from_files(self):
    self.assertEqual({
      'dt_region_id': {
        0: 'kb:France52',
        1: 'kb:France76',
        2: 'kb:France76',
        3: 'kb:France76',
        4: 'kb:France76'
      },
      'name': {
        0: 'Pays de la Loire',
        1: 'Occitanie',
        2: 'Occitanie',
        3: 'Occitanie',
        4: 'Occitanie'
      }
    },
      dh.collect_region_information_from_files(self.urls).to_dict()
    )

  def test_collect_department_information_from_files(self):
    self.assertEqual({
      'dt_departement_id': {0: 'kb:France5249',
                            1: 'kb:France7631',
                            2: 'kb:France7631',
                            3: 'kb:France7611',
                            4: 'kb:France7631'},
      'dt_region_id': {0: 'kb:France52',
                       1: 'kb:France76',
                       2: 'kb:France76',
                       3: 'kb:France76',
                       4: 'kb:France76'},
      'name': {0: 'Maine-et-Loire',
               1: 'Haute-Garonne',
               2: 'Haute-Garonne',
               3: 'Aude',
               4: 'Haute-Garonne'}
    },
      dh.collect_department_information_from_files(self.urls).to_dict()
    )

  def test_collect_city_information_from_files(self):
    self.assertEqual({
      'dt_city_id': {
        0: 'kb:49328',
        1: 'kb:31555',
        3: 'kb:11069'
      },
      'dt_departement_id': {
        0: 'kb:France5249',
        1: 'kb:France7631',
        3: 'kb:France7611'
      },
      'name': {
        0: 'Saumur',
        1: 'Toulouse',
        3: 'Carcassonne'
      },
    },
      dh.collect_city_information_from_files(self.urls).to_dict()
    )

    if __name__ == '__main__':
      unittest.main()
