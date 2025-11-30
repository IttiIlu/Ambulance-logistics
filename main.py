"""Ambulance Logistics - Kharkiv Emergency Response System"""
import sys
import os
import random
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QLabel, QFrame, QPushButton
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QFont

from map_generator import (
    create_base_map, add_emergency_to_map, add_blocked_roads_to_map,
    add_impact_zones_to_map, add_route_to_map, KHARKIV_CENTER
)
from road_network import load_road_graph, get_edge_geometry, get_major_road_edges
from pathfinding import find_routes


class AmbulanceCard(QFrame):
    """Clickable ambulance status card"""

    def __init__(self, ambulance_id, station, status, is_selected=False, on_click=None):
        super().__init__()
        self.ambulance_id = ambulance_id
        self.station = station
        self.status = status
        self.is_selected = is_selected
        self.on_click = on_click
        self._setup_ui()

    def mousePressEvent(self, event):
        if self.on_click:
            self.on_click(self.ambulance_id, self.station)
        super().mousePressEvent(event)

    def update_selection_style(self):
        border = "border: 2px solid #5865f2;" if self.is_selected else "border: 1px solid #1a1b1e;"
        self.setStyleSheet(f"""
            AmbulanceCard {{
                background-color: #2b2d31; border-radius: 8px;
                padding: 0px; margin: 4px; {border}
            }}
            AmbulanceCard:hover {{background-color: #313338;}}
        """)

    def _setup_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_selection_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Top row: ID and status
        top_row = QHBoxLayout()
        id_label = QLabel(f"Ambulance {self.ambulance_id}")
        id_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        id_label.setStyleSheet("color: #f2f3f5;")
        top_row.addWidget(id_label)
        top_row.addStretch()
        top_row.addWidget(self._create_status_badge())
        layout.addLayout(top_row)

        # Station label
        station_label = QLabel(f"Station {self.station}")
        station_label.setFont(QFont("Segoe UI", 9))
        station_label.setStyleSheet("color: #949ba4;")
        layout.addWidget(station_label)

    def _create_status_badge(self):
        """Create status indicator badge"""
        colors = {"Available": ("#23a55a", "#1a3a2a"), "Busy": ("#f23f43", "#3a1a1a")}
        fg, bg = colors.get(self.status, ("#f0b232", "#3a2f1a"))

        container = QFrame()
        container.setStyleSheet(f"QFrame {{background-color: {bg}; border-radius: 12px;}}")

        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 4, 8, 4)

        dot = QLabel("●")
        dot.setFont(QFont("Segoe UI", 10))
        dot.setStyleSheet(f"color: {fg};")
        layout.addWidget(dot)

        text = QLabel(self.status)
        text.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
        text.setStyleSheet(f"color: {fg};")
        layout.addWidget(text)

        return container


