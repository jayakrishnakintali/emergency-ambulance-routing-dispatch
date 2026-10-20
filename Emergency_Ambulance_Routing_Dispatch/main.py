"""
main.py
-------
Entry point:  python main.py
Builds the sample city, creates the dispatch system and starts the GUI.
"""

import sys

from ambulance_system import Ambulance, AmbulanceDispatchSystem
from city_data import AMBULANCE_START_LOCATIONS, HOSPITALS, build_sample_graph


def create_sample_system() -> AmbulanceDispatchSystem:
    """Create the dispatch system from the data in city_data.py."""
    graph = build_sample_graph()
    ambulances = [Ambulance(ambulance_id, location)
                  for ambulance_id, location in AMBULANCE_START_LOCATIONS.items()]
    return AmbulanceDispatchSystem(graph, ambulances, HOSPITALS)


def main() -> None:
    try:
        import tkinter as tk
        from gui import AmbulanceDispatchApp
    except ImportError as error:
        print("Could not start the GUI:", error)
        print("Tkinter is part of the standard Python installer on Windows.")
        print("Re-run the Python installer, choose 'Modify' and tick 'tcl/tk and IDLE'.")
        sys.exit(1)

    root = tk.Tk()
    AmbulanceDispatchApp(root, create_sample_system())
    root.mainloop()


if __name__ == "__main__":
    main()
