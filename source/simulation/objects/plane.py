from source.simulation.objects.object import Object


class Plane(Object):
    CAN_HAVE_CHILDREN = False
    CONSUME_ROTATION_FROM_PARENTS = False
    UI_ICON_COLOR = "#0000ff"

    def __init__(self, name: str, parent=None):
        super().__init__(name, parent)
        self.obj_type = "plane"
        self.icon = "📐"
        self.can_delete = True
        self.orientation = "XY"
        self.grid_step = 10.0
        self.grid_size = 100.0
        self.line_color = "#7A8288"
        self.is_visible = True

    @property
    def properties(self) -> dict:
        return {
            "name": self.name,
            "orientation": getattr(self, "orientation", "XY"),
            "grid_step": getattr(self, "grid_step", 10.0),
            "grid_size": getattr(self, "grid_size", 100.0),
            "line_color": getattr(self, "line_color", "#7A8288"),
            "is_visible": getattr(self, "is_visible", True),
            "pos_x": self.local_position.x,
            "pos_y": self.local_position.y,
            "rotation": self.local_rotation_deg,
        }
