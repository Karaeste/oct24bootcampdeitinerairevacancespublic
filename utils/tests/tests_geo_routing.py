import unittest
import os
import pandas as pd
from utils.geo_clustering import GeoClustering
from utils.geo_routing import GeoRouting


class TestsGeoRouting(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    pois = pd.read_csv(os.path.join(os.path.dirname(__file__), 'poi_lat_lon.csv'), sep=',')
    clustering = GeoClustering(pois)
    clustering.create_clusters()
    clustering.increase_clusters(5000)
    cls.df = clustering.clusters

  def setUp(self):
    self.routing = GeoRouting(self.df)

  def test_all_nodes_are_connected(self):
    all_nodes = set(self.df.index)
    routed_nodes = {node for edge in self.routing.edges for node in edge}
    self.assertEqual(len(all_nodes), len(routed_nodes))

  def test_all_routes_have_distances(self):
    for distance in self.routing.edges.values():
      self.assertGreater(distance, 0)

  def test_routes_are_increased(self):
    self.assertEqual(42, len(self.routing.edges))
    self.routing.increase(50000, 3)
    self.assertEqual(47, len(self.routing.edges))
    self.test_all_nodes_are_connected()
    self.test_all_routes_have_distances()


if __name__ == '__main__':
  unittest.main()
