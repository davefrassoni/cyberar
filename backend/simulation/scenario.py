import copy
from dataclasses import dataclass

FIXED_WING = "FIXED_WING"
QUADCOPTER = "QUADCOPTER"

# Coordenadas de teatros ficticios. x/y son unidades vectoriales propias (viewBox 0 0 1100 650).
_ATLANTIC_ROUTE = [
    {"id": "BASE", "x": 195, "y": 230, "at": 0},
    {"id": "CP-01", "x": 330, "y": 275, "at": 15},
    {"id": "CP-02", "x": 460, "y": 340, "at": 30},
    {"id": "CP-03", "x": 605, "y": 330, "at": 50},
    {"id": "RECON-01", "x": 735, "y": 270, "at": 70},
    {"id": "RECON-02", "x": 855, "y": 390, "at": 90},
    {"id": "CP-RETURN", "x": 515, "y": 495, "at": 115},
    {"id": "BASE", "x": 195, "y": 230, "at": 145},
]
_ATLANTIC_UGV_ROUTE = [dict(id=name, x=x, y=y) for name, x, y in [
    ("BASE-UGV", 666, 252), ("T-01", 680, 238), ("T-02", 706, 242),
    ("T-03", 711, 264), ("OBSERVATION", 689, 294), ("RETURN", 666, 252)]]

_VACA_MUERTA_ROUTE = [
    {"id": "BASE-VM", "x": 150, "y": 500, "at": 0},
    {"id": "POZO-01", "x": 300, "y": 430, "at": 15},
    {"id": "POZO-02", "x": 445, "y": 470, "at": 30},
    {"id": "DUCTO-01", "x": 590, "y": 400, "at": 50},
    {"id": "POZO-03", "x": 730, "y": 340, "at": 70},
    {"id": "COMPRESORA-01", "x": 860, "y": 390, "at": 90},
    {"id": "CP-RETORNO", "x": 500, "y": 560, "at": 115},
    {"id": "BASE-VM", "x": 150, "y": 500, "at": 145},
]
_VACA_MUERTA_UGV_ROUTE = [dict(id=name, x=x, y=y) for name, x, y in [
    ("BASE-ROV", 690, 330), ("DUCTO-T1", 715, 320), ("DUCTO-T2", 740, 336),
    ("VALVULA-01", 733, 358), ("INSPECCION", 706, 368), ("RETURN", 690, 330)]]

_TRIPLE_FRONTERA_ROUTE = [
    {"id": "BASE-TF", "x": 165, "y": 150, "at": 0},
    {"id": "PUESTO-01", "x": 320, "y": 210, "at": 15},
    {"id": "PUESTO-02", "x": 470, "y": 170, "at": 30},
    {"id": "CONFLUENCIA", "x": 610, "y": 260, "at": 50},
    {"id": "PUESTO-03", "x": 760, "y": 320, "at": 70},
    {"id": "PUESTO-04", "x": 890, "y": 260, "at": 90},
    {"id": "CP-RETORNO", "x": 520, "y": 400, "at": 115},
    {"id": "BASE-TF", "x": 165, "y": 150, "at": 145},
]
_TRIPLE_FRONTERA_UGV_ROUTE = [dict(id=name, x=x, y=y) for name, x, y in [
    ("BASE-PTF", 640, 280), ("PASO-01", 662, 268), ("PASO-02", 686, 280),
    ("RIBERA-01", 680, 300), ("CONTROL", 654, 302), ("RETURN", 640, 280)]]

SCENARIOS = {
    "atlantic": {
        "label": "Operación Atlántico", "subtitle": "Reconocimiento marítimo",
        "vehicle_type": FIXED_WING, "route": _ATLANTIC_ROUTE,
        "ugv": {"asset": "UGV-01", "label": "Vehículo terrestre costero", "route": _ATLANTIC_UGV_ROUTE},
    },
    "vaca-muerta": {
        "label": "Operación Cuenca Neuquina", "subtitle": "Patrulla de infraestructura petrolera",
        "vehicle_type": QUADCOPTER, "route": _VACA_MUERTA_ROUTE,
        "ugv": {"asset": "ROV-01", "label": "Rover inspector de ductos", "route": _VACA_MUERTA_UGV_ROUTE},
    },
    "triple-frontera": {
        "label": "Operación Triple Frontera", "subtitle": "Patrulla fronteriza fluvial",
        "vehicle_type": QUADCOPTER, "route": _TRIPLE_FRONTERA_ROUTE,
        "ugv": {"asset": "PTF-01", "label": "Patrulla terrestre fronteriza", "route": _TRIPLE_FRONTERA_UGV_ROUTE},
    },
}

# Compatibilidad con importaciones existentes (tests, módulos que asumían un único teatro).
ROUTE = _ATLANTIC_ROUTE


def route_for(key, override=None):
    if key not in SCENARIOS:
        raise ValueError("Escenario desconocido")
    base = SCENARIOS[key]["route"]
    if override is not None and isinstance(override, list) and len(override) == len(base):
        return copy.deepcopy(override)
    return copy.deepcopy(base)


def ugv_route_for(key):
    if key not in SCENARIOS:
        raise ValueError("Escenario desconocido")
    return copy.deepcopy(SCENARIOS[key]["ugv"]["route"])


def scenario_meta(key, fleet_size):
    if key not in SCENARIOS:
        raise ValueError("Escenario desconocido")
    entry = SCENARIOS[key]
    return {"key": key, "label": entry["label"], "subtitle": entry["subtitle"],
            "vehicle_type": entry["vehicle_type"], "fleet_size": fleet_size,
            "ugv": {"asset": entry["ugv"]["asset"], "label": entry["ugv"]["label"]}}


@dataclass(frozen=True)
class DemoScenario:
    duration: int = 150

    def time(self, elapsed):
        return elapsed * 150 / self.duration

    def interference(self, elapsed):
        t = self.time(elapsed)
        if t < 30: return 0
        if t < 55: return 32
        if t < 80: return 66
        if t < 105: return 90
        return 0

    def can_manipulation(self, elapsed):
        """SILENT_CAN_MANIPULATION: gradual, reproducible, purely synthetic."""
        return max(0, min(100, (self.time(elapsed) - 70) * 5))