class RouteCard(QFrame):
    """Clickable route option card"""

    def __init__(self, route_data, is_selected=False, on_click=None):
        super().__init__()
        self.route_data = route_data
        self.is_selected = is_selected
        self.on_click = on_click
        self._setup_ui()

    def mousePressEvent(self, event):
        if self.on_click:
            self.on_click(self.route_data)
        super().mousePressEvent(event)

    def update_selection_style(self):
        colors = {'fastest': '#00c853', 'alternative': '#ffa726'}
        accent = colors.get(self.route_data['type'], '#00c853')
        border = f"border: 2px solid {accent};" if self.is_selected else "border: 1px solid #1a1b1e;"
        self.setStyleSheet(f"""
            RouteCard {{
                background-color: #2b2d31; border-radius: 8px; {border}
            }}
            RouteCard:hover {{background-color: #313338;}}
        """)

    def _setup_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_selection_style()

        colors = {'fastest': ('#00c853', '#1a3a2a'), 'alternative': ('#ffa726', '#3a2f1a')}
        accent, bg_accent = colors.get(self.route_data['type'], ('#00c853', '#1a3a2a'))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Top row: name and indicator
        top_row = QHBoxLayout()
        name = QLabel(self.route_data['name'])
        name.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        name.setStyleSheet("color: #f2f3f5;")
        top_row.addWidget(name)
        top_row.addStretch()

        indicator = QFrame()
        indicator.setStyleSheet(f"background-color: {bg_accent}; border-radius: 10px; padding: 4px 10px;")
        ind_layout = QHBoxLayout(indicator)
        ind_layout.setContentsMargins(8, 4, 8, 4)
        dot = QLabel("●")
        dot.setFont(QFont("Segoe UI", 9))
        dot.setStyleSheet(f"color: {accent};")
        ind_layout.addWidget(dot)
        top_row.addWidget(indicator)
        layout.addLayout(top_row)

        # Stats row
        stats = QHBoxLayout()
        time = QLabel(f"⏱ {self.route_data['time_min']:.1f} min")
        time.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        time.setStyleSheet("color: #ffffff;")
        stats.addWidget(time)

        stats.addWidget(QLabel("•") if True else None)
        stats.itemAt(1).widget().setStyleSheet("color: #4e5058;")

        dist = QLabel(f"{self.route_data['distance_km']:.2f} km")
        dist.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        dist.setStyleSheet("color: #b5bac1;")
        stats.addWidget(dist)
        stats.addStretch()
        layout.addLayout(stats)


