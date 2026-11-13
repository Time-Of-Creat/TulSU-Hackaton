from source.simulation.objects.object import Object


class Plane(Object):
    CAN_HAVE_CHILDREN = False
    CONSUME_ROTATION_FROM_PARENTS = False
    UI_ICON_COLOR = "#0000ff"

    def __init__(self, name: str, parent=None):
        super().__init__(name, parent)
