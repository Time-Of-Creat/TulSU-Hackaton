import math
from collections import deque
from dataclasses import dataclass
from enum import Enum

from source.simulation.objects.builtin_types.coords2 import Coords2
from source.simulation.objects.planet import Planet, G


class SystemConfiguration(Enum):
    COLLISION = "collision"          # Столкновение
    EJECTION = "ejection"            # Выброс тела из системы
    LAGRANGE = "lagrange"            # Решение Лагранжа (равносторонний треугольник)
    EULER = "euler"                  # Решение Эйлера (коллинеарная конфигурация)
    FIGURE_EIGHT = "figure_eight"    # Орбита "восьмёрка"
    CHAOS = "chaos"                  # Хаотическое движение


# Готовые подписи и цвета для вывода в UI (MainWindow)
CONFIG_META = {
    SystemConfiguration.COLLISION: ("Столкновение!", "#ff3b30"),
    SystemConfiguration.EJECTION: ("Выброс тела", "#ff9500"),
    SystemConfiguration.LAGRANGE: ("Решение Лагранжа", "#34c759"),
    SystemConfiguration.EULER: ("Решение Эйлера", "#00c7be"),
    SystemConfiguration.FIGURE_EIGHT: ("Орбита «Восьмёрка»", "#5856d6"),
    SystemConfiguration.CHAOS: ("Хаос", "#8e8e93"),
}


@dataclass
class DetectionResult:
    configuration: SystemConfiguration
    title: str
    color: str
    confidence: float = 0.0  # Насколько близко к эталону (0.0 .. 1.0)
    collided_planets: tuple[str, str] | None = None
    ejected_planet: str | None = None


@dataclass
class _FrameMetrics:
    """Метрики одного кадра для анализа устойчивости во времени."""
    d12: float
    d23: float
    d13: float
    lagrange_err: float
    collinearity_err: float
    line_order: tuple[int, int, int]
    line_ratio: float
    omegas: tuple[float, float, float]
    radial_ratios: tuple[float, float, float]
    norm_angular_momentum: float
    center_crossing: bool
    ejected_index: int | None


def _dot(a: Coords2, b: Coords2) -> float:
    return a.x * b.x + a.y * b.y


def _cross_z(a: Coords2, b: Coords2) -> float:
    return a.x * b.y - a.y * b.x


def _length(a: Coords2) -> float:
    return math.hypot(a.x, a.y)


