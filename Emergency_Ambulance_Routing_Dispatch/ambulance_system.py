"""
ambulance_system.py
-------------------
Core (non-GUI) logic of the simulation:
  * emergency requests and the severity priority queue
  * greedy ambulance assignment using Dijkstra distances
  * hospital selection and completing a response
  * reset

The GUI only calls the methods of AmbulanceDispatchSystem.
"""

import heapq
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from graph_algorithms import Graph, ShortestPathResult, dijkstra

# Lower number = more urgent. This dictionary IS the priority rule.
SEVERITY_RANK: Dict[str, int] = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4}
SEVERITY_LEVELS: List[str] = list(SEVERITY_RANK.keys())

STATUS_PENDING = "Pending"
STATUS_DISPATCHED = "Dispatched"
STATUS_COMPLETED = "Completed"


class DispatchError(Exception):
    """Raised for invalid actions (bad input, no ambulance, response already active...)."""


@dataclass
class Ambulance:
    ambulance_id: str
    location: str
    available: bool = True


@dataclass
class EmergencyRequest:
    request_id: int
    location: str
    severity: str
    arrival_order: int                      # 1, 2, 3... in the order requests arrive
    status: str = STATUS_PENDING
    assigned_ambulance_id: Optional[str] = None
    hospital_name: Optional[str] = None


@dataclass
class DispatchResult:
    """What happened when a request was dispatched."""
    request: EmergencyRequest
    ambulance: Ambulance
    route: ShortestPathResult                                   # ambulance -> incident
    candidates: List[Tuple[str, ShortestPathResult]]            # every ambulance that was checked


@dataclass
class CompletionResult:
    """What happened when the response was completed."""
    request: EmergencyRequest
    ambulance: Ambulance
    hospital_name: str
    route: ShortestPathResult                                   # incident -> hospital
    candidates: List[Tuple[str, ShortestPathResult]]            # every hospital that was checked


class EmergencyPriorityQueue:
    """
    Min-heap of pending requests (Python heapq).

    Each heap entry is (severity_rank, arrival_order, request):
      * smaller severity_rank (Critical = 1) comes out first
      * if severity is equal, smaller arrival_order (earlier request) comes out first
    arrival_order is unique, so two entries never tie completely and Python never
    has to compare the request objects themselves.

    Push / pop cost O(log n); peek is O(1). This class does not use Dijkstra.
    """

    def __init__(self) -> None:
        self._heap: List[Tuple[int, int, EmergencyRequest]] = []

    def push(self, request: EmergencyRequest) -> None:
        heapq.heappush(self._heap, (SEVERITY_RANK[request.severity], request.arrival_order, request))

    def peek(self) -> Optional[EmergencyRequest]:
        """Look at the next request without removing it (None if empty)."""
        return self._heap[0][2] if self._heap else None

    def pop(self) -> EmergencyRequest:
        """Remove and return the next request."""
        if not self._heap:
            raise DispatchError("There are no pending emergency requests.")
        return heapq.heappop(self._heap)[2]

    def is_empty(self) -> bool:
        return not self._heap

    def __len__(self) -> int:
        return len(self._heap)

    def clear(self) -> None:
        self._heap.clear()

    def in_priority_order(self) -> List[EmergencyRequest]:
        """Pending requests sorted by priority (for display; does not change the heap)."""
        return [entry[2] for entry in sorted(self._heap)]


