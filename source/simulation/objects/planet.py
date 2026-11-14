import math

from source.simulation.objects.object import Object
from .builtin_types.coords2 import Coords2

G = 6.674e-11


class Planet(Object):
    CAN_HAVE_CHILDREN = True
    UI_ICON_COLOR = "#ff0000"

    def __init__(self, name: str, mass: float = 1, parent=None):
        super().__init__(name, parent)

        self.mass = mass
        self.density = 1.0

        self.F = Coords2(0, 0)
        self.acceleration = Coords2(0, 0)
        self.velocity = Coords2(0, 0)
        self.obj_type = "planet"
        self.icon = "🌍"
        self.can_delete = False
        self.color = "#4A90E2"
        self.is_fixed = False

    @property
    def properties(self) -> dict:
        return {
            "name": self.name,
            "mass": self.mass,
            "density": getattr(self, "density", 1.0),
            "radius": self.calculate_radius(),
            "pos_x": self.local_position.x,
            "pos_y": self.local_position.y,
            "pos_z": 0.0,
            "vel_x": self.velocity.x,
            "vel_y": self.velocity.y,
            "vel_z": 0.0,
            "color": getattr(self, "color", "#4A90E2"),
            "is_fixed": getattr(self, "is_fixed", False),
        }

    def process_step(self, dt: float):
        super().process_step(dt)

        if getattr(self, "is_fixed", False):
            self.velocity = Coords2(0, 0)
            self.acceleration = Coords2(0, 0)
            self.F = Coords2(0, 0)
            return

        if self.mass != 0:
            self.acceleration = self.F / self.mass
        else:
            self.acceleration = Coords2(0, 0)

        self.velocity += self.acceleration * dt
        self.local_position += self.velocity * dt

        self.F = Coords2(0, 0)

    def calculate_radius(self):
        density = getattr(self, "density", 1.0)
        if density <= 0:
            density = 1.0
        volume = self.mass / density
        return (3 * volume / (4 * math.pi)) ** (1 / 3)

    def calculate_gravity(self, other_planet):
        p1 = self.get_global_position()
        p2 = other_planet.get_global_position()

        r = p1.get_dist(p2)
        if r == 0:
            return

        d = p2 - p1
        f = G * self.mass * other_planet.mass / (r * r)

        self.F = self.F + Coords2(f * d.x / r, f * d.y / r)