class ConfigurationDetector:
    """
    Классификатор конфигураций задачи трёх тел в реальном времени.
    """

    def __init__(self, history_size: int = 60):
        self.history_size = history_size
        self.history: deque[_FrameMetrics] = deque(maxlen=history_size)
        self.last_result: DetectionResult = self._make_result(SystemConfiguration.CHAOS)

    def reset(self):
        self.history.clear()
        self.last_result = self._make_result(SystemConfiguration.CHAOS)

    def analyze(self, planets: list[Planet]) -> DetectionResult:
        # 1. Высший приоритет: проверка столкновений (работает для любого числа планет >= 2)
        collision_pair = self._check_collision(planets)
        if collision_pair is not None:
            self.last_result = self._make_result(
                SystemConfiguration.COLLISION,
                confidence=1.0,
                collided_planets=collision_pair,
            )
            return self.last_result

        # Если планет не 3, классические конфигурации 3 тел не применимы
        if len(planets) != 3:
            self.history.clear()
            self.last_result = self._make_result(SystemConfiguration.CHAOS)
            return self.last_result

        # 2. Считаем геометрию и динамику текущего кадра
        metrics = self._compute_frame_metrics(planets)
        self.history.append(metrics)

        # 3. Выброс одного из тел (проверяем по последним 15 кадрам, чтобы отсеять случайные сближения)
        ejected_idx = self._check_ejection()
        if ejected_idx is not None:
            self.last_result = self._make_result(
                SystemConfiguration.EJECTION,
                confidence=1.0,
                ejected_planet=planets[ejected_idx].name,
            )
            return self.last_result

        # Для устойчивых орбит нужно накопить хотя бы полсекунды истории (30 тиков)
        if len(self.history) < 30:
            self.last_result = self._make_result(SystemConfiguration.CHAOS)
            return self.last_result

        # 4. Решение Лагранжа (равносторонний треугольник)
        lagrange_conf = self._check_lagrange()
        if lagrange_conf is not None:
            self.last_result = self._make_result(
                SystemConfiguration.LAGRANGE,
                confidence=lagrange_conf,
            )
            return self.last_result

        # 5. Решение Эйлера (три тела на одной вращающейся прямой)
        euler_conf = self._check_euler()
        if euler_conf is not None:
            self.last_result = self._make_result(
                SystemConfiguration.EULER,
                confidence=euler_conf,
            )
            return self.last_result

        # 6. Орбита "Восьмёрка"
        fig8_conf = self._check_figure_eight(planets)
        if fig8_conf is not None:
            self.last_result = self._make_result(
                SystemConfiguration.FIGURE_EIGHT,
                confidence=fig8_conf,
            )
            return self.last_result

        # 7. Иначе — хаос
        self.last_result = self._make_result(SystemConfiguration.CHAOS)
        return self.last_result

    @staticmethod
    def _make_result(
        config: SystemConfiguration,
        confidence: float = 0.0,
        collided_planets: tuple[str, str] | None = None,
        ejected_planet: str | None = None,
    ) -> DetectionResult:
        title, color = CONFIG_META[config]
        return DetectionResult(
            configuration=config,
            title=title,
            color=color,
            confidence=round(confidence, 3),
            collided_planets=collided_planets,
            ejected_planet=ejected_planet,
        )

    @staticmethod
    def _check_collision(planets: list[Planet]) -> tuple[str, str] | None:
        n = len(planets)
        for i in range(n):
            p1 = planets[i].get_global_position()
            r1 = planets[i].calculate_radius()
            for j in range(i + 1, n):
                p2 = planets[j].get_global_position()
                r2 = planets[j].calculate_radius()
                if p1.get_dist(p2) <= (r1 + r2):
                    return (planets[i].name, planets[j].name)
        return None

    def _compute_frame_metrics(self, planets: list[Planet]) -> _FrameMetrics:
        pos = [p.get_global_position() for p in planets]
        vel = [p.velocity for p in planets]
        mass = [p.mass for p in planets]
        total_mass = sum(mass)

        # Центр масс и скорость центра масс
        if total_mass > 0:
            cm_pos = (pos[0] * mass[0] + pos[1] * mass[1] + pos[2] * mass[2]) / total_mass
            cm_vel = (vel[0] * mass[0] + vel[1] * mass[1] + vel[2] * mass[2]) / total_mass
        else:
            cm_pos = (pos[0] + pos[1] + pos[2]) / 3.0
            cm_vel = (vel[0] + vel[1] + vel[2]) / 3.0

        u = [p - cm_pos for p in pos]  # Позиции относительно центра масс
        w = [v - cm_vel for v in vel]  # Скорости относительно центра масс

        # Попарные расстояния
        d12 = pos[0].get_dist(pos[1])
        d23 = pos[1].get_dist(pos[2])
        d13 = pos[0].get_dist(pos[2])
        mean_d = max((d12 + d23 + d13) / 3.0, 1e-9)
        max_d = max(d12, d23, d13, 1e-9)

        # Ошибка равносторонности (для Лагранжа)
        lagrange_err = (max(d12, d23, d13) - min(d12, d23, d13)) / mean_d

        # Ошибка коллинеарности (удвоенная площадь треугольника / max_d^2)
        area2 = abs(_cross_z(pos[1] - pos[0], pos[2] - pos[0]))
        collinearity_err = area2 / (max_d * max_d)

        # Порядок тел вдоль главной оси и отношение отрезков (для Эйлера)
        axis = pos[1] - pos[0]
        if _length(axis) < 1e-9:
            axis = pos[2] - pos[0]
        projections = sorted((_dot(pos[i], axis), i) for i in range(3))
        line_order = (projections[0][1], projections[1][1], projections[2][1])
        d_left = pos[line_order[0]].get_dist(pos[line_order[1]])
        d_right = max(pos[line_order[1]].get_dist(pos[line_order[2]]), 1e-9)
        line_ratio = d_left / d_right

        # Угловые скорости и доля радиальной скорости вокруг центра масс
        omegas = []
        radial_ratios = []
        for i in range(3):
            r_len = _length(u[i])
            v_len = _length(w[i])
            if r_len > 1e-9:
                omegas.append(_cross_z(u[i], w[i]) / (r_len * r_len))
            else:
                omegas.append(0.0)

            if r_len > 1e-9 and v_len > 1e-9:
                radial_ratios.append(abs(_dot(u[i], w[i])) / (r_len * v_len))
            else:
                radial_ratios.append(0.0)

        # Нормированный суммарный момент импульса (для восьмёрки он ~ 0)
        l_total = sum(mass[i] * _cross_z(u[i], w[i]) for i in range(3))
        l_scale = sum(mass[i] * _length(u[i]) * _length(w[i]) for i in range(3))
        norm_l = abs(l_total) / max(l_scale, 1e-9)

        # Проверка симметричного прохождения центра масс (ключевой признак восьмёрки)
        center_crossing = False
        for i in range(3):
            if _length(u[i]) < 0.08 * max_d:
                others = [j for j in range(3) if j != i]
                j, k = others[0], others[1]
                opp_pos_err = _length(u[j] + u[k]) / max_d
                vel_scale = max(_length(w[j]), _length(w[k]), 1e-9)
                same_vel_err = _length(w[j] - w[k]) / vel_scale
                if opp_pos_err < 0.12 and same_vel_err < 0.15:
                    center_crossing = True
                    break

        # Проверка выброса одного из тел
        ejected_index = None
        pair_dists = [(0, d23), (1, d13), (2, d12)]
        for i, other_pair_d in pair_dists:
            r_i = _length(u[i])
            if r_i > 5.0 * max(other_pair_d, 1e-9) and _dot(u[i], w[i]) > 0:
                kinetic = 0.5 * mass[i] * (_length(w[i]) ** 2)
                potential = 0.0
                for j in range(3):
                    if i != j:
                        dist_ij = max(pos[i].get_dist(pos[j]), 1e-9)
                        potential -= G * mass[i] * mass[j] / dist_ij
                if kinetic + potential > 0:
                    ejected_index = i
                    break

        return _FrameMetrics(
            d12=d12,
            d23=d23,
            d13=d13,
            lagrange_err=lagrange_err,
            collinearity_err=collinearity_err,
            line_order=line_order,
            line_ratio=line_ratio,
            omegas=(omegas[0], omegas[1], omegas[2]),
            radial_ratios=(radial_ratios[0], radial_ratios[1], radial_ratios[2]),
            norm_angular_momentum=norm_l,
            center_crossing=center_crossing,
            ejected_index=ejected_index,
        )

    def _check_ejection(self) -> int | None:
        if len(self.history) < 15:
            return None
        recent = list(self.history)[-15:]
        first = recent[0].ejected_index
        if first is not None and all(m.ejected_index == first for m in recent):
            return first
        return None

    def _check_lagrange(self) -> float | None:
        tol = 0.05  # Допуск 5% на разницу сторон треугольника
        avg_err = sum(m.lagrange_err for m in self.history) / len(self.history)
        if avg_err > tol:
            return None

        # Все кадры в окне должны держать форму треугольника и вращаться в одну сторону
        for m in self.history:
            if m.lagrange_err > tol * 1.4:
                return None
            if max(m.radial_ratios) > 0.2:
                return None
            signs = [1 if om > 1e-7 else (-1 if om < -1e-7 else 0) for om in m.omegas]
            if len(set(signs)) != 1 or signs[0] == 0:
                return None

        return max(0.0, min(1.0, 1.0 - avg_err / tol))

    def _check_euler(self) -> float | None:
        tol = 0.03  # Допуск на отклонение от прямой
        avg_err = sum(m.collinearity_err for m in self.history) / len(self.history)
        if avg_err > tol:
            return None

        expected_order = self.history[0].line_order
        ratios = []
        for m in self.history:
            if m.collinearity_err > tol * 1.5:
                return None
            # Среднее тело не должно меняться местами с крайними
            if m.line_order[1] != expected_order[1]:
                return None
            ratios.append(m.line_ratio)

        mean_ratio = max(sum(ratios) / len(ratios), 1e-9)
        ratio_drift = (max(ratios) - min(ratios)) / mean_ratio
        if ratio_drift > 0.10:
            return None

        return max(0.0, min(1.0, 1.0 - avg_err / tol))

    def _check_figure_eight(self, planets: list[Planet]) -> float | None:
        # 1. Массы должны быть равны с точностью до 3%
        masses = [p.mass for p in planets]
        mean_m = max(sum(masses) / 3.0, 1e-9)
        mass_err = (max(masses) - min(masses)) / mean_m
        if mass_err > 0.03:
            return None

        # 2. Суммарный момент импульса близок к нулю
        avg_norm_l = sum(m.norm_angular_momentum for m in self.history) / len(self.history)
        if avg_norm_l > 0.06:
            return None

        # 3. Тела не улетают и не схлопываются (ограниченность орбиты)
        max_dists = [max(m.d12, m.d23, m.d13) for m in self.history]
        if max(max_dists) > 2.5 * max(min(max_dists), 1e-9):
            return None

        # 4. Характерная смена знака угловой скорости (переход между петлями восьмёрки)
        # или зафиксированное симметричное прохождение центра масс
        has_center_crossing = any(m.center_crossing for m in self.history)
        omega_0_values = [m.omegas[0] for m in self.history]
        has_loop_switch = min(omega_0_values) < -1e-6 and max(omega_0_values) > 1e-6

        if not (has_center_crossing or has_loop_switch):
            return None

        return max(0.0, min(1.0, 1.0 - avg_norm_l / 0.06))