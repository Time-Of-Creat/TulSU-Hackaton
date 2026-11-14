import json
import os
import threading
import uuid
from contextlib import nullcontext
from pathlib import Path
from typing import Callable, Optional, Any, List, Dict
import tkinter.filedialog as fd
import tkinter.messagebox as mb

from source.simulation.objects.object import Object
from source.simulation.objects.planet import Planet
from source.simulation.objects.plane import Plane
from source.simulation.objects.builtin_types.coords2 import Coords2


class SimulationController:
    """
    Контроллер симуляции и обработчики действий.
    Отвечает за состояние интерфейса, сохранение/загрузку конфигурации и точки подключения симуляции.
    """
    def __init__(self, on_status_change: Optional[Callable[[str], None]] = None, backend: Optional[Any] = None):
        self.is_running: bool = False
        self.is_paused: bool = False
        self._on_status_change = on_status_change
        self.backend = backend
        self._sim_thread: Optional[threading.Thread] = None
        self.current_file_path: Optional[str] = None
        self.on_scene_changed: Optional[Callable[[], None]] = None

    def set_status_callback(self, callback: Callable[[str], None]):
        self._on_status_change = callback

    def notify_status(self, text: str):
        if self._on_status_change:
            self._on_status_change(text)

    # --- Секция Файл: Сохранение и Загрузка ---

    def file_save(self, parent_window=None) -> bool:
        """Сохраняет текущую конфигурацию в уже открытый файл, либо запрашивает новый путь."""
        if not self.current_file_path:
            return self.file_save_as(parent_window)
        return self._save_to_path(self.current_file_path, parent_window)

    def file_save_as(self, parent_window=None) -> bool:
        """Запрашивает у пользователя путь к файлу и сохраняет конфигурацию."""
        file_path = fd.asksaveasfilename(
            parent=parent_window,
            defaultextension=".json",
            filetypes=[("Файлы симуляции (*.json)", "*.json"), ("Все файлы (*.*)", "*.*")],
            title="Сохранить конфигурацию как..."
        )
        if file_path:
            self.current_file_path = file_path
            return self._save_to_path(file_path, parent_window)
        return False

    def file_load(self, parent_window=None) -> bool:
        """Запрашивает файл конфигурации и загружает объекты в симуляцию."""
        file_path = fd.askopenfilename(
            parent=parent_window,
            filetypes=[("Файлы симуляции (*.json)", "*.json"), ("Все файлы (*.*)", "*.*")],
            title="Загрузить конфигурацию..."
        )
        if file_path:
            return self._load_from_path(file_path, parent_window)
        return False

    def _serialize_object(self, obj: Object) -> Dict[str, Any]:
        """Рекурсивно сериализует объект и его дочерние узлы в словарь."""
        is_planet = isinstance(obj, Planet) or getattr(obj, "obj_type", "") == "planet"
        is_plane = isinstance(obj, Plane) or getattr(obj, "obj_type", "") == "plane"

        pos = getattr(obj, "local_position", None)
        pos_list = [float(getattr(pos, "x", 0.0)), float(getattr(pos, "y", 0.0))]

        data: Dict[str, Any] = {
            "id": getattr(obj, "id", uuid.uuid4().hex[:8]),
            "name": getattr(obj, "name", "Объект"),
            "position": pos_list,
            "rotation_deg": float(getattr(obj, "local_rotation_deg", 0.0)),
            "children": [self._serialize_object(child) for child in getattr(obj, "children", [])]
        }

        if is_planet:
            data["type"] = "planet"
            data["mass"] = float(getattr(obj, "mass", 1.0))
            data["density"] = float(getattr(obj, "density", 1.0))
            vel = getattr(obj, "velocity", None)
            data["velocity"] = [float(getattr(vel, "x", 0.0)), float(getattr(vel, "y", 0.0))]
            data["color"] = str(getattr(obj, "color", "#4A90E2"))
            data["is_fixed"] = bool(getattr(obj, "is_fixed", False))
        elif is_plane:
            data["type"] = "plane"
            data["orientation"] = str(getattr(obj, "orientation", "XY"))
            data["grid_step"] = float(getattr(obj, "grid_step", 10.0))
            data["grid_size"] = float(getattr(obj, "grid_size", 100.0))
            data["line_color"] = str(getattr(obj, "line_color", "#7A8288"))
            data["is_visible"] = bool(getattr(obj, "is_visible", True))
        else:
            data["type"] = "object"

        return data

    def _deserialize_object(self, data: Dict[str, Any], parent: Optional[Object] = None) -> Object:
        """Рекурсивно десериализует словарь в объект с восстановлением иерархии."""
        obj_type = data.get("type", "object")
        name = data.get("name", "Объект")
        obj_id = data.get("id") or uuid.uuid4().hex[:8]

        pos_arr = data.get("position", [0.0, 0.0])
        pos = Coords2(float(pos_arr[0]), float(pos_arr[1]))
        rot = float(data.get("rotation_deg", 0.0))

        if obj_type == "planet":
            mass = float(data.get("mass", 1.0))
            planet = Planet(name=name, mass=mass, parent=parent)
            planet.id = obj_id
            planet.density = float(data.get("density", 1.0))
            vel_arr = data.get("velocity", [0.0, 0.0])
            planet.velocity = Coords2(float(vel_arr[0]), float(vel_arr[1]))
            planet.color = str(data.get("color", "#4A90E2"))
            planet.is_fixed = bool(data.get("is_fixed", False))
            obj = planet
        elif obj_type == "plane":
            plane = Plane(name=name, parent=parent)
            plane.id = obj_id
            plane.orientation = str(data.get("orientation", "XY"))
            plane.grid_step = float(data.get("grid_step", 10.0))
            plane.grid_size = float(data.get("grid_size", 100.0))
            plane.line_color = str(data.get("line_color", "#7A8288"))
            plane.is_visible = bool(data.get("is_visible", True))
            obj = plane
        else:
            obj = Object(name=name, parent=parent)
            obj.id = obj_id

        obj.local_position = pos
        obj.local_rotation_deg = rot

        for child_data in data.get("children", []):
            child_obj = self._deserialize_object(child_data, parent=obj)
            obj.add_child(child_obj)

        return obj

    def _save_to_path(self, file_path: str, parent_window=None) -> bool:
        try:
            if not self.backend:
                return False

            lock = getattr(self.backend, "lock", None)
            sim_data = getattr(self.backend, "simulation_data", None)
            if not sim_data or not hasattr(sim_data, "instance"):
                return False

            with (lock if lock else nullcontext()):
                root_objs = sim_data.instance.objects
                payload = {
                    "version": "1.0",
                    "simulation_speed": float(getattr(sim_data, "simulation_speed", 1.0)),
                    "objects": [self._serialize_object(o) for o in root_objs]
                }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)

            filename = Path(file_path).name
            self.notify_status(f"Конфигурация сохранена: {filename}")
            if parent_window:
                mb.showinfo("Файл", f"Конфигурация успешно сохранена в:\n{filename}", parent=parent_window)
            return True
        except Exception as e:
            if parent_window:
                mb.showerror("Ошибка сохранения", f"Не удалось сохранить файл:\n{e}", parent=parent_window)
            self.notify_status(f"Ошибка сохранения: {e}")
            return False

    def _load_from_path(self, file_path: str, parent_window=None) -> bool:
        try:
            if not self.backend:
                return False

            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Файл не найден: {file_path}")

            with open(file_path, "r", encoding="utf-8") as f:
                payload = json.load(f)

            if "objects" not in payload:
                raise ValueError("В файле отсутствует список объектов ('objects')")

            # Если симуляция активна, останавливаем её
            if self.is_running:
                self.toggle_run()

            lock = getattr(self.backend, "lock", None)
            sim_data = getattr(self.backend, "simulation_data", None)
            if not sim_data or not hasattr(sim_data, "instance"):
                return False

            new_root_objects: List[Object] = [
                self._deserialize_object(item) for item in payload["objects"]
            ]

            with (lock if lock else nullcontext()):
                sim_data.instance.objects = new_root_objects
                if "simulation_speed" in payload:
                    sim_data.simulation_speed = float(payload["simulation_speed"])
                sim_data._snapshot()

            self.current_file_path = file_path
            filename = Path(file_path).name
            self.notify_status(f"Загружен файл: {filename}")

            if self.on_scene_changed:
                self.on_scene_changed()

            if parent_window:
                mb.showinfo("Файл", f"Конфигурация успешно загружена из:\n{filename}", parent=parent_window)
            return True
        except Exception as e:
            if parent_window:
                mb.showerror("Ошибка загрузки", f"Не удалось загрузить файл:\n{e}", parent=parent_window)
            self.notify_status(f"Ошибка загрузки: {e}")
            return False

    # --- Управление симуляцией ---

    def toggle_run(self) -> bool:
        """
        Переключает запуск и сброс.
        Возвращает True, если симуляция запущена, иначе False.
        """
        if not self.is_running:
            self.is_running = True
            self.is_paused = False
            self.notify_status("Симуляция запущена.")
            self._start_simulation_hook()
            return True
        else:
            self.is_running = False
            self.is_paused = False
            self.notify_status("Симуляция сброшена.")
            self._reset_simulation_hook()
            return False

    def toggle_pause(self) -> bool:
        """
        Переключает паузу и продолжение.
        Возвращает True, если симуляция на паузе, иначе False.
        """
        if not self.is_running:
            return False

        self.is_paused = not self.is_paused
        if self.is_paused:
            self.notify_status("Симуляция приостановлена.")
            self._pause_simulation_hook()
        else:
            self.notify_status("Симуляция возобновлена.")
            self._resume_simulation_hook()
        return self.is_paused

    def _start_simulation_hook(self):
        """Вызывается при запуске симуляции."""
        if self.backend and not getattr(self.backend, "running", False):
            self._sim_thread = threading.Thread(target=self.backend.start_simulation, daemon=True)
            self._sim_thread.start()

    def _reset_simulation_hook(self):
        """Вызывается при сбросе симуляции."""
        if self.backend and hasattr(self.backend, "reset_simulation"):
            self.backend.reset_simulation()

    def _pause_simulation_hook(self):
        """Вызывается при включении паузы."""
        if self.backend and hasattr(self.backend, "pause_simulation"):
            self.backend.pause_simulation()

    def _resume_simulation_hook(self):
        """Вызывается при продолжении симуляции."""
        if self.backend and not getattr(self.backend, "running", False):
            self._sim_thread = threading.Thread(target=self.backend.start_simulation, daemon=True)
            self._sim_thread.start()

    def on_plane_added(self, plane):
        """Обработчик добавления координатной системы."""
        self.notify_status(f"Добавлена координатная система: {plane.name}")

    def on_plane_removed(self, plane_id: str):
        """Обработчик удаления координатной системы."""
        self.notify_status(f"Координатная система {plane_id} удалена.")

    def on_property_changed(self, obj_id: str, key: str, value):
        """Обработчик изменения параметра объекта."""
        self.notify_status(f"Параметр {key} изменен на: {value}")
