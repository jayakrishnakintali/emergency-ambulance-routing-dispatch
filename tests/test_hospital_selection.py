"""Tests for hospital selection and completing a response (no GUI involved)."""

import unittest

from ambulance_system import (
    Ambulance,
    AmbulanceDispatchSystem,
    DispatchError,
    STATUS_COMPLETED,
)
from graph_algorithms import Graph


def build_hospital_system() -> AmbulanceDispatchSystem:
    """
        Near --2-- Incident --6-- Far
                      |
                      +--4-- Junction --1-- Middle     'Lonely' is disconnected.

    Hospitals: Near (2 km), Middle (5 km via Junction), Far (6 km), Lonely (unreachable).
    """
    graph = Graph()
    for name in ["Near", "Incident", "Far", "Junction", "Middle", "Lonely", "Depot"]:
        graph.add_location(name)
    graph.add_road("Near", "Incident", 2)
    graph.add_road("Incident", "Far", 6)
    graph.add_road("Incident", "Junction", 4)
    graph.add_road("Junction", "Middle", 1)
    graph.add_road("Depot", "Incident", 3)
    return AmbulanceDispatchSystem(
        graph, [Ambulance("AMB-1", "Depot")], ["Far", "Lonely", "Middle", "Near"])


class TestHospitalSelection(unittest.TestCase):
    def setUp(self) -> None:
        self.system = build_hospital_system()
        self.system.add_request("Incident", "Critical")
        self.system.dispatch_next_request()

    def test_nearest_reachable_hospital_is_chosen(self):
        result = self.system.complete_active_response()
        self.assertEqual(result.hospital_name, "Near")
        self.assertEqual(result.route.distance_km, 2.0)
        self.assertEqual(result.route.path, ["Incident", "Near"])

    def test_unreachable_hospital_is_ignored_but_reported(self):
        result = self.system.complete_active_response()
        reachability = {name: route.reachable for name, route in result.candidates}
        self.assertFalse(reachability["Lonely"])
        self.assertTrue(reachability["Far"])

    def test_completing_updates_request_and_ambulance(self):
        result = self.system.complete_active_response()
        self.assertEqual(result.request.status, STATUS_COMPLETED)
        self.assertEqual(result.request.hospital_name, "Near")
        ambulance = self.system.ambulances[0]
        self.assertEqual(ambulance.location, "Near")
        self.assertTrue(ambulance.available)
        self.assertFalse(self.system.has_active_response)

    def test_new_dispatch_allowed_after_completion(self):
        self.system.complete_active_response()
        self.system.add_request("Far", "Low")
        result = self.system.dispatch_next_request()
        self.assertEqual(result.ambulance.ambulance_id, "AMB-1")
        self.assertEqual(result.route.start, "Near")      # ambulance starts from the hospital now

    def test_complete_without_active_response_raises_error(self):
        self.system.complete_active_response()
        with self.assertRaises(DispatchError):
            self.system.complete_active_response()


class TestNoReachableHospital(unittest.TestCase):
    def test_response_stays_active_if_no_hospital_reachable(self):
        graph = Graph()
        for name in ["Depot", "Incident", "Lonely"]:
            graph.add_location(name)
        graph.add_road("Depot", "Incident", 1)
        system = AmbulanceDispatchSystem(graph, [Ambulance("AMB-1", "Depot")], ["Lonely"])
        system.add_request("Incident", "High")
        system.dispatch_next_request()
        with self.assertRaises(DispatchError):
            system.complete_active_response()
        self.assertTrue(system.has_active_response)
        self.assertFalse(system.ambulances[0].available)


if __name__ == "__main__":
    unittest.main()
