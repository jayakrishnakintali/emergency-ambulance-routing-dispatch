"""
gui.py
------
Tkinter interface. This file only DRAWS things and reacts to button clicks.
All real logic (Dijkstra, priority order, dispatch rules) lives in
graph_algorithms.py and ambulance_system.py.
"""

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from typing import List, Optional

from ambulance_system import (
    SEVERITY_LEVELS,
    AmbulanceDispatchSystem,
    CompletionResult,
    DispatchError,
    DispatchResult,
)
from city_data import LOCATION_COORDINATES, MAP_HEIGHT, MAP_WIDTH
from graph_algorithms import ShortestPathResult

# ---- colours used on the map ----
COLOR_ROAD = "#9aa5b1"
COLOR_NORMAL_NODE = "#4a90d9"
COLOR_HOSPITAL = "#2e9e5b"
COLOR_INCIDENT = "#d62828"
COLOR_INCIDENT_ROUTE = "#f77f00"
COLOR_HOSPITAL_ROUTE = "#1b8a3f"
COLOR_AMB_FREE = "#f4a261"
COLOR_AMB_BUSY = "#8d99ae"
COLOR_BACKGROUND = "#f7f9fb"


def format_route(path: List[str]) -> str:
    return " -> ".join(path)


def format_performance(route: ShortestPathResult) -> str:
    return f"{route.runtime_ms:.4f} ms measured, {route.operations} operations"