class AmbulanceApp(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ambulance Logistics - Kharkiv")
        self.setGeometry(100, 100, 1600, 900)
        self._apply_theme()
        self._setup_ui()
        self._load_data()

    def _apply_theme(self):
        """Apply dark theme stylesheet"""
        self.setStyleSheet("""
            QMainWindow {background-color: #1e1f22;}
            QWidget {font-family: 'Segoe UI', Arial, sans-serif;}
            QScrollBar:vertical {background-color: #2b2d31; width: 12px; border-radius: 6px;}
            QScrollBar::handle:vertical {background-color: #1a1b1e; border-radius: 6px; min-height: 20px;}
            QScrollBar::handle:vertical:hover {background-color: #3e4045;}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {height: 0px;}
        """)

    def _setup_ui(self):
        """Setup main UI layout"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(self._create_sidebar())

        # Map view
        self.web_view = QWebEngineView()
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        layout.addWidget(self.web_view)

    def _create_sidebar(self):
        """Create left sidebar with controls and status"""
        sidebar = QWidget()
        sidebar.setFixedWidth(350)
        sidebar.setStyleSheet("QWidget {background-color: #313338;}")

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(16)

        # Title
        title = QLabel("Ambulances")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #f2f3f5;")
        layout.addWidget(title)

        subtitle = QLabel("Real-time vehicle status")
        subtitle.setFont(QFont("Segoe UI", 10))
        subtitle.setStyleSheet("color: #949ba4;")
        layout.addWidget(subtitle)

        # Action buttons
        layout.addWidget(self._create_button("Generate Emergency", "#5865f2", self.generate_emergency))
        layout.addWidget(self._create_button("Heavy Damage", "#ed4245", self.block_roads))

        # Routes section
        self.routes_section = QWidget()
        routes_layout = QVBoxLayout(self.routes_section)
        routes_layout.setContentsMargins(0, 8, 0, 8)

        routes_title = QLabel("Route Options")
        routes_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        routes_title.setStyleSheet("color: #f2f3f5;")
        routes_layout.addWidget(routes_title)

        self.routes_container = QWidget()
        self.routes_layout = QVBoxLayout(self.routes_container)
        self.routes_layout.setContentsMargins(0, 0, 0, 0)
        routes_layout.addWidget(self.routes_container)
        self.routes_section.hide()
        layout.addWidget(self.routes_section)

        # Ambulance cards scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea {background-color: transparent; border: none;}")

        cards_container = QWidget()
        cards_layout = QVBoxLayout(cards_container)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(8)

        self.ambulance_cards = []
        for i in range(1, 7):
            card = AmbulanceCard(i, i, "Available", on_click=self.select_ambulance)
            cards_layout.addWidget(card)
            self.ambulance_cards.append(card)

        cards_layout.addStretch()
        scroll.setWidget(cards_container)
        layout.addWidget(scroll)

        return sidebar

    def _create_button(self, text, color, callback):
        """Create styled action button"""
        btn = QPushButton(text)
        btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color}; color: #ffffff; border: none;
                border-radius: 6px; padding: 12px 20px; margin: 8px 0px;
            }}
            QPushButton:hover {{background-color: {color}dd;}}
            QPushButton:pressed {{background-color: {color}bb;}}
        """)
        btn.clicked.connect(callback)
        return btn

    def _load_data(self):
        """Load road graph and initialize state"""
        try:
            self.road_graph = load_road_graph()
            self.major_road_edges = get_major_road_edges(self.road_graph)
            print(f"Loaded: {len(self.road_graph.edges)} edges, {len(self.major_road_edges)} major roads")

            # Initialize state
            self.emergency_location = None
            self.blocked_edges = []
            self.blocked_edges_coords = []
            self.impact_zones = []
            self.map_file = "map.html"

            # Station positions
            offset = 0.025
            lat, lon = KHARKIV_CENTER
            self.stations = [
                (lat, lon, "Central"), (lat + offset, lon, "North"),
                (lat - offset, lon, "South"), (lat, lon + offset, "East"),
                (lat, lon - offset, "West"), (lat + offset/1.5, lon + offset/1.5, "Northeast")
            ]

            self.calculated_routes = []
            self.selected_ambulance_station = None
            self.selected_route = None

            self._update_map()
        except Exception as e:
            print(f"Error loading: {e}")

    def _update_map(self):
        """Update map with current state"""
        m = create_base_map()
        if self.impact_zones:
            add_impact_zones_to_map(m, self.impact_zones)
        if self.blocked_edges_coords:
            add_blocked_roads_to_map(m, self.blocked_edges_coords)
        if self.emergency_location:
            add_emergency_to_map(m, *self.emergency_location)
        m.save(self.map_file)
        self.web_view.setUrl(QUrl.fromLocalFile(os.path.abspath(self.map_file)))

    def select_ambulance(self, ambulance_id, station_id):
        """Handle ambulance selection"""
        if not self.emergency_location:
            return

        # Update selection state
        for card in self.ambulance_cards:
            card.is_selected = (card.ambulance_id == ambulance_id)
            card.update_selection_style()

        self.selected_ambulance_station = station_id
        station_lat, station_lon, _ = self.stations[station_id - 1]

        # Calculate routes
        try:
            self.calculated_routes = find_routes(
                self.road_graph, station_lat, station_lon,
                *self.emergency_location, self.blocked_edges
            )
            print(f"Found {len(self.calculated_routes)} routes for Ambulance {ambulance_id}")
        except Exception as e:
            print(f"Route error: {e}")
            self.calculated_routes = []

        self._populate_route_cards()

    def generate_emergency(self):
        """Generate random emergency call"""
        offset = 0.03
        lat, lon = KHARKIV_CENTER
        self.emergency_location = (
            lat + random.uniform(-offset, offset),
            lon + random.uniform(-offset, offset)
        )

        # Reset selection
        for card in self.ambulance_cards:
            card.is_selected = False
            card.update_selection_style()

        self.selected_ambulance_station = None
        self.calculated_routes = []
        self.routes_section.hide()
        self._update_map()
        print(f"Emergency at: {self.emergency_location[0]:.4f}, {self.emergency_location[1]:.4f}")

    def _populate_route_cards(self):
        """Populate route options UI"""
        # Clear existing cards
        while self.routes_layout.count():
            item = self.routes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.calculated_routes:
            # Show no route message
            self.routes_section.show()
            no_route = QLabel("⚠ No route available")
            no_route.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            no_route.setStyleSheet("color: #f23f43; padding: 16px; background-color: #2b2d31; border-radius: 8px;")
            no_route.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.routes_layout.addWidget(no_route)

            help_text = QLabel("All roads are blocked.\nTry another ambulance.")
            help_text.setFont(QFont("Segoe UI", 9))
            help_text.setStyleSheet("color: #949ba4; padding: 8px;")
            help_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.routes_layout.addWidget(help_text)
            return

        # Show route cards
        self.routes_section.show()
        for route in self.calculated_routes:
            card = RouteCard(route, route == self.calculated_routes[0], self.select_route)
            self.routes_layout.addWidget(card)

        if self.calculated_routes:
            self.selected_route = self.calculated_routes[0]
            self._update_map_with_route()

    def select_route(self, route_data):
        """Handle route selection"""
        self.selected_route = route_data
        for i in range(self.routes_layout.count()):
            card = self.routes_layout.itemAt(i).widget()
            if card:
                card.is_selected = (card.route_data == route_data)
                card.update_selection_style()
        self._update_map_with_route()

    def _update_map_with_route(self):
        """Update map showing selected route"""
        m = create_base_map()
        if self.impact_zones:
            add_impact_zones_to_map(m, self.impact_zones)
        if self.blocked_edges_coords:
            add_blocked_roads_to_map(m, self.blocked_edges_coords)
        if self.emergency_location:
            add_emergency_to_map(m, *self.emergency_location)
        if self.selected_route:
            add_route_to_map(m, self.road_graph, self.selected_route['path'],
                           self.selected_route['color'], 6, 0.8, self.selected_route)
        m.save(self.map_file)
        self.web_view.setUrl(QUrl.fromLocalFile(os.path.abspath(self.map_file)))

    def block_roads(self):
        """Simulate road damage from impacts"""
        if not self.major_road_edges:
            return

        # Generate random impact points
        num_impacts = random.randint(3, 5)
        lat, lon = KHARKIV_CENTER
        radius = 0.02
        impacts = [(lat + random.uniform(-radius, radius),
                   lon + random.uniform(-radius, radius))
                  for _ in range(num_impacts)]

        self.blocked_edges = []
        self.blocked_edges_coords = []
        self.impact_zones = []

        # Block roads near each impact
        for impact_lat, impact_lon in impacts:
            nearby = []
            for edge in self.major_road_edges:
                if edge in self.blocked_edges:
                    continue

                u, v, key = edge
                mid_lat = (self.road_graph.nodes[u]['y'] + self.road_graph.nodes[v]['y']) / 2
                mid_lon = (self.road_graph.nodes[u]['x'] + self.road_graph.nodes[v]['x']) / 2
                dist = ((mid_lat - impact_lat)**2 + (mid_lon - impact_lon)**2)**0.5

                if dist <= 0.008:
                    nearby.append((edge, dist))

            nearby.sort(key=lambda x: x[1])
            blocked_count = 0

            for edge, _ in nearby[:random.randint(2, 4)]:
                u, v, key = edge

                # Block forward direction
                if edge not in self.blocked_edges:
                    self.blocked_edges.append(edge)
                    self.blocked_edges_coords.append(get_edge_geometry(self.road_graph, edge))
                    blocked_count += 1

                # Block reverse direction (whole road destroyed)
                reverse_edge = (v, u, key)
                if self.road_graph.has_edge(v, u, key) and reverse_edge not in self.blocked_edges:
                    self.blocked_edges.append(reverse_edge)
                    blocked_count += 1

            self.impact_zones.append({'lat': impact_lat, 'lon': impact_lon, 'roads_damaged': blocked_count})

        print(f"{num_impacts} impacts, {len(self.blocked_edges)} roads blocked")

        # Recalculate routes if needed
        if self.emergency_location and self.selected_ambulance_station:
            station_lat, station_lon, _ = self.stations[self.selected_ambulance_station - 1]
            try:
                self.calculated_routes = find_routes(
                    self.road_graph, station_lat, station_lon,
                    *self.emergency_location, self.blocked_edges
                )
            except:
                self.calculated_routes = []
            self._populate_route_cards()
        else:
            self._update_map()


def main():
    """Application entry point"""
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = AmbulanceApp()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
