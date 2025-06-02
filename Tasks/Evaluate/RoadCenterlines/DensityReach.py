import os, json, random, copy, math
from shapely.geometry import Point, Polygon, LineString
from shapely.ops import unary_union
import shapely
import matplotlib.pyplot as plt
import geopandas as gpd

from Utilities.Visualize import *
from Utilities.Utilities import *


import networkx as nx

def find_nearest_node(G, point):

    min_distance = float('inf')
    nearest_node = None
    
    for k,node in enumerate(G.nodes()):
        # Calculate Euclidean distance from the point to the node
        node_coords = np.array(node)
        distance = np.linalg.norm(node_coords - np.array([point.x,point.y]))
        
        if distance < min_distance:
            min_distance = distance
            nearest_node = k

    return nearest_node

def get_edge_indices_for_shortest_path(G, node1, node2):
    """
    Finds the shortest path between two nodes and returns the edge indices for that path.

    Parameters:
        G (networkx.Graph): The graph containing nodes and edges.
        node1 (tuple): The first node (start).
        node2 (tuple): The second node (end).

    Returns:
        edge_indices (list): A list of edge indices forming the shortest path between node1 and node2.
    """
    # Find the shortest path (list of nodes) between node1 and node2
    shortest_path = nx.shortest_path(G, source=list(G.nodes())[node1], target=list(G.nodes())[node2], weight="weight")

    # Get edge indices for the edges in the shortest path
    edge_indices = []
    
    # Loop through the nodes in the shortest path and get the corresponding edge index
    for i in range(len(shortest_path) - 1):
        edge = (shortest_path[i], shortest_path[i + 1])
        
        # Find the index of the edge
        edge_index = list(G.edges()).index(edge)
        edge_indices.append(edge_index)
    
    return edge_indices

def main(UDS):

    for i in range(len(UDS['Features']['RoadCenterlines'])):
        UDS['Features']['RoadCenterlines'][i]['properties']['DensityReach'] = 0

    G = geojson_lines_to_graph(UDS['Features']['RoadCenterlines'])
    target_indicies = [26,25,0,41,48]

    # fixed for no GPR plots
    source_indicies,GPRs = [],[]
    for BG in UDS['Features']['ParcelBoundaries']:
        if 'GPR' in BG['properties'] and BG['properties']['GPR']!= None:

            source_indicies.append(find_nearest_node(G, shape(BG['geometry']).centroid))
            GPRs.append(BG['properties']['GPR'])

    for GPR, source_index in zip(GPRs,source_indicies):
        if GPR:
            for target_index in target_indicies:
                shortest_path_node = nx.shortest_path(G, source=list(G.nodes())[source_index], target=list(G.nodes())[target_index] , weight="weight")
                shortest_path_node_index = [list(G.nodes()).index(coords) for coords in shortest_path_node]
                for spi, epi in zip(shortest_path_node_index[:-1],shortest_path_node_index[1:]): 
                    path_segment_properties = G[list(G.nodes())[spi]][list(G.nodes())[epi]]
                    UDS['Features']['RoadCenterlines'][path_segment_properties['edge_index']]['properties']['DensityReach'] += 0.001 * float(GPR) * float(path_segment_properties['category']) * float(path_segment_properties['length'])

    UDS['Evaluations']['TotalDensityReach'] = sum([RC['properties']['DensityReach'] for RC in UDS['Features']['RoadCenterlines']])
    return UDS


