"""Road network graph loading and caching"""
import os
import pickle
import osmnx as ox

CACHE_FILE = "road_graph.pkl"


def load_road_graph():
    """Load cached or download road graph for Kharkiv"""
    if os.path.exists(CACHE_FILE):
        print("Loading road graph from cache...")
        with open(CACHE_FILE, 'rb') as f:
            return pickle.load(f)

    print("Downloading road graph from OSM...")
    graph = ox.graph_from_place("Kharkiv, Ukraine", network_type='drive')

    with open(CACHE_FILE, 'wb') as f:
        pickle.dump(graph, f)
    print(f"Road graph cached ({len(graph.edges)} edges)")
    return graph


def get_major_road_edges(graph, center_lat=49.9808, center_lon=36.2527, max_dist=0.015):
    """Get major road edges near city center"""
    major_types = ['motorway', 'motorway_link', 'trunk', 'trunk_link',
                   'primary', 'primary_link', 'secondary', 'secondary_link']
    major_edges = []

    for u, v, key, data in graph.edges(keys=True, data=True):
        highway = data.get('highway', '')
        highway = highway[0] if isinstance(highway, list) else highway

        if highway in major_types:
            mid_lat = (graph.nodes[u]['y'] + graph.nodes[v]['y']) / 2
            mid_lon = (graph.nodes[u]['x'] + graph.nodes[v]['x']) / 2
            dist = ((mid_lat - center_lat)**2 + (mid_lon - center_lon)**2)**0.5

            if dist <= max_dist:
                major_edges.append((u, v, key))

    print(f"Found {len(major_edges)} major roads in center (out of {len(graph.edges)} total)")
    return major_edges


def get_edge_geometry(graph, edge):
    """Get coordinates for an edge (uses geometry or node positions)"""
    u, v, key = edge
    edge_data = graph.edges[u, v, key]

    if 'geometry' in edge_data:
        return [(p[1], p[0]) for p in edge_data['geometry'].coords]

    return [[graph.nodes[u]['y'], graph.nodes[u]['x']],
            [graph.nodes[v]['y'], graph.nodes[v]['x']]]
