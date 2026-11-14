import threading
from typing import Callable, Optional, Any
import tkinter.filedialog as fd
import tkinter.messagebox as mb


class SimulationController:
    """
    Контроллер симуляции и обработчики действий.
    Отвечает за состояние интерфейса и точки подключения симуляции.
    """
    def __init__(self, on_status_change: Optional[Callable[[str], None]] = None, backend: Optional[Any] = None):
        self.is_running: bool = False
        self.is_paused: bool = False
        self._on_status_change = on_status_change
        self.backend = backend
        self._sim_thread: Optional[threading.Thread] = None

    def set_status_callback(self, callback: Callable[[str], None]):
        self._on_status_change = callback

    def notify_status(self, text: str):
        if self._on_status_change:
            self._on_status_change(text)

    def file_save(self, parent_window=None):
        self.notify_status("Конфигурация сохранена (stub).")
        if parent_window:
            mb.showinfo("Файл", "Конфигурация успешно сохранена (заглушка).", parent=parent_window)

    def file_save_as(self, parent_window=None):
        file_path = fd.asksaveasfilename(
            parent=parent_window,
            defaultextension=".json",
            filetypes=[("Файлы симуляции (*.json)", "*.json"), ("Все файлы (*.*)", "*.*")],
            title="Сохранить конфигурацию как..."
        )
        if file_path:
            self.notify_status(f"Сохранено в: {file_path} (stub)")

    def file_load(self, parent_window=None):
        file_path = fd.askopenfilename(
            parent=parent_window,
            filetypes=[("Файлы симуляции (*.json)", "*.json"), ("Все файлы (*.*)", "*.*")],
            title="Загрузить конфигурацию..."
        )
        if file_path:
            self.notify_status(f"Загружен файл: {file_path} (stub)")

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
        """Пустой обработчик добавления плоскости."""
        self.notify_status(f"Добавлена плоскость: {plane.name}")

    def on_plane_removed(self, plane_id: str):
        """Пустой обработчик удаления плоскости."""
        self.notify_status(f"Плоскость {plane_id} удалена.")

    def on_property_changed(self, obj_id: str, key: str, value):
        """Пустой обработчик изменения параметра объекта."""
        self.notify_status(f"Параметр {key} изменен на: {value}")
