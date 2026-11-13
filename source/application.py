from source.simulation.simulation import Simulation


class Application:
    def __init__(self):
        self.backend: Simulation = Simulation()

    def run(self):
        # Эта функция должна запускать оконное приложение и логику симуляции одновременно (по идее в два потока)
        pass
