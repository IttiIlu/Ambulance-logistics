"""Folium map generation with stations, emergencies, and routes"""
import folium

KHARKIV_CENTER = (49.9808, 36.2527)


def create_base_map():
    """Create map with 6 ambulance stations"""
    m = folium.Map(
        location=KHARKIV_CENTER,
        zoom_start=12,
        min_zoom=11,
        max_zoom=15,
        tiles='OpenStreetMap',
        max_bounds=True
    )
    m.fit_bounds([[49.93, 36.15], [50.03, 36.35]])

    # Add 6 stations with ambulances
    offset = 0.025
    lat, lon = KHARKIV_CENTER
    stations = [
        (lat, lon, "Central Station"),
        (lat + offset, lon, "North Station"),
        (lat - offset, lon, "South Station"),
        (lat, lon + offset, "East Station"),
        (lat, lon - offset, "West Station"),
        (lat + offset/1.5, lon + offset/1.5, "Northeast Station")
    ]

    for i, (lat, lon, name) in enumerate(stations, 1):
        # Station marker
        folium.Marker(
            [lat, lon], popup=name, tooltip=name,
            icon=folium.Icon(color='blue', icon='home', prefix='fa')
        ).add_to(m)

        # Ambulance background circle
        folium.CircleMarker(
            [lat, lon], radius=12, popup=f'Ambulance {i}', tooltip=f'Ambulance {i}',
            color='#ff0000', fill=True, fillColor='#ff0000', fillOpacity=0.3, weight=2
        ).add_to(m)

        # Ambulance icon
        folium.Marker(
            [lat, lon], popup=f'<b>Ambulance {i}</b><br>{name}', tooltip=f'Ambulance {i}',
            icon=folium.Icon(color='red', icon='ambulance', prefix='fa')
        ).add_to(m)

    return m


def add_emergency_to_map(base_map, lat, lon):
    """Add emergency marker to map"""
    folium.CircleMarker(
        [lat, lon], radius=15, popup=f'<b>EMERGENCY</b><br>{lat:.4f}, {lon:.4f}',
        tooltip='Emergency Call', color='#ff0000', fill=True,
        fillColor='#ff0000', fillOpacity=0.7, weight=3
    ).add_to(base_map)

    folium.Marker(
        [lat, lon], popup=f'<b>EMERGENCY</b><br>{lat:.4f}, {lon:.4f}',
        tooltip='Emergency Call',
        icon=folium.Icon(color='red', icon='exclamation-triangle', prefix='fa')
    ).add_to(base_map)


def add_impact_zones_to_map(base_map, impact_zones):
    """Impact zones rendered as blocked road lines only"""
    pass


def add_blocked_roads_to_map(base_map, blocked_edges_coords):
    """Add blocked road segments as red dashed lines"""
    for coords in blocked_edges_coords:
        folium.PolyLine(
            coords, color='#ff0000', weight=8, opacity=1.0, dash_array='15, 10',
            popup='<b>BLOCKED ROAD</b>', tooltip='Blocked Road'
        ).add_to(base_map)


def add_route_to_map(base_map, graph, route_path, color, weight=5, opacity=0.7, route_info=None):
    """Add route path using actual road geometry"""
    coords = []

    for i in range(len(route_path) - 1):
        u, v = route_path[i], route_path[i + 1]

        if graph.has_edge(u, v):
            edge_data = graph[u][v]
            edge_key = list(edge_data.keys())[0]
            edge_info = edge_data[edge_key]

            if 'geometry' in edge_info:
                coords.extend([(p[1], p[0]) for p in edge_info['geometry'].coords])
            else:
                if not coords or coords[-1] != [graph.nodes[u]['y'], graph.nodes[u]['x']]:
                    coords.append([graph.nodes[u]['y'], graph.nodes[u]['x']])
                coords.append([graph.nodes[v]['y'], graph.nodes[v]['x']])

    if coords:
        tooltip = popup = "Route"
        if route_info:
            tooltip = f"{route_info['name']}: {route_info['time_min']:.1f} min, {route_info['distance_km']:.2f} km"
            popup = f"<b>{route_info['name']}</b><br>Time: {route_info['time_min']:.1f} min<br>Distance: {route_info['distance_km']:.2f} km"

        folium.PolyLine(
            coords, color=color, weight=weight, opacity=opacity,
            tooltip=tooltip, popup=popup
        ).add_to(base_map)
