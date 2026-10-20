# Emergency Ambulance Routing and Dispatch Optimization Using Graph Algorithms

> **Simulation only.** This is an academic mini-project for *Design and Analysis of Algorithms (DAA)*.
> It uses an imaginary city with invented distances. It is **not** a real emergency-response tool and
> never connects to real ambulances, GPS, live traffic or emergency services.

## 1. Project Overview

A Python desktop application (Tkinter) that simulates how an ambulance control room could
handle emergency calls on a small road network. It shows, in a working program, how a
**graph**, **Dijkstra's algorithm**, a **priority queue** and a **greedy strategy** solve a
practical problem.

## 2. Problem Statement

Given a city road network, several ambulances, hospitals and a stream of emergency requests of
different severity: which request should be served first, which ambulance should go, which route
should it take, and which hospital should the patient be taken to?

## 3. Project Objectives

- Represent a city as a weighted, undirected graph (adjacency list).
- Implement Dijkstra's algorithm manually with a `heapq` min-priority queue.
- Order emergency requests by severity, then by arrival time, with a priority queue.
- Assign the nearest available reachable ambulance (greedy choice).
- Recommend the nearest reachable hospital.
- Report the route, distance, measured runtime and a clearly defined operation count.
- Keep algorithm code, data, GUI and tests in separate modules.

## 4. Main Features

- Predefined sample city: 12 locations (3 are hospitals), 20 roads, 4 ambulances.
- Schematic map with distances on roads, hospital/ambulance symbols and highlighted routes.
- Emergency request form with validation (location + severity: Critical, High, Medium, Low).
- Request table, ambulance fleet table, results panel and timestamped activity log.
- Buttons: **Dispatch Next Request**, **Complete Response**, **Reset Simulation**.
  Invalid actions are disabled or rejected with a message.
- Works offline, window can be resized, standard library only.
- 39 automated `unittest` tests that do not need the GUI.

## 5. Technologies Used

| Purpose | Technology |
|---|---|
| Language | Python 3.10 or later |
| GUI | Tkinter with `ttk` |
| Graph | Adjacency list (Python dictionaries) |
| Shortest path | Dijkstra's algorithm (written by hand) |
| Priority queue | `heapq` |
| Tests | `unittest` |
| Version control | Git and GitHub |

## 6. Folder Structure

```text
Emergency_Ambulance_Routing_Dispatch/
│
├── main.py                  # entry point: builds the system and starts the GUI
├── ambulance_system.py      # requests, priority queue, greedy dispatch, hospital choice, reset
├── graph_algorithms.py      # Graph (adjacency list) + Dijkstra's algorithm
├── city_data.py             # sample city: locations, coordinates, roads, hospitals, ambulances
├── gui.py                   # Tkinter interface (no algorithm logic)
├── README.md
├── requirements.txt         # no external packages needed
├── .gitignore
│
└── tests/
    ├── __init__.py
    ├── test_dijkstra.py             # graph validation + Dijkstra + sample city
    ├── test_dispatch.py             # priority queue, dispatch rules, validation, reset
    └── test_hospital_selection.py   # hospital choice and completing a response
```

| File | Responsibility |
|---|---|
| `graph_algorithms.py` | `Graph` class, `dijkstra()`, `ShortestPathResult` |
| `ambulance_system.py` | `EmergencyPriorityQueue`, `AmbulanceDispatchSystem` and the rules |
| `city_data.py` | **Only file you edit** to change the city |
| `gui.py` | Draws the window; calls the core system; never re-implements Dijkstra or dispatch rules |

## 7. Installation Instructions (Windows)

1. **Install Python 3.10+** from <https://www.python.org/downloads/>. On the first installer screen
   tick **"Add python.exe to PATH"**, then choose *Install Now*. (Tkinter is included. If you pick
   *Customize installation*, keep **tcl/tk and IDLE** ticked.)
2. **Install VS Code** from <https://code.visualstudio.com/> and, inside VS Code, install the
   **Python** extension (Extensions icon on the left, search "Python", publisher Microsoft).
3. **Check Python** in a new terminal: `python --version` (or `py --version`).
4. No packages need installing: `requirements.txt` lists none.

## 8. Run the Application in VS Code

1. Unzip the project and in VS Code choose **File > Open Folder...** and select
   `Emergency_Ambulance_Routing_Dispatch`.
2. Press `Ctrl+Shift+P`, type **Python: Select Interpreter**, pick your Python 3.10+ installation.
3. Open the terminal with ``Ctrl+` `` (or **Terminal > New Terminal**). Make sure the path shown ends
   with `Emergency_Ambulance_Routing_Dispatch`.
4. *(Optional)* Virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
   If PowerShell blocks activation, run
   `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first. Skipping this step is fine,
   since the project has no dependencies.
5. Run:
   ```bash
   python main.py
   ```
   If `python` is not recognised, use `py main.py`.

