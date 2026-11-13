from source.simulation.simulation_data import SimulationData


class Simulation:
    def __init__(self):
        self.running: bool = False
        self.simulation_data: SimulationData = SimulationData()

    def start_simulation(self):
        self.running = True
        self._run()

    def pause_simulation(self):
        self.running = False

    def reset_simulation(self):
        self.running = False
        self.simulation_data.reset()

    def _run(self):
        while self.running:
            pass
