from source.simulation.objects.object import Object


class Plane(Object):
    UI_ICON_COLOR = "#0000ff"
    def __init__(self, name: str):
        super().__init__(name)