### Troubleshooting

| Problem | Fix |
|---|---|
| `'python' is not recognized` | Re-run the installer and tick *Add python.exe to PATH*, or use `py` instead of `python`. Restart VS Code afterwards. |
| `No module named 'tkinter'` / `_tkinter` | Run the Python installer again > *Modify* > tick **tcl/tk and IDLE** > Install. |
| `ModuleNotFoundError: No module named 'graph_algorithms'` | The terminal is in the wrong folder. `cd` into the project folder (the one containing `main.py`). |
| Wrong interpreter shown in VS Code | `Ctrl+Shift+P` > *Python: Select Interpreter*. |
| Tests find no modules | Run the test command from the project root, not from inside `tests/`. |

## 9. Application Workflow

1. Start the app: the sample city loads, with the map, ambulances and hospitals shown.
2. Choose an **incident location** and a **severity**, then press **Add Request**. Repeat as needed.
   Pending requests get a dashed red ring on the map.
3. The request table lists every request with its severity, status and assigned ambulance.
4. Press **Dispatch Next Request**. The highest-priority pending request is picked, Dijkstra runs
   for every available ambulance, and the nearest reachable one is assigned.
5. The route to the incident is drawn in orange; the results panel shows the ambulance, route,
   distance, runtime and operation count. The ambulance turns grey (busy).
6. Press **Complete Response**. Dijkstra runs from the incident to every hospital; the nearest
   reachable one is chosen and its route is drawn in green.
7. The request becomes *Completed*; the ambulance moves to the hospital and is available again.
8. **Reset Simulation** restores the initial state.

**Limitation:** only **one active dispatch at a time** is supported. While a response is active the
Dispatch button is disabled and the system also rejects a second dispatch.

## 10. DAA Concepts Demonstrated

| Concept | Where |
|---|---|
| Graph representation (weighted, undirected, adjacency list) | `Graph` in `graph_algorithms.py` |
| Dijkstra's algorithm with a min-priority queue | `dijkstra()` |
| Priority queue / heap | `EmergencyPriorityQueue` (and the heap inside Dijkstra) |
| Greedy strategy | `AmbulanceDispatchSystem.dispatch_next_request()` |
| Nearest-facility selection | `choose_nearest_hospital()` |
| Complexity analysis and measurement | `ShortestPathResult.operations` and `.runtime_ms` |

## 11. Dijkstra's Algorithm: Explanation and Complexity

**Graph model.** Each location is a vertex. Each road is an undirected edge whose weight is its
length in km. The graph rejects zero, negative, non-numeric, NaN or infinite weights, so Dijkstra
only ever sees valid non-negative weights (it is not correct with negative weights).

**Idea.** Keep a "best known distance from the start" for every location (0 for the start,
infinity for the others) and a min-priority queue of `(distance, location)`.

1. Pop the queue entry with the smallest distance. If that location is already settled, skip it
   (a stale entry).
2. Mark it settled: with non-negative weights, its distance can no longer be improved.
3. For each neighbour, compute `distance_so_far + road_length`. If it is smaller than the neighbour's
   best known distance, update it, remember `previous[neighbour] = this location`, and push it.
4. Stop when the destination is settled. If the queue empties first, the destination is **unreachable**
   and the program reports that safely instead of crashing.
5. Rebuild the path by walking `previous` backwards from the destination, then reverse it.

**Why shortest is not always fewest edges.** In the sample city, `Railway Station -> Central Square`
has a direct 9 km road (1 edge), but `Railway Station -> Green Park -> Central Square` is 3 + 3 = 6 km
(2 edges). Dijkstra returns the 6 km route.

**Complexity.** With an adjacency list and a binary heap: **O((V + E) log V)** time and O(V + E)
space, where V = number of vertices and E = number of edges.

**Operation count used in this project:** `operations = heap pops + roads examined`. It is a simple
counter that shows how work grows with the graph. It is *not* a hardware measurement.

**Runtime.** Measured with `time.perf_counter()` for that single call and shown in milliseconds.
On a graph this small the numbers are tiny and vary from run to run, so a single reading proves
nothing about speed. Use the operation count and the O(...) analysis for reasoning.

## 12. Priority Queue and Greedy Dispatch

**Priority queue.** `EmergencyPriorityQueue` is a binary min-heap (`heapq`) of
`(severity_rank, arrival_order, request)`. Ranks: Critical = 1, High = 2, Medium = 3, Low = 4.
Smaller rank comes out first; for equal severity the smaller `arrival_order` (earlier request)
comes out first. Push and pop cost O(log n). It is independent of Dijkstra.

**Greedy ambulance assignment** (for the highest-priority pending request):

1. Collect all available ambulances.
2. Run Dijkstra from each ambulance's location to the incident.
3. Ignore unreachable ambulances.
4. Choose the smallest distance (ties keep the first ambulance in the fleet list).
5. Mark it busy and record the assignment.

