from dataclasses import dataclass

# Coordenadas de un teatro ficticio. x/y son unidades vectoriales propias.
ROUTE = [
    {"id": "BASE", "x": 195, "y": 230, "at": 0},
    {"id": "CP-01", "x": 330, "y": 275, "at": 15},
    {"id": "CP-02", "x": 460, "y": 340, "at": 30},
    {"id": "CP-03", "x": 605, "y": 330, "at": 50},
    {"id": "RECON-01", "x": 735, "y": 270, "at": 70},
    {"id": "RECON-02", "x": 855, "y": 390, "at": 90},
    {"id": "CP-RETURN", "x": 515, "y": 495, "at": 115},
    {"id": "BASE", "x": 195, "y": 230, "at": 145},
]


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
