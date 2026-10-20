"""
city_data.py
------------
All sample-city data lives here. To change the city, edit ONLY this file:
add a location, change a distance, add a hospital or add an ambulance.
No algorithm code needs to change.

This is an imaginary city. Distances are invented for the simulation and
do not represent a real place.
"""

from typing import Dict, List, Tuple

from graph_algorithms import Graph

# Size of the schematic map drawing area (GUI scales this to the window).
MAP_WIDTH = 900
MAP_HEIGHT = 560

# location name -> (x, y) position on the schematic map
LOCATION_COORDINATES: Dict[str, Tuple[int, int]] = {
    "North Market": (430, 70),
    "Railway Station": (110, 130),
    "University": (700, 90),
    "Northside Hospital": (830, 150),
    "Green Park": (270, 240),
    "Central Square": (460, 270),
    "City General Hospital": (640, 300),
    "Airport Road": (810, 330),
    "Old Town": (100, 330),
    "River Bridge": (290, 460),
    "Riverside Hospital": (440, 500),
    "Industrial Area": (680, 480),
}

# Which of the locations above are hospitals.
HOSPITALS: List[str] = ["City General Hospital", "Riverside Hospital", "Northside Hospital"]

# (location_a, location_b, distance in km). Roads are two-way.
ROADS: List[Tuple[str, str, float]] = [
    ("North Market", "Railway Station", 5),
    ("North Market", "University", 6),
    ("North Market", "Central Square", 4),
    ("Railway Station", "Green Park", 3),
    ("Railway Station", "Old Town", 4),
    # Direct but long road: 9 km in ONE edge, while Railway Station -> Green Park
    # -> Central Square is only 6 km in TWO edges (shortest is not fewest edges).
    ("Railway Station", "Central Square", 9),
    ("Green Park", "Central Square", 3),
    ("Green Park", "Old Town", 5),
    ("Old Town", "River Bridge", 4),
    ("River Bridge", "Riverside Hospital", 2),
    ("River Bridge", "Central Square", 6),
    ("River Bridge", "Industrial Area", 8),
    ("Central Square", "City General Hospital", 3),
    ("Central Square", "Airport Road", 7),
    ("City General Hospital", "Airport Road", 5),
    ("City General Hospital", "Industrial Area", 5),
    ("Airport Road", "University", 7),
    ("Airport Road", "Industrial Area", 6),
    ("University", "Northside Hospital", 2),
    ("Riverside Hospital", "Industrial Area", 9),
]

# ambulance id -> starting location
AMBULANCE_START_LOCATIONS: Dict[str, str] = {
    "AMB-1": "North Market",
    "AMB-2": "Old Town",
    "AMB-3": "Airport Road",
    "AMB-4": "Industrial Area",
}


def build_sample_graph() -> Graph:
    """Create the Graph object from the data above."""
    graph = Graph()
    for location_name in LOCATION_COORDINATES:
        graph.add_location(location_name)
    for location_a, location_b, distance_km in ROADS:
        graph.add_road(location_a, location_b, distance_km)
    return graph