This is **greedy**: it makes the best choice for the *current* request only. It does **not**
guarantee the best assignment across all future requests. For example, sending the nearest ambulance
now could leave a far-away area uncovered for the next call.

**Hospital selection.** After the simulated arrival, Dijkstra runs from the incident to every
hospital and the smallest reachable distance wins. Only road distance is used; hospital capacity,
speciality and real-time availability are **not** considered.

## 13. Testing

Run from the project root (the folder containing `main.py`):

```bash
python -m unittest discover -s tests -v
```

All tests should end with `OK`. They cover: correct shortest distances, valid paths, start and
destination, same start/destination, unreachable destinations, rejection of negative/zero/invalid
weights, Critical-before-lower priority, arrival order for equal severity, nearest-reachable
ambulance selection, busy ambulances not assigned, a blocked second dispatch, nearest-reachable
hospital selection, completing a response, input validation and reset.

## 14. Sample Use Case

Output below was produced by running the project's own code on the sample city.

Requests added in this order: **#1** Low at *Railway Station*, **#2** Critical at *University*,
**#3** High at *Green Park*. Priority order: #2, #3, #1.

| Step | Result |
|---|---|
| Dispatch #2 (Critical, University) | Distances: AMB-1 6 km, AMB-2 15, AMB-3 7, AMB-4 13. **AMB-1** wins: `North Market -> University`, 6.0 km |
| Complete #2 | Hospitals: City General 12 km, Riverside 18, Northside 2. **Northside Hospital**: `University -> Northside Hospital`, 2.0 km. AMB-1 is now at Northside Hospital |
| Dispatch #3 (High, Green Park) | AMB-1 15 km, AMB-2 5, AMB-3 10, AMB-4 11. **AMB-2** wins: `Old Town -> Green Park`, 5.0 km |
| Complete #3 | **City General Hospital**: `Green Park -> Central Square -> City General Hospital`, 6.0 km |
| Dispatch #1 (Low, Railway Station) | AMB-1 13, AMB-2 9 (now at City General), AMB-3 13, AMB-4 14. **AMB-2** wins: 9.0 km |

## 15. Assumptions and Limitations

- The city, distances and ambulance positions are invented and do not represent a real place.
- Distance is the only cost; there is no traffic, speed, travel time or road closure.
- Only one active dispatch at a time.
- The ambulance "teleports" to the incident when the response is completed; there is no animation.
- Hospitals are chosen only by distance (no capacity or speciality).
- Greedy assignment is locally good, not globally optimal.
- A request that cannot be served (no available or reachable ambulance) stays pending and a message is shown.
- Runtime values are single measurements and vary between runs.

## 16. Future Improvements

- Several simultaneous dispatches with ambulances travelling on the map.
- Travel time using road speeds instead of plain distance.
- Hospital capacity and speciality.
- Loading the city from a JSON file.
- Comparison with other shortest-path methods (for example A\* or Bellman-Ford) using operation counts.
- A BFS connectivity check to warn about disconnected locations.

## 17. How to Change the City

Edit only `city_data.py`: add a name and `(x, y)` to `LOCATION_COORDINATES`, add roads to `ROADS`,
add hospital names to `HOSPITALS`, or add ambulances to `AMBULANCE_START_LOCATIONS`. No algorithm
code needs to change. Roads must connect existing locations and have positive distances.

## 18. GitHub Upload Instructions

1. Create a GitHub account at <https://github.com> and sign in.
2. Click **+ > New repository**. Name it **`emergency-ambulance-routing-dispatch`**.
   Choose **Public** (so your teacher can open it without signing in). Do **not** tick
   *Add a README*, *.gitignore* or *license* (the project already has them). Click **Create repository**.
3. Install Git for Windows from <https://git-scm.com/download/win> if needed, then restart VS Code.
4. In the VS Code terminal, inside the project folder, set your identity once:
   ```bash
   git config --global user.name "YOUR NAME"
   git config --global user.email "YOUR_GITHUB_EMAIL"
   ```
5. Upload the project (replace `YOUR_GITHUB_USERNAME`):
   ```bash
   git init
   git add .
   git commit -m "Add emergency ambulance routing and dispatch mini-project"
   git branch -M main
   git remote add origin https://github.com/YOUR_GITHUB_USERNAME/emergency-ambulance-routing-dispatch.git
   git push -u origin main
   ```
   A browser window may ask you to sign in to GitHub the first time.
6. **Verify:** open `https://github.com/YOUR_GITHUB_USERNAME/emergency-ambulance-routing-dispatch`
   (use a private/incognito window to confirm it opens without login). You should see all `.py` files,
   the `tests` folder and this README rendered on the front page.
7. **Share:** copy the address bar URL and send it to your teacher.

To upload later changes: `git add .`, `git commit -m "Describe the change"`, `git push`.
