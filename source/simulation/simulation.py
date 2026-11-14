import threading
import time

from source.simulation.simulation_data import SimulationData


class Simulation:
    FPS = 60

    def __init__(self):
        self.running: bool = False
        self.simulation_data: SimulationData = SimulationData()
        self.lock = threading.Lock()

        self.frame_time = 1.0 / self.FPS
        self.fixed_dt = 1.0 / self.FPS
        self.max_frame_time = 0.25

    def start_simulation(self):
        self.running = True
        self._run()

    def pause_simulation(self):
        self.running = False

    def reset_simulation(self):
        self.running = False
        with self.lock:
            self.simulation_data.reset()

    def _run(self):
        physics_accumulator = 0.0
        last_time = time.perf_counter()

        while self.running:
            frame_start = time.perf_counter()
            real_dt = self._clamp_dt(frame_start - last_time)
            last_time = frame_start

            scaled_dt = real_dt * self.simulation_data.simulation_speed
            physics_accumulator = self._step_physics(physics_accumulator + scaled_dt)
            self._limit_fps(frame_start)

    def _clamp_dt(self, real_dt: float) -> float:
        return min(real_dt, self.max_frame_time)

    def _step_physics(self, accumulator: float) -> float:
        steps = 0
        while accumulator >= self.fixed_dt and steps < 20:
            with self.lock:
                self.simulation_data.process_instance_step(self.fixed_dt)
                if self.simulation_data.is_collision:
                    self.running = False
                    return 0.0
            accumulator -= self.fixed_dt
            steps += 1
        return accumulator

    def _limit_fps(self, frame_start: float):
        elapsed = time.perf_counter() - frame_start
        sleep_time = self.frame_time - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)
