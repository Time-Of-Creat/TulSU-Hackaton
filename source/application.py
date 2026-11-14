from source.simulation.simulation import Simulation
from source.view.ui.main_window import MainWindow
from source.view.controllers.simulation_controller import SimulationController


class Application:
    def __init__(self):
        self.backend: Simulation = Simulation()
        self.controller: SimulationController = SimulationController(backend=self.backend)
        self.frontend: MainWindow = MainWindow(controller=self.controller)
        self.window: MainWindow = self.frontend

        # ВАЖНО: связываем контроллер с обновлением UI
        self.controller.on_scene_changed = self.frontend.refresh_scene

        self.frontend.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        if getattr(self.backend, "running", False):
            self.backend.reset_simulation()
        self.frontend.destroy()

    def run(self):
        """
        Запускает оконное приложение.
        Графический интерфейс работает в основном потоке,
        а физическая симуляция управляется через контроллер в фоновом потоке.
        """
        self.frontend.mainloop()
