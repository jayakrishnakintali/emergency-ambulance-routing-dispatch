"""
graph_algorithms.py
-------------------
Graph data structure and Dijkstra's shortest-path algorithm.

This module knows nothing about ambulances, hospitals or the GUI.
It only deals with locations (vertices) and roads (weighted edges).
"""

import heapq
import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


class GraphError(Exception):
    """Raised when the graph is used incorrectly (bad location, bad distance...)."""


class Graph:
    """
    Weighted, undirected graph stored as an ADJACENCY LIST.

    Internal shape:
        {
            "A": {"B": 4.0, "C": 2.0},   # A is connected to B (4 km) and C (2 km)
            "B": {"A": 4.0},
            "C": {"A": 2.0},
        }

    Space used is O(V + E): we store only the roads that really exist.
    """

    def __init__(self) -> None:
        self._adjacency: Dict[str, Dict[str, float]] = {}

    # ---------- building the graph ----------
    def add_location(self, name: str) -> None:
        """Add a vertex. Adding the same location twice is harmless."""
        if not isinstance(name, str) or not name.strip():
            raise GraphError("Location name must be a non-empty text value.")
        self._adjacency.setdefault(name, {})

    def add_road(self, location_a: str, location_b: str, distance_km: float) -> None:
        """
        Add an undirected road between two existing locations.

        Validation happens HERE so that an invalid weight (zero, negative,
        NaN, infinity, text) can never enter the graph. Dijkstra's algorithm
        is only correct for non-negative weights, so this protects it.
        """
        if location_a not in self._adjacency or location_b not in self._adjacency:
            raise GraphError(
                f"Both locations must be added before a road: '{location_a}', '{location_b}'."
            )
        if location_a == location_b:
            raise GraphError("A road must connect two different locations.")
        if isinstance(distance_km, bool) or not isinstance(distance_km, (int, float)):
            raise GraphError("Road distance must be a number.")
        if math.isnan(distance_km) or math.isinf(distance_km):
            raise GraphError("Road distance must be a finite number.")
        if distance_km <= 0:
            raise GraphError(
                f"Road distance must be positive (got {distance_km} between "
                f"'{location_a}' and '{location_b}')."
            )
        if location_b in self._adjacency[location_a]:
            raise GraphError(f"Road '{location_a}' - '{location_b}' already exists.")

        # Undirected road = store the edge in both directions.
        self._adjacency[location_a][location_b] = float(distance_km)
        self._adjacency[location_b][location_a] = float(distance_km)

    # ---------- reading the graph ----------
    def has_location(self, name: str) -> bool:
        return name in self._adjacency

    def locations(self) -> List[str]:
        """All vertices, in the order they were added."""
        return list(self._adjacency.keys())

    def neighbors(self, name: str) -> Dict[str, float]:
        """Return {neighbour: distance} for one location."""
        if name not in self._adjacency:
            raise GraphError(f"Unknown location: '{name}'.")
        return self._adjacency[name]

    def roads(self) -> List[Tuple[str, str, float]]:
        """Every road exactly once as (location_a, location_b, distance_km)."""
        seen = set()
        road_list = []
        for location_a, connections in self._adjacency.items():
            for location_b, distance in connections.items():
                key = frozenset((location_a, location_b))
                if key not in seen:
                    seen.add(key)
                    road_list.append((location_a, location_b, distance))
        return road_list

    def location_count(self) -> int:
        return len(self._adjacency)

    def road_count(self) -> int:
        return len(self.roads())


@dataclass
class ShortestPathResult:
    """Everything Dijkstra's algorithm reports for one route calculation."""

    start: str
    destination: str
    reachable: bool
    distance_km: Optional[float]          # None when unreachable
    path: List[str] = field(default_factory=list)   # [] when unreachable
    operations: int = 0                   # see dijkstra() docstring
    runtime_ms: float = 0.0               # measured with time.perf_counter()


def dijkstra(graph: Graph, start: str, destination: str) -> ShortestPathResult:
    """
    Shortest road distance from `start` to `destination` using Dijkstra's
    algorithm with a min-priority queue (Python's heapq).

    Idea (greedy):
      1. Give every location a tentative distance: 0 for start, infinity for the rest.
      2. Repeatedly take the not-yet-finished location with the SMALLEST tentative
         distance. With non-negative weights, that distance can no longer improve,
         so the location is "settled".
      3. "Relax" each road leaving it: if going through this location gives a
         shorter way to a neighbour, update the neighbour and remember where we
         came from (previous[neighbour] = this location).
      4. Stop when the destination is settled, or the queue is empty
         (empty queue + destination not settled = unreachable).

    OPERATION COUNT (clearly defined for this project):
        operations = (number of heap pops) + (number of roads examined)
    A "road examined" means one iteration of the inner loop over a location's
    neighbours. This is a simple counter, not a hardware measurement.

    TIME COMPLEXITY: O((V + E) log V) with a binary heap and adjacency list.
    """
    if not graph.has_location(start):
        raise GraphError(f"Unknown start location: '{start}'.")
    if not graph.has_location(destination):
        raise GraphError(f"Unknown destination location: '{destination}'.")

    timer_start = time.perf_counter()
    operations = 0

    distances = {location: math.inf for location in graph.locations()}
    previous: Dict[str, str] = {}          # for rebuilding the path
    settled = set()                        # locations whose distance is final

    distances[start] = 0.0
    priority_queue = [(0.0, start)]        # entries are (distance so far, location)

    while priority_queue:
        current_distance, current_location = heapq.heappop(priority_queue)
        operations += 1

        # The same location can be pushed several times with different
        # distances. Older (larger) entries are stale, so we skip them.
        if current_location in settled:
            continue
        settled.add(current_location)

        if current_location == destination:
            break                          # shortest distance to destination is final

        for neighbour, road_length in graph.neighbors(current_location).items():
            operations += 1
            if neighbour in settled:
                continue
            new_distance = current_distance + road_length
            if new_distance < distances[neighbour]:      # relaxation step
                distances[neighbour] = new_distance
                previous[neighbour] = current_location
                heapq.heappush(priority_queue, (new_distance, neighbour))

    runtime_ms = (time.perf_counter() - timer_start) * 1000.0

    if destination not in settled:
        return ShortestPathResult(start, destination, False, None, [], operations, runtime_ms)

    path = _rebuild_path(previous, start, destination)
    return ShortestPathResult(
        start, destination, True, distances[destination], path, operations, runtime_ms
    )


def _rebuild_path(previous: Dict[str, str], start: str, destination: str) -> List[str]:
    """Walk backwards from destination to start using the `previous` map."""
    path = [destination]
    while path[-1] != start:
        path.append(previous[path[-1]])
    path.reverse()
    return path