class AmbulanceDispatchApp:
    """Main window of the application."""

    def __init__(self, root: tk.Tk, system: AmbulanceDispatchSystem) -> None:
        self.root = root
        self.system = system
        # Routes currently highlighted on the map (lists of location names).
        self.incident_route: List[str] = []
        self.hospital_route: List[str] = []

        self.root.title("Emergency Ambulance Routing and Dispatch Optimization")
        self.root.geometry("1280x800")
        self.root.minsize(1100, 700)
        self.location_var = tk.StringVar()
        self.severity_var = tk.StringVar(value=SEVERITY_LEVELS[0])

        self._build_layout()
        self.log("Sample city loaded. This is a simulation, not a real emergency tool.")
        self.refresh_all()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build_layout(self) -> None:
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("Small.TLabel", font=("Segoe UI", 9))

        self.root.columnconfigure(0, weight=3)
        self.root.columnconfigure(1, weight=2)
        self.root.rowconfigure(1, weight=3)
        self.root.rowconfigure(2, weight=2)

        self._build_dashboard()
        self._build_map_panel()
        self._build_right_panel()
        self._build_bottom_panel()

    def _build_dashboard(self) -> None:
        frame = ttk.Frame(self.root, padding=(10, 8))
        frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttk.Label(frame, text="Emergency Ambulance Routing and Dispatch Optimization",
                  style="Title.TLabel").pack(anchor="w")
        ttk.Label(frame, style="Small.TLabel", wraplength=1200, text=(
            "Academic DAA simulation on an imaginary city. Nothing here connects to real "
            "ambulances, GPS, traffic or emergency services.")).pack(anchor="w")
        ttk.Label(frame, style="Small.TLabel", wraplength=1200, text=(
            "Algorithms: Dijkstra's shortest path (heapq min-priority queue) | emergency "
            "priority queue (severity, then arrival order) | greedy nearest-ambulance "
            "assignment | nearest-hospital selection.")).pack(anchor="w")

    def _build_map_panel(self) -> None:
        frame = ttk.LabelFrame(self.root, text="City Map (distances in km)", padding=4)
        frame.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=5)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(frame, background=COLOR_BACKGROUND, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        # Redraw whenever the window is resized so the map always fits.
        self.canvas.bind("<Configure>", lambda event: self.draw_map())

    def _build_right_panel(self) -> None:
        panel = ttk.Frame(self.root)
        panel.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=5)
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(2, weight=1)
        panel.rowconfigure(3, weight=1)

        # --- emergency request form ---
        form = ttk.LabelFrame(panel, text="New Emergency Request", padding=6)
        form.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        form.columnconfigure(1, weight=1)
        ttk.Label(form, text="Incident location:").grid(row=0, column=0, sticky="w", pady=2)
        self.location_combo = ttk.Combobox(form, textvariable=self.location_var, state="readonly",
                                           values=self.system.graph.locations())
        self.location_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        ttk.Label(form, text="Severity:").grid(row=1, column=0, sticky="w", pady=2)
        self.severity_combo = ttk.Combobox(form, textvariable=self.severity_var, state="readonly",
                                           values=SEVERITY_LEVELS)
        self.severity_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        self.add_button = ttk.Button(form, text="Add Request", command=self.on_add_request)
        self.add_button.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 0))

        # --- dispatch controls ---
        controls = ttk.LabelFrame(panel, text="Dispatch Controls", padding=6)
        controls.grid(row=1, column=0, sticky="ew", pady=5)
        controls.columnconfigure((0, 1, 2), weight=1)
        self.dispatch_button = ttk.Button(controls, text="Dispatch Next Request",
                                          command=self.on_dispatch)
        self.dispatch_button.grid(row=0, column=0, sticky="ew", padx=2)
        self.complete_button = ttk.Button(controls, text="Complete Response",
                                          command=self.on_complete)
        self.complete_button.grid(row=0, column=1, sticky="ew", padx=2)
        self.reset_button = ttk.Button(controls, text="Reset Simulation", command=self.on_reset)
        self.reset_button.grid(row=0, column=2, sticky="ew", padx=2)

        # --- request table ---
        request_frame = ttk.LabelFrame(panel, text="Emergency Requests", padding=4)
        request_frame.grid(row=2, column=0, sticky="nsew", pady=5)
        self.request_table = self._make_table(
            request_frame, ("id", "severity", "location", "status", "ambulance"),
            ("ID", "Severity", "Incident Location", "Status", "Ambulance"),
            (40, 70, 140, 90, 80))

        # --- fleet table ---
        fleet_frame = ttk.LabelFrame(panel, text="Ambulance Fleet", padding=4)
        fleet_frame.grid(row=3, column=0, sticky="nsew", pady=(5, 0))
        self.fleet_table = self._make_table(
            fleet_frame, ("id", "location", "status"),
            ("Ambulance", "Current Location", "Status"), (80, 180, 90))

    @staticmethod
    def _make_table(parent: ttk.Frame, columns, headings, widths) -> ttk.Treeview:
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        table = ttk.Treeview(parent, columns=columns, show="headings", height=4)
        for column, heading, width in zip(columns, headings, widths):
            table.heading(column, text=heading)
            table.column(column, width=width, stretch=True)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=scrollbar.set)
        table.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        return table

    def _build_bottom_panel(self) -> None:
        frame = ttk.Frame(self.root)
        frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 10))
        frame.columnconfigure((0, 1), weight=1)
        frame.rowconfigure(0, weight=1)
        self.results_text = self._make_text_box(frame, "Results and Algorithm Performance", 0)
        self.log_text = self._make_text_box(frame, "Activity Log", 1)

    @staticmethod
    def _make_text_box(parent: ttk.Frame, title: str, column: int) -> tk.Text:
        box = ttk.LabelFrame(parent, text=title, padding=4)
        box.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 5, 5 if column == 0 else 0))
        box.rowconfigure(0, weight=1)
        box.columnconfigure(0, weight=1)
        text = tk.Text(box, height=8, wrap="word", state="disabled", font=("Consolas", 10))
        scrollbar = ttk.Scrollbar(box, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        return text

    # ------------------------------------------------------------------
    # Button handlers (they call the core system, then refresh the screen)
    # ------------------------------------------------------------------
    def on_add_request(self) -> None:
        try:
            request = self.system.add_request(self.location_var.get(), self.severity_var.get())
        except DispatchError as error:
            messagebox.showwarning("Cannot add request", str(error))
            return
        self.log(f"Request #{request.request_id} added: {request.severity} at {request.location}.")
        self.refresh_all()

    def on_dispatch(self) -> None:
        try:
            result = self.system.dispatch_next_request()
        except DispatchError as error:
            messagebox.showwarning("Cannot dispatch", str(error))
            self.log(f"Dispatch rejected: {error}")
            self.refresh_all()
            return
        self.incident_route = result.route.path
        self.hospital_route = []
        self.show_dispatch_result(result)
        self.log(f"Request #{result.request.request_id} dispatched: {result.ambulance.ambulance_id} "
                 f"travels {result.route.distance_km:.1f} km to {result.request.location}.")
        self.refresh_all()

    def on_complete(self) -> None:
        try:
            result = self.system.complete_active_response()
        except DispatchError as error:
            messagebox.showwarning("Cannot complete response", str(error))
            self.log(f"Completion rejected: {error}")
            self.refresh_all()
            return
        self.hospital_route = result.route.path
        self.show_completion_result(result)
        self.log(f"Request #{result.request.request_id} completed: {result.ambulance.ambulance_id} "
                 f"took the patient to {result.hospital_name} ({result.route.distance_km:.1f} km).")
        self.refresh_all()

    def on_reset(self) -> None:
        self.system.reset()
        self.incident_route = []
        self.hospital_route = []
        self.set_results("")
        self.log("Simulation reset to the initial state.")
        self.refresh_all()

    # ------------------------------------------------------------------
    # Result text
    # ------------------------------------------------------------------
    def show_dispatch_result(self, result: DispatchResult) -> None:
        request, route = result.request, result.route
        lines = [
            f"DISPATCH: Request #{request.request_id} ({request.severity}) at {request.location}",
            f"Selected ambulance : {result.ambulance.ambulance_id} (from {route.start})",
            f"Route to incident  : {format_route(route.path)}",
            f"Distance           : {route.distance_km:.1f} km",
            f"Latest Dijkstra run: {format_performance(route)}",
            "",
            "Available ambulances checked (greedy: smallest distance wins):",
        ]
        for ambulance_id, candidate in result.candidates:
            if candidate.reachable:
                lines.append(f"  {ambulance_id}: {candidate.distance_km:.1f} km "
                             f"({candidate.operations} operations)")
            else:
                lines.append(f"  {ambulance_id}: unreachable (ignored)")
        lines += ["", "Press 'Complete Response' to pick the nearest hospital."]
        self.set_results("\n".join(lines))

    def show_completion_result(self, result: CompletionResult) -> None:
        route = result.route
        lines = [
            f"COMPLETED: Request #{result.request.request_id} handled by {result.ambulance.ambulance_id}",
            f"Nearest hospital   : {result.hospital_name}",
            f"Route to hospital  : {format_route(route.path)}",
            f"Distance           : {route.distance_km:.1f} km",
            f"Latest Dijkstra run: {format_performance(route)}",
            "",
            "Hospitals checked (distance only; capacity and speciality are NOT considered):",
        ]
        for hospital_name, candidate in result.candidates:
            if candidate.reachable:
                lines.append(f"  {hospital_name}: {candidate.distance_km:.1f} km")
            else:
                lines.append(f"  {hospital_name}: unreachable (ignored)")
        lines += ["", f"{result.ambulance.ambulance_id} is now at {result.hospital_name} and available."]
        self.set_results("\n".join(lines))

    def set_results(self, text: str) -> None:
        self._write_text(self.results_text, text, replace=True)

    def log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._write_text(self.log_text, f"[{timestamp}] {message}\n", replace=False)

    @staticmethod
    def _write_text(widget: tk.Text, text: str, replace: bool) -> None:
        widget.configure(state="normal")
        if replace:
            widget.delete("1.0", "end")
        widget.insert("end", text)
        # Results box starts at the top; the log box follows the newest line.
        widget.see("1.0" if replace else "end")
        widget.configure(state="disabled")

    # ------------------------------------------------------------------
    # Refreshing the screen
    # ------------------------------------------------------------------
    def refresh_all(self) -> None:
        self.refresh_tables()
        self.refresh_buttons()
        self.draw_map()

    def refresh_tables(self) -> None:
        for table in (self.request_table, self.fleet_table):
            table.delete(*table.get_children())
        for request in self.system.requests:
            self.request_table.insert("", "end", values=(
                request.request_id, request.severity, request.location,
                request.status, request.assigned_ambulance_id or "-"))
        for ambulance in self.system.ambulances:
            self.fleet_table.insert("", "end", values=(
                ambulance.ambulance_id, ambulance.location,
                "Available" if ambulance.available else "Busy"))

    def refresh_buttons(self) -> None:
        """Disable actions that are not valid right now."""
        active = self.system.has_active_response
        can_dispatch = (not active) and self.system.pending_count() > 0
        self.dispatch_button.configure(state="normal" if can_dispatch else "disabled")
        self.complete_button.configure(state="normal" if active else "disabled")

    # ------------------------------------------------------------------
    # Map drawing
    # ------------------------------------------------------------------
    def draw_map(self) -> None:
        canvas = self.canvas
        canvas.delete("all")
        width, height = canvas.winfo_width(), canvas.winfo_height()
        if width < 50 or height < 50:
            return                                   # window not ready yet
        margin = 50
        scale = min((width - 2 * margin) / MAP_WIDTH, (height - 2 * margin) / MAP_HEIGHT)
        offset_x = (width - MAP_WIDTH * scale) / 2
        offset_y = (height - MAP_HEIGHT * scale) / 2

        def to_screen(location: str):
            map_x, map_y = LOCATION_COORDINATES[location]
            return offset_x + map_x * scale, offset_y + map_y * scale

        radius = max(10, 16 * scale)
        self._draw_roads(to_screen)
        self._draw_route(self.incident_route, COLOR_INCIDENT_ROUTE, to_screen)
        self._draw_route(self.hospital_route, COLOR_HOSPITAL_ROUTE, to_screen)
        self._draw_road_labels(to_screen)
        self._draw_locations(to_screen, radius)
        self._draw_ambulances(to_screen, radius)
        self._draw_legend()

    def _draw_roads(self, to_screen) -> None:
        for location_a, location_b, _distance in self.system.graph.roads():
            x1, y1 = to_screen(location_a)
            x2, y2 = to_screen(location_b)
            self.canvas.create_line(x1, y1, x2, y2, fill=COLOR_ROAD, width=2)

    def _draw_road_labels(self, to_screen) -> None:
        """Distance labels are drawn last so highlighted routes never hide them."""
        for location_a, location_b, distance in self.system.graph.roads():
            x1, y1 = to_screen(location_a)
            x2, y2 = to_screen(location_b)
            label = self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=f"{distance:g}",
                                            font=("Segoe UI", 9, "bold"), fill="#333")
            background = self.canvas.create_rectangle(self.canvas.bbox(label), fill=COLOR_BACKGROUND, outline="")
            self.canvas.tag_lower(background, label)

    def _draw_route(self, path: List[str], color: str, to_screen) -> None:
        for location_a, location_b in zip(path, path[1:]):
            x1, y1 = to_screen(location_a)
            x2, y2 = to_screen(location_b)
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=6, capstyle="round")

    def _draw_locations(self, to_screen, radius: float) -> None:
        active = self.system.active_request
        pending_locations = {request.location for request in self.system.pending_in_priority_order()}
        for location in LOCATION_COORDINATES:
            x, y = to_screen(location)
            if location in self.system.hospital_names:
                self.canvas.create_rectangle(x - radius, y - radius, x + radius, y + radius,
                                             fill=COLOR_HOSPITAL, outline="white", width=2)
                self.canvas.create_text(x, y, text="H", fill="white", font=("Segoe UI", 11, "bold"))
            else:
                self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius,
                                        fill=COLOR_NORMAL_NODE, outline="white", width=2)
            if location in pending_locations:       # dashed ring = waiting request
                ring = radius + 6
                self.canvas.create_oval(x - ring, y - ring, x + ring, y + ring,
                                        outline=COLOR_INCIDENT, width=2, dash=(4, 3))
            if active is not None and active.location == location:   # solid ring = active incident
                ring = radius + 7
                self.canvas.create_oval(x - ring, y - ring, x + ring, y + ring,
                                        outline=COLOR_INCIDENT, width=4)
            self.canvas.create_text(x, y + radius + 11, text=location, font=("Segoe UI", 9))

    def _draw_ambulances(self, to_screen, radius: float) -> None:
        slot_by_location = {}                         # stack several ambulances at one place
        for ambulance in self.system.ambulances:
            slot = slot_by_location.get(ambulance.location, 0)
            slot_by_location[ambulance.location] = slot + 1
            x, y = to_screen(ambulance.location)
            top = y - radius - 20 - slot * 18
            color = COLOR_AMB_FREE if ambulance.available else COLOR_AMB_BUSY
            self.canvas.create_rectangle(x - 26, top, x + 26, top + 16, fill=color, outline="#333")
            self.canvas.create_text(x, top + 8, text=ambulance.ambulance_id, font=("Segoe UI", 8, "bold"))

    def _draw_legend(self) -> None:
        items = [
            (COLOR_NORMAL_NODE, "Location"), (COLOR_HOSPITAL, "Hospital (H)"),
            (COLOR_AMB_FREE, "Ambulance (available)"), (COLOR_AMB_BUSY, "Ambulance (busy)"),
            (COLOR_INCIDENT_ROUTE, "Route to incident"), (COLOR_HOSPITAL_ROUTE, "Route to hospital"),
            (COLOR_INCIDENT, "Solid ring: active incident"),
            (COLOR_INCIDENT, "Dashed ring: pending request"),
        ]
        for index, (color, text) in enumerate(items):
            y = 12 + index * 16
            self.canvas.create_rectangle(8, y, 20, y + 11, fill=color, outline="")
            self.canvas.create_text(26, y + 6, text=text, anchor="w", font=("Segoe UI", 8))
