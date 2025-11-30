"""Ambulance pathfinding with blocked road avoidance"""
import networkx as nx
import osmnx as ox


def find_nearest_node(graph, lat, lon):
    """Find nearest graph node to coordinates"""
    return ox.distance.nearest_nodes(graph, lon, lat)


def calculate_route_metrics(graph, route):
    """Calculate distance (km) and time (min) for a route"""
    distance_m = 0
    time_hours = 0

    for i in range(len(route) - 1):
        edge_data = min(graph[route[i]][route[i + 1]].values(),
                       key=lambda x: x.get('length', float('inf')))
        length = edge_data.get('length', 0)
        distance_m += length

        # Speed: 80 km/h for highways, 60 km/h for others
        highway = edge_data.get('highway', '')
        speed = 80 if highway in ['motorway', 'trunk', 'primary'] else 60
        time_hours += (length / 1000) / speed

    return distance_m / 1000, time_hours * 60


def find_routes(graph, start_lat, start_lon, end_lat, end_lon, blocked_edges):
    """Find fastest and alternative routes avoiding blocked edges"""
    start_node = find_nearest_node(graph, start_lat, start_lon)
    end_node = find_nearest_node(graph, end_lat, end_lon)

    # Remove blocked edges in both directions
    graph_clean = graph.copy()
    removed = 0
    for u, v, key in blocked_edges:
        if graph_clean.has_edge(u, v, key):
            graph_clean.remove_edge(u, v, key)
            removed += 1
        if graph_clean.has_edge(v, u, key):
            graph_clean.remove_edge(v, u, key)
            removed += 1

    print(f"Removed {removed} edge directions from graph ({len(blocked_edges)} blocked roads)")

    # Find fastest route
    try:
        path = nx.shortest_path(graph_clean, start_node, end_node, weight='length')
        distance, time = calculate_route_metrics(graph_clean, path)
        routes = [{
            'name': 'Fastest Route',
            'path': path,
            'distance_km': distance,
            'time_min': time,
            'color': '#00c853',
            'type': 'fastest'
        }]
    except nx.NetworkXNoPath:
        print("No path found - all routes blocked!")
        return []

    # Find alternative route (remove middle section of fastest path)
    if len(path) > 10:
        graph_alt = graph_clean.copy()
        mid_start, mid_end = len(path) // 3, 2 * len(path) // 3

        for i in range(mid_start, min(mid_end, len(path) - 1)):
            u, v = path[i], path[i + 1]
            if graph_alt.has_edge(u, v):
                for key in list(graph_alt[u][v].keys()):
                    graph_alt.remove_edge(u, v, key)

        try:
            alt_path = nx.shortest_path(graph_alt, start_node, end_node, weight='length')
            if alt_path != path:
                distance, time = calculate_route_metrics(graph_clean, alt_path)
                routes.append({
                    'name': 'Alternative Route',
                    'path': alt_path,
                    'distance_km': distance,
                    'time_min': time,
                    'color': '#ffa726',
                    'type': 'alternative'
                })
        except nx.NetworkXNoPath:
            pass

    return routes
