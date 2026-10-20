"""Tests for the Graph class and Dijkstra's algorithm (no GUI involved)."""

import unittest

from city_data import build_sample_graph
from graph_algorithms import Graph, GraphError, dijkstra


def build_known_graph() -> Graph:
    """
    Small graph with a known answer:

        A --1-- B --1-- C
        |               |
        +-------5-------+      (A-C direct is 5, but A-B-C is only 2)
        C --3-- D        E is isolated (unreachable)
    """
    graph = Graph()
    for name in ["A", "B", "C", "D", "E"]:
        graph.add_location(name)
    graph.add_road("A", "B", 1)
    graph.add_road("B", "C", 1)
    graph.add_road("A", "C", 5)
    graph.add_road("C", "D", 3)
    return graph


class TestDijkstra(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = build_known_graph()

    def test_correct_shortest_distance(self):
        result = dijkstra(self.graph, "A", "D")
        self.assertTrue(result.reachable)
        self.assertEqual(result.distance_km, 5.0)       # A-B-C-D = 1 + 1 + 3

    def test_shortest_path_is_not_fewest_edges(self):
        result = dijkstra(self.graph, "A", "C")
        self.assertEqual(result.path, ["A", "B", "C"])  # 2 edges beat the 1-edge road of 5 km
        self.assertEqual(result.distance_km, 2.0)

    def test_path_uses_only_valid_edges_and_matches_distance(self):
        result = dijkstra(self.graph, "A", "D")
        total = 0.0
        for location_a, location_b in zip(result.path, result.path[1:]):
            self.assertIn(location_b, self.graph.neighbors(location_a))
            total += self.graph.neighbors(location_a)[location_b]
        self.assertEqual(total, result.distance_km)

    def test_start_and_destination_are_correct(self):
        result = dijkstra(self.graph, "A", "D")
        self.assertEqual(result.path[0], "A")
        self.assertEqual(result.path[-1], "D")

    def test_same_start_and_destination(self):
        result = dijkstra(self.graph, "B", "B")
        self.assertTrue(result.reachable)
        self.assertEqual(result.distance_km, 0.0)
        self.assertEqual(result.path, ["B"])

    def test_unreachable_destination_is_handled_safely(self):
        result = dijkstra(self.graph, "A", "E")
        self.assertFalse(result.reachable)
        self.assertIsNone(result.distance_km)
        self.assertEqual(result.path, [])

    def test_unknown_location_raises_error(self):
        with self.assertRaises(GraphError):
            dijkstra(self.graph, "A", "Nowhere")
        with self.assertRaises(GraphError):
            dijkstra(self.graph, "Nowhere", "A")

    def test_performance_information_is_reported(self):
        result = dijkstra(self.graph, "A", "D")
        self.assertGreater(result.operations, 0)
        self.assertGreaterEqual(result.runtime_ms, 0.0)

    def test_roads_work_in_both_directions(self):
        forward = dijkstra(self.graph, "A", "D").distance_km
        backward = dijkstra(self.graph, "D", "A").distance_km
        self.assertEqual(forward, backward)


class TestGraphValidation(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = Graph()
        self.graph.add_location("A")
        self.graph.add_location("B")

    def test_negative_weight_is_rejected(self):
        with self.assertRaises(GraphError):
            self.graph.add_road("A", "B", -2)

    def test_zero_weight_is_rejected(self):
        with self.assertRaises(GraphError):
            self.graph.add_road("A", "B", 0)

    def test_non_numeric_weight_is_rejected(self):
        with self.assertRaises(GraphError):
            self.graph.add_road("A", "B", "far")

    def test_road_to_unknown_location_is_rejected(self):
        with self.assertRaises(GraphError):
            self.graph.add_road("A", "Z", 3)

    def test_rejected_weight_does_not_enter_graph(self):
        try:
            self.graph.add_road("A", "B", -1)
        except GraphError:
            pass
        self.assertEqual(self.graph.road_count(), 0)


class TestSampleCity(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = build_sample_graph()

    def test_sample_city_size(self):
        self.assertTrue(8 <= self.graph.location_count() <= 12)

    def test_sample_city_has_shortest_route_with_more_edges(self):
        result = dijkstra(self.graph, "Railway Station", "Central Square")
        self.assertEqual(result.distance_km, 6.0)
        self.assertEqual(result.path, ["Railway Station", "Green Park", "Central Square"])
        # The direct road exists but is longer (9 km) than the 2-edge route (6 km).
        self.assertGreater(self.graph.neighbors("Railway Station")["Central Square"], result.distance_km)


if __name__ == "__main__":
    unittest.main()
