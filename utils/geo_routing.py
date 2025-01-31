from typing import Dict, Tuple
import pandas as pd
import numpy as np
import networkx as nx
from scipy.sparse.csgraph import minimum_spanning_tree
from scipy.spatial.distance import pdist, squareform
from scipy.spatial import Delaunay


class GeoRouting:
  def __init__(self, nodes: pd.DataFrame, x_column: str = "x", y_column: str = "y"):
    """
    Initialise un geo-routing en calculant les arêtes formant un arbre couvrant minimal selon la distance euclienne
    :param nodes: pd.DataFrame - Les noeuds à relier
    :param x_column: str - nom de la colonne des x dans le dataframe
    :param y_column: str - nom de la colonne des y dans le dataframe
    """
    self.points = nodes[[x_column, y_column]].values
    self.count = len(nodes)
    distances = pdist(self.points, metric='euclidean')
    self.dist_matrix = squareform(distances)
    mst = minimum_spanning_tree(self.dist_matrix)
    edges = np.transpose(mst.nonzero())
    self.graph = nx.Graph()
    for u, v in edges:
      self.graph.add_edge(u, v, weight=self.dist_matrix[u, v])

  @property
  def edges(self) -> Dict[Tuple[int, int], int]:
    """
    :return: edges as a dictionary of pair of node ids to distance
    """
    return {
      (int(edge[0]), int(edge[1])): int(edge[2]['weight'])
      for edge in self.graph.edges(data=True)
    }

  def increase(
    self,
    threshold_in_meters: int = 50000,
    shortcut_factor: float = 3
  ):
    """
    Rajoute des arêtes entre les paires de noeuds
    - dont la distance est inférieure au seuil
    - dont la distance via le graphe actuel est supérieure à distance à vol d'oiseau * shortcut_factor
    :param threshold_in_meters: seuil en mètres
    :param shortcut_factor: facteur multiplicateur pour décider de rajouter un raccourci
    :return:
    """
    tri = Delaunay(self.points)
    for i, node in enumerate(self.points):
      neighbors_indices = np.unique(tri.simplices[tri.vertex_to_simplex[i]])
      neighbor_distances = self.dist_matrix[i, neighbors_indices]
      valid_neighbors = neighbors_indices[neighbor_distances <= threshold_in_meters]
      valid_distances = neighbor_distances[neighbor_distances <= threshold_in_meters]
      for neighbor, dist in zip(valid_neighbors, valid_distances):
        if neighbor == i:
          continue
        try:
          mst_distance = nx.shortest_path_length(self.graph, source=i, target=neighbor, weight='weight')
        except nx.NetworkXNoPath:
          mst_distance = float('inf')
        if dist * shortcut_factor > mst_distance:
          continue
        if not self.graph.has_edge(i, neighbor):
          self.graph.add_edge(i, neighbor, weight=dist)
