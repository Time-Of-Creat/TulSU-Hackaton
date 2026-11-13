from source.simulation.objects.object import Object


class Planet(Object):
    CAN_HAVE_CHILDREN = False
    UI_ICON_COLOR = "#ff0000"
    def __init__(self, name: str):
        super().__init__(name)
