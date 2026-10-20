"""Tests for the priority queue, greedy dispatch and reset (no GUI involved)."""

import unittest

from ambulance_system import (
    Ambulance,
    AmbulanceDispatchSystem,
    DispatchError,
    EmergencyPriorityQueue,
    EmergencyRequest,
    STATUS_DISPATCHED,
    STATUS_PENDING,
)
from graph_algorithms import Graph


def build_line_system() -> AmbulanceDispatchSystem:
    """
    A line of locations (distances in km):

        West --2-- Mid --3-- East --4-- Hospital
        (AMB-1)    (incident area)       (AMB-2 starts at Hospital)

    'Island' is not connected to anything.
    """
    graph = Graph()
    for name in ["West", "Mid", "East", "Hospital", "Island"]:
        graph.add_location(name)
    graph.add_road("West", "Mid", 2)
    graph.add_road("Mid", "East", 3)
    graph.add_road("East", "Hospital", 4)
    ambulances = [Ambulance("AMB-1", "West"), Ambulance("AMB-2", "Hospital")]
    return AmbulanceDispatchSystem(graph, ambulances, ["Hospital"])


def make_request(request_id: int, severity: str) -> EmergencyRequest:
    return EmergencyRequest(request_id, "Mid", severity, arrival_order=request_id)


class TestPriorityQueue(unittest.TestCase):
    def test_critical_before_lower_severity(self):
        queue = EmergencyPriorityQueue()
        queue.push(make_request(1, "Low"))
        queue.push(make_request(2, "Medium"))
        queue.push(make_request(3, "Critical"))
        queue.push(make_request(4, "High"))
        order = [queue.pop().severity for _ in range(4)]
        self.assertEqual(order, ["Critical", "High", "Medium", "Low"])

    def test_equal_severity_keeps_arrival_order(self):
        queue = EmergencyPriorityQueue()
        for request_id in (1, 2, 3):
            queue.push(make_request(request_id, "High"))
        self.assertEqual([queue.pop().request_id for _ in range(3)], [1, 2, 3])

    def test_pop_from_empty_queue_raises_error(self):
        with self.assertRaises(DispatchError):
            EmergencyPriorityQueue().pop()


class TestDispatch(unittest.TestCase):
    def setUp(self) -> None:
        self.system = build_line_system()

    def test_highest_priority_request_is_dispatched_first(self):
        self.system.add_request("East", "Low")
        critical = self.system.add_request("Mid", "Critical")
        result = self.system.dispatch_next_request()
        self.assertEqual(result.request.request_id, critical.request_id)

    def test_nearest_available_reachable_ambulance_is_selected(self):
        self.system.add_request("Mid", "High")       # AMB-1 is 2 km away, AMB-2 is 7 km away
        result = self.system.dispatch_next_request()
        self.assertEqual(result.ambulance.ambulance_id, "AMB-1")
        self.assertEqual(result.route.distance_km, 2.0)
        self.assertEqual(result.route.path, ["West", "Mid"])

    def test_dispatched_ambulance_becomes_busy_and_unavailable(self):
        self.system.add_request("Mid", "High")
        result = self.system.dispatch_next_request()
        self.assertFalse(result.ambulance.available)
        free_ids = [a.ambulance_id for a in self.system.available_ambulances()]
        self.assertNotIn(result.ambulance.ambulance_id, free_ids)

    def test_busy_ambulances_are_skipped_when_choosing(self):
        self.system.add_request("West", "High")
        self.system.ambulances[0].available = False  # AMB-1 (closest to West) is busy
        result = self.system.dispatch_next_request()
        self.assertEqual(result.ambulance.ambulance_id, "AMB-2")

    def test_second_dispatch_is_blocked_while_response_active(self):
        self.system.add_request("Mid", "High")
        self.system.add_request("East", "Low")
        self.system.dispatch_next_request()
        with self.assertRaises(DispatchError):
            self.system.dispatch_next_request()
        self.assertEqual(self.system.pending_count(), 1)

    def test_dispatch_with_no_requests_raises_error(self):
        with self.assertRaises(DispatchError):
            self.system.dispatch_next_request()

    def test_unreachable_ambulances_are_ignored(self):
        self.system.ambulances[0].location = "Island"   # AMB-1 cannot reach anything
        self.system.add_request("Mid", "High")
        result = self.system.dispatch_next_request()
        self.assertEqual(result.ambulance.ambulance_id, "AMB-2")

    def test_unreachable_incident_keeps_request_pending(self):
        self.system.add_request("Island", "Critical")
        with self.assertRaises(DispatchError):
            self.system.dispatch_next_request()
        self.assertEqual(self.system.pending_count(), 1)
        self.assertEqual(self.system.requests[0].status, STATUS_PENDING)
        self.assertTrue(all(ambulance.available for ambulance in self.system.ambulances))

    def test_no_available_ambulance_raises_error(self):
        for ambulance in self.system.ambulances:
            ambulance.available = False
        self.system.add_request("Mid", "High")
        with self.assertRaises(DispatchError):
            self.system.dispatch_next_request()

    def test_dispatch_marks_request_and_ambulance(self):
        self.system.add_request("Mid", "High")
        result = self.system.dispatch_next_request()
        self.assertEqual(result.request.status, STATUS_DISPATCHED)
        self.assertEqual(result.request.assigned_ambulance_id, "AMB-1")
        self.assertFalse(result.ambulance.available)


class TestInputValidation(unittest.TestCase):
    def setUp(self) -> None:
        self.system = build_line_system()

    def test_empty_location_is_rejected(self):
        with self.assertRaises(DispatchError):
            self.system.add_request("", "High")

    def test_unknown_location_is_rejected(self):
        with self.assertRaises(DispatchError):
            self.system.add_request("Atlantis", "High")

    def test_invalid_severity_is_rejected(self):
        with self.assertRaises(DispatchError):
            self.system.add_request("Mid", "Extreme")
        self.assertEqual(self.system.pending_count(), 0)


class TestReset(unittest.TestCase):
    def test_reset_restores_initial_state(self):
        system = build_line_system()
        system.add_request("Mid", "Critical")
        system.add_request("East", "Low")
        system.dispatch_next_request()
        system.complete_active_response()
        system.reset()

        self.assertEqual(system.requests, [])
        self.assertEqual(system.pending_count(), 0)
        self.assertFalse(system.has_active_response)
        self.assertEqual([(a.ambulance_id, a.location, a.available) for a in system.ambulances],
                         [("AMB-1", "West", True), ("AMB-2", "Hospital", True)])
        self.assertEqual(system.add_request("Mid", "Low").request_id, 1)   # numbering restarts


if __name__ == "__main__":
    unittest.main()
