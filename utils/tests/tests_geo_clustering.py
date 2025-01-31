import math
import os
import unittest
import pandas as pd
from utils.geo_clustering import GeoClustering, compute_xy


class TestsGeoClustering(unittest.TestCase):
  def setUp(self):
    pois = pd.read_csv(os.path.join(os.path.dirname(__file__), 'poi_lat_lon.csv'), sep=',')
    self.clustering = GeoClustering(pois)

  def test_wrong_lat_lon_do_not_fail(self):
    self.assertEqual((math.nan, math.nan), compute_xy(1059.0, 199.0))

  def test_x_y_are_computed(self):
    self.assertEqual('x', self.clustering.pois.columns[4])
    self.assertEqual('y', self.clustering.pois.columns[5])
    row0 = self.clustering.pois.iloc[0]
    self.assertEqual(623323, row0[['x']].item())
    self.assertEqual(6257326, row0[['y']].item())

  def test_no_clusters_by_default(self):
    self.assertEqual(0, len(self.clustering.clusters))

  def test_clusters_are_computed(self):
    self.clustering.create_clusters()
    self.assertEqual('cluster', self.clustering.pois.columns[6])
    row0 = self.clustering.pois.iloc[0]
    self.assertEqual(8, row0[['cluster']].item())

  def test_clusters_details_are_computed(self):
    self.clustering.create_clusters()
    clusters = self.clustering.clusters
    self.assertEqual(43, len(clusters))
    cluster0 = clusters.iloc[0]
    self.assertEqual(666183, cluster0[['x']].item())
    self.assertEqual(6209297, cluster0[['y']].item())
    self.assertEqual(8853, cluster0[['radius']].item())
    self.assertEqual(17, cluster0[['count']].item())
    self.assertEqual(2168, int(10000 * cluster0[['density']].item()))

  def test_clusters_are_increased(self):
    self.clustering.create_clusters()
    self.assertEqual(619, len(self.clustering.unclustered_pois))
    self.clustering.increase_clusters(5000)
    self.assertEqual(344, len(self.clustering.unclustered_pois))

  def test_all_as_clusters(self):
    self.clustering.create_clusters()
    self.assertEqual(43, len(self.clustering.clusters))
    self.assertEqual(619, len(self.clustering.unclustered_pois))
    self.clustering.transform_unclustered_into_clusters()
    self.assertEqual(662, len(self.clustering.clusters))
    self.assertEqual(0, len(self.clustering.unclustered_pois))


if __name__ == '__main__':
  unittest.main()
