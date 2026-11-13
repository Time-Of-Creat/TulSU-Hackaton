import math


class Coords2:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def get_dist(self, other_coord):
        dx = self.x - other_coord.x
        dy = self.y - other_coord.y
        return (dx*dx + dy*dy)**(1/2)

    def rotate(self, angle_deg: float):
        angle_rad = math.radians(angle_deg)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        new_x = self.x * cos_a - self.y * sin_a
        new_y = self.x * sin_a + self.y * cos_a

        return Coords2(new_x, new_y)

    def __add__(self, other):
        if isinstance(other, Coords2):
            return Coords2(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        if isinstance(other, Coords2):
            return Coords2(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return Coords2(self.x * other, self.y * other)

    def __rmul__(self, other: float):
        return self.__mul__(other)

    def __truediv__(self, scalar: float):
        if isinstance(scalar, (int, float)):
            return Coords2(self.x / scalar, self.y / scalar)
