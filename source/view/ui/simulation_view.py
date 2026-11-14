import math
import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List, Optional


class SimulationView(ttk.Frame):
    """Центральное поле визуализации объектов текущей симуляции.

    Виджет только читает состояние backend и рисует его на Canvas.
    Физика и изменение объектов выполняются backend-потоком.
    """

    REFRESH_INTERVAL_MS = 33
    BACKGROUND = "#1e1e24"
    GRID_COLOR = "#282832"
    AXIS_COLOR = "#6c757d"
    TEXT_COLOR = "#d9d9df"

    def __init__(self, parent, backend: Optional[Any] = None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.backend = backend
        self._last_snapshot: List[Dict[str, Any]] = []
        self._refresh_job = None
        self._build_ui()
        self._schedule_refresh()

    def _build_ui(self):
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=4, pady=(4, 2))

        ttk.Label(
            header_frame,
            text="Сектор симуляции",
            font=("Segoe UI", 9, "bold")
        ).pack(side=tk.LEFT)

        self.status_label = ttk.Label(
            header_frame,
            text="Статус: ожидание данных",
            font=("Segoe UI", 8, "italic")
        )
        self.status_label.pack(side=tk.RIGHT)

        self.canvas = tk.Canvas(
            self,
            background=self.BACKGROUND,
            highlightthickness=1,
            highlightbackground="#3a3a44"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)
        self.canvas.bind("<Configure>", self._on_resize)

    def _schedule_refresh(self):
        self._refresh_job = self.after(self.REFRESH_INTERVAL_MS, self._refresh)

    def _refresh(self):
        self._last_snapshot = self._read_backend_snapshot()
        self._draw_scene(self._last_snapshot)
        self._schedule_refresh()

    def _read_backend_snapshot(self) -> List[Dict[str, Any]]:
        """Снимает короткую копию данных под lock, не меняя backend."""
        if self.backend is None:
            return []

        simulation_data = getattr(self.backend, "simulation_data", None)
        instance = getattr(simulation_data, "instance", None)
        if instance is None:
            return []

        lock = getattr(self.backend, "lock", None)
        if lock is None:
            return self._snapshot_objects(instance)

        with lock:
            return self._snapshot_objects(instance)

    def _snapshot_objects(self, instance) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []

        def visit(obj):
            get_position = getattr(obj, "get_global_position", None)
            if callable(get_position):
                position = get_position()
            else:
                position = getattr(obj, "local_position", None)
            if position is not None:
                item = {
                    "name": str(getattr(obj, "name", obj.__class__.__name__)),
                    "type": obj.__class__.__name__.lower(),
                    "x": self._number(getattr(position, "x", 0.0)),
                    "y": self._number(getattr(position, "y", 0.0)),
                    "mass": self._number(getattr(obj, "mass", 0.0)),
                    "radius": self._calculate_radius(obj),
                }
                result.append(item)

            for child in list(getattr(obj, "children", []) or []):
                visit(child)

        for obj in list(getattr(instance, "objects", []) or []):
            visit(obj)

        return result

    @staticmethod
    def _number(value: Any) -> float:
        try:
            number = float(value)
            return number if math.isfinite(number) else 0.0
        except (TypeError, ValueError, OverflowError):
            return 0.0

    @classmethod
    def _calculate_radius(cls, obj: Any) -> float:
        calculate_radius = getattr(obj, "calculate_radius", None)
        if not callable(calculate_radius):
            return 0.0
        try:
            return max(cls._number(calculate_radius()), 0.0)
        except (TypeError, ValueError, ZeroDivisionError):
            return 0.0

    def _on_resize(self, _event=None):
        self._draw_scene(self._last_snapshot)

    def _draw_scene(self, objects: List[Dict[str, Any]]):
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        self.canvas.delete("all")

        cx, cy = width / 2, height / 2
        self._draw_grid(width, height, cx, cy)

        planets = [obj for obj in objects if obj["type"] == "planet"]
        drawable_objects = [obj for obj in objects if obj["type"] in ("planet", "plane")]
        max_coordinate = max(
            [max(abs(obj["x"]), abs(obj["y"])) for obj in drawable_objects] or [50.0]
        )
        coordinate_limit = max(max_coordinate * 1.25, 50.0)
        scale = min(width, height) * 0.42 / coordinate_limit

        self._draw_planes(objects, width, height, cx, cy, scale, coordinate_limit)

        max_radius = max([planet["radius"] for planet in planets] or [1.0])
        for index, planet in enumerate(planets):
            self._draw_planet(planet, index, cx, cy, scale, max_radius)

        if not objects:
            self.canvas.create_text(
                cx, cy,
                text="ОЖИДАНИЕ ОБЪЕКТОВ СИМУЛЯЦИИ",
                fill="#9a9aa8",
                font=("Segoe UI", 10, "bold")
            )
            self.status_label.configure(text="Статус: нет объектов")
        else:
            self.status_label.configure(
                text=f"Объектов визуализации: {len(objects)}"
            )

    def _draw_grid(self, width, height, cx, cy):
        step = 40
        for x in range(0, int(width) + step, step):
            self.canvas.create_line(x, 0, x, height, fill=self.GRID_COLOR)
        for y in range(0, int(height) + step, step):
            self.canvas.create_line(0, y, width, y, fill=self.GRID_COLOR)

    def _draw_axes(self, width, height, cx, cy, coordinate_limit, scale):
        self.canvas.create_line(0, cy, width, cy, fill=self.AXIS_COLOR, arrow=tk.LAST)
        self.canvas.create_line(cx, height, cx, 0, fill=self.AXIS_COLOR, arrow=tk.LAST)
        self.canvas.create_text(width - 14, cy - 12, text="X", fill=self.TEXT_COLOR)
        self.canvas.create_text(cx + 12, 12, text="Y", fill=self.TEXT_COLOR)
        self.canvas.create_text(
            cx + 8, cy + 14, text="0", fill="#8e8e98", anchor=tk.NW
        )

        tick_step = self._nice_tick(coordinate_limit / 4)
        tick = tick_step
        while tick < coordinate_limit:
            offset = tick * scale
            for sign in (-1, 1):
                dx = cx + sign * offset
                dy = cy - sign * offset
                self.canvas.create_line(dx, cy - 3, dx, cy + 3, fill=self.AXIS_COLOR)
                self.canvas.create_line(cx - 3, dy, cx + 3, dy, fill=self.AXIS_COLOR)
                self.canvas.create_text(dx, cy + 7, text=self._format_number(sign * tick),
                                        fill="#8e8e98", anchor=tk.N)
                self.canvas.create_text(cx + 7, dy, text=self._format_number(sign * tick),
                                        fill="#8e8e98", anchor=tk.W)
            tick += tick_step

    @staticmethod
    def _nice_tick(value: float) -> float:
        if value <= 0:
            return 1.0
        power = 10 ** math.floor(math.log10(value))
        normalized = value / power
        multiplier = 1 if normalized < 2 else 2 if normalized < 5 else 5
        return multiplier * power

    @staticmethod
    def _format_number(value: float) -> str:
        if abs(value) >= 1000 or value.is_integer():
            return f"{value:.0f}"
        return f"{value:.2f}"

    def _draw_planes(self, objects, width, height, cx, cy, scale, coordinate_limit):
        """Рисует отдельные системы координат для каждой Plane."""
        planes = [obj for obj in objects if obj["type"] == "plane"]
        if not planes:
            self._draw_axes(width, height, cx, cy, coordinate_limit, scale)
            return

        colors = [self.AXIS_COLOR, "#b56576", "#6a994e", "#c08457"]
        for index, plane in enumerate(planes):
            origin_x = cx + plane["x"] * scale
            origin_y = cy - plane["y"] * scale
            color = colors[index % len(colors)]

            if index == 0:
                self._draw_axes(width, height, origin_x, origin_y, coordinate_limit, scale)
            else:
                axis_length = min(width, height) * 0.18
                self.canvas.create_line(
                    origin_x - axis_length, origin_y,
                    origin_x + axis_length, origin_y,
                    fill=color, arrow=tk.LAST, width=2
                )
                self.canvas.create_line(
                    origin_x, origin_y + axis_length,
                    origin_x, origin_y - axis_length,
                    fill=color, arrow=tk.LAST, width=2
                )
                self._draw_compact_ticks(
                    origin_x, origin_y, axis_length, color, scale, coordinate_limit
                )

            self.canvas.create_text(
                origin_x + 8, origin_y + 8,
                text=plane["name"], fill=color, anchor=tk.NW,
                font=("Segoe UI", 8, "italic")
            )

    def _draw_compact_ticks(self, origin_x, origin_y, axis_length, color, scale, coordinate_limit):
        tick_step = self._nice_tick(coordinate_limit / 4)
        offset = tick_step * scale
        if offset <= 0 or offset >= axis_length:
            return

        for sign in (-1, 1):
            dx = origin_x + sign * offset
            dy = origin_y - sign * offset
            self.canvas.create_line(dx, origin_y - 3, dx, origin_y + 3, fill=color)
            self.canvas.create_line(origin_x - 3, dy, origin_x + 3, dy, fill=color)
            self.canvas.create_text(
                dx, origin_y + 6, text=self._format_number(sign * tick_step),
                fill=color, anchor=tk.N
            )
            self.canvas.create_text(
                origin_x + 6, dy, text=self._format_number(sign * tick_step),
                fill=color, anchor=tk.W
            )

        self.canvas.create_text(
            origin_x + axis_length - 8, origin_y - 14,
            text="X", fill=color
        )
        self.canvas.create_text(
            origin_x + 8, origin_y - axis_length + 8,
            text="Y", fill=color
        )

    def _draw_planet(self, planet, index, cx, cy, scale, max_radius):
        x = cx + planet["x"] * scale
        y = cy - planet["y"] * scale

        physical_radius = planet["radius"]
        if max_radius > 0 and physical_radius > 0:
            radius = 4.0 + 20.0 * math.sqrt(physical_radius / max_radius)
        else:
            radius = 7.0
        radius = min(radius, 24.0)

        color = self._planet_color(planet["name"], index)
        self.canvas.create_oval(
            x - radius, y - radius, x + radius, y + radius,
            fill=color, outline="#f0f0f0", width=1
        )
        self.canvas.create_text(
            x + radius + 5, y - radius - 2,
            text=planet["name"], fill=self.TEXT_COLOR, anchor=tk.SW,
            font=("Segoe UI", 8)
        )

    @staticmethod
    def _planet_color(name: str, index: int) -> str:
        palette = ["#ffb703", "#219ebc", "#fb8500", "#e76f51", "#b8c0ff"]
        lowered = name.lower()
        if "солн" in lowered or "sun" in lowered:
            return "#ffb703"
        if "зем" in lowered or "earth" in lowered:
            return "#219ebc"
        if "марс" in lowered or "mars" in lowered:
            return "#fb8500"
        return palette[index % len(palette)]

    def get_render_canvas(self) -> tk.Canvas:
        """Возвращает Canvas для будущих расширений визуализации."""
        return self.canvas

    def get_container_id(self) -> int:
        """Возвращает ID Canvas для совместимости с текущим интерфейсом."""
        return self.canvas.winfo_id()