class AmbulanceDispatchSystem:
    """Runs the whole simulation. Handles ONE active dispatch at a time."""

    def __init__(self, graph: Graph, ambulances: List[Ambulance], hospital_names: List[str]) -> None:
        self._validate_setup(graph, ambulances, hospital_names)
        self.graph = graph
        self.hospital_names = list(hospital_names)
        # Remember the starting positions so reset() can restore them.
        self._initial_positions = [(a.ambulance_id, a.location) for a in ambulances]
        self.ambulances: List[Ambulance] = []
        self.requests: List[EmergencyRequest] = []
        self._queue = EmergencyPriorityQueue()
        self._next_request_id = 1
        self._active_request: Optional[EmergencyRequest] = None
        self._active_ambulance: Optional[Ambulance] = None
        self.reset()

    # ---------- setup / reset ----------
    @staticmethod
    def _validate_setup(graph: Graph, ambulances: List[Ambulance], hospital_names: List[str]) -> None:
        if not hospital_names:
            raise DispatchError("At least one hospital is required.")
        for name in hospital_names:
            if not graph.has_location(name):
                raise DispatchError(f"Hospital '{name}' is not a location in the city graph.")
        if not ambulances:
            raise DispatchError("At least one ambulance is required.")
        seen_ids = set()
        for ambulance in ambulances:
            if ambulance.ambulance_id in seen_ids:
                raise DispatchError(f"Duplicate ambulance id: {ambulance.ambulance_id}.")
            seen_ids.add(ambulance.ambulance_id)
            if not graph.has_location(ambulance.location):
                raise DispatchError(
                    f"Ambulance {ambulance.ambulance_id} starts at unknown location '{ambulance.location}'."
                )

    def reset(self) -> None:
        """Restore the initial simulation state."""
        self.ambulances = [Ambulance(ambulance_id, location, True)
                           for ambulance_id, location in self._initial_positions]
        self.requests = []
        self._queue.clear()
        self._next_request_id = 1
        self._active_request = None
        self._active_ambulance = None

    # ---------- simple queries ----------
    @property
    def has_active_response(self) -> bool:
        return self._active_request is not None

    @property
    def active_request(self) -> Optional[EmergencyRequest]:
        return self._active_request

    @property
    def active_ambulance(self) -> Optional[Ambulance]:
        return self._active_ambulance

    def pending_count(self) -> int:
        return len(self._queue)

    def next_pending_request(self) -> Optional[EmergencyRequest]:
        return self._queue.peek()

    def pending_in_priority_order(self) -> List[EmergencyRequest]:
        return self._queue.in_priority_order()

    def available_ambulances(self) -> List[Ambulance]:
        return [ambulance for ambulance in self.ambulances if ambulance.available]

    # ---------- step 1: add a request ----------
    def add_request(self, location: str, severity: str) -> EmergencyRequest:
        if not location or not self.graph.has_location(location):
            raise DispatchError("Please choose a valid incident location.")
        if severity not in SEVERITY_RANK:
            raise DispatchError("Please choose a severity: " + ", ".join(SEVERITY_LEVELS) + ".")
        request = EmergencyRequest(
            request_id=self._next_request_id,
            location=location,
            severity=severity,
            arrival_order=self._next_request_id,
        )
        self._next_request_id += 1
        self.requests.append(request)
        self._queue.push(request)
        return request

    # ---------- step 2: dispatch (greedy ambulance assignment) ----------
    def dispatch_next_request(self) -> DispatchResult:
        """
        Take the highest-priority pending request and assign the available
        ambulance with the smallest shortest-path distance to the incident.

        GREEDY: we pick what is best for THIS request right now. This does not
        guarantee the best overall assignment for all future requests.
        """
        if self.has_active_response:
            raise DispatchError("A response is already active. Complete it before dispatching another.")
        request = self._queue.peek()
        if request is None:
            raise DispatchError("There are no pending emergency requests.")
        free_ambulances = self.available_ambulances()
        if not free_ambulances:
            raise DispatchError("No ambulance is available right now.")

        # Run Dijkstra once per available ambulance.
        candidates: List[Tuple[str, ShortestPathResult]] = []
        best_ambulance: Optional[Ambulance] = None
        best_route: Optional[ShortestPathResult] = None
        for ambulance in free_ambulances:
            route = dijkstra(self.graph, ambulance.location, request.location)
            candidates.append((ambulance.ambulance_id, route))
            if not route.reachable:
                continue                                  # ignore unreachable ambulances
            if best_route is None or route.distance_km < best_route.distance_km:
                best_ambulance, best_route = ambulance, route   # strict "<": ties keep the first

        if best_ambulance is None or best_route is None:
            # The request stays in the queue so nothing is lost.
            raise DispatchError("No available ambulance can reach the incident location.")

        self._queue.pop()                                 # now it is really dispatched
        best_ambulance.available = False
        request.status = STATUS_DISPATCHED
        request.assigned_ambulance_id = best_ambulance.ambulance_id
        self._active_request = request
        self._active_ambulance = best_ambulance
        return DispatchResult(request, best_ambulance, best_route, candidates)

    # ---------- step 3: complete (hospital selection) ----------
    def choose_nearest_hospital(self, incident_location: str) -> Tuple[str, ShortestPathResult, List[Tuple[str, ShortestPathResult]]]:
        """Run Dijkstra from the incident to every hospital and pick the closest reachable one."""
        candidates: List[Tuple[str, ShortestPathResult]] = []
        best_name: Optional[str] = None
        best_route: Optional[ShortestPathResult] = None
        for hospital_name in self.hospital_names:
            route = dijkstra(self.graph, incident_location, hospital_name)
            candidates.append((hospital_name, route))
            if not route.reachable:
                continue
            if best_route is None or route.distance_km < best_route.distance_km:
                best_name, best_route = hospital_name, route
        if best_name is None or best_route is None:
            raise DispatchError("No hospital can be reached from the incident location.")
        return best_name, best_route, candidates

    def complete_active_response(self) -> CompletionResult:
        """
        The ambulance has reached the incident. Find the nearest reachable
        hospital, move the ambulance there, mark it available and finish the request.
        """
        if not self.has_active_response or self._active_request is None or self._active_ambulance is None:
            raise DispatchError("There is no active response to complete.")
        request = self._active_request
        ambulance = self._active_ambulance

        hospital_name, route, candidates = self.choose_nearest_hospital(request.location)

        request.status = STATUS_COMPLETED
        request.hospital_name = hospital_name
        ambulance.location = hospital_name
        ambulance.available = True
        self._active_request = None
        self._active_ambulance = None
        return CompletionResult(request, ambulance, hospital_name, route, candidates)
