import unittest
import os
import json
from datetime import datetime, timezone
import utils.json_helper_functions as jhf


class TestsJsonHelperFunctions(unittest.TestCase):
  def setUp(self):
    base_path = os.path.join(os.path.dirname(__file__), 'dt_feed_example')
    self.file_path = os.path.join(base_path, "data", "objects", "0", "0a",
                                  "49-0a1a7c7e-b2b1-3bb8-b4a2-0be8c160333a.json")

  def test_parse_poi(self):
    with open(self.file_path, "r", encoding="utf-8") as file:
      content = json.load(file)
      poi = jhf.parse_poi_from_json(content)
      self.assertEqual("Le chat, la goutte d'eau et le frigo (titre provisoire)", poi.name)
      self.assertEqual("49400", poi.postal_code)
      self.assertEqual("Saumur", poi.city.name)
      self.assertEqual("kb:49328", poi.city.id)
      self.assertEqual("Maine-et-Loire", poi.city.departement.name)
      self.assertEqual("kb:France5249", poi.city.departement.id)
      self.assertEqual("Pays de la Loire", poi.city.departement.region.name)
      self.assertEqual("kb:France52", poi.city.departement.region.id)
      self.assertEqual(4, len(poi.categories))
      self.assertEqual('CulturalEvent', poi.categories[0].name)
      self.assertEqual('EntertainmentAndEvent', poi.categories[1].name)
      self.assertEqual('PointOfInterest', poi.categories[2].name)
      self.assertEqual('ShowEvent', poi.categories[3].name)
      self.assertEqual("FMAPDL049V50HL4Q", poi.id)
      self.assertEqual(datetime(2024, 9, 25, 0, 0, 0), poi.created_at)
      self.assertEqual(
        datetime(2024, 10, 17, 3, 22, 7, 570000, tzinfo=timezone.utc),
        poi.updated_at
      )
      self.assertEqual(-0.076107, poi.longitude)
      self.assertEqual(47.260621, poi.latitude)

  def test_poi_identifier(self):
    self.assertEqual("FMAPDL049V50HL4Q", jhf.get_poi_identifier(self.file_path))

  def test_poi_name(self):
    self.assertEqual("Le chat, la goutte d'eau et le frigo (titre provisoire)", jhf.get_poi_name(self.file_path))

  def test_poi_creation_date(self):
    self.assertEqual("2024-09-25", jhf.get_poi_creation_date(self.file_path))

  def test_poi_category(self):
    self.assertEqual(['A', 'B', 'C'], jhf.category_cleanup(['schema:xyz', 'A', 'B', 'C']))
    self.assertEqual([
      'CulturalEvent',
      'EntertainmentAndEvent',
      'PointOfInterest',
      'ShowEvent'
    ], jhf.category_cleanup(jhf.get_poi_category(self.file_path))
    )

  def test_poi_region(self):
    self.assertEqual(('kb:France52', 'Pays de la Loire'), jhf.get_poi_region(self.file_path))

  def test_poi_department(self):
    self.assertEqual(('kb:France5249', 'Maine-et-Loire'), jhf.get_poi_department(self.file_path))

  def test_poi_city(self):
    self.assertEqual(('kb:49328', 'Saumur'), jhf.get_poi_city(self.file_path))

  def test_poi_coordinates(self):
    self.assertEqual((47.260621, -0.076107), jhf.get_poi_coordinates(self.file_path))


if __name__ == '__main__':
  unittest.main()
