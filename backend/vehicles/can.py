"""Tráfico ficticio en memoria. No contiene interfaces ni transporte CAN real."""
import math


class CANSimulationEngine:
    IDS = [("0x101", "MOTOR", (0, 5000)), ("0x120", "BATTERY", (0, 100)),
           ("0x201", "SPEED", (0, 60)), ("0x220", "STEERING", (-45, 45)),
           ("0x310", "BRAKE", (0, 100)), ("0x410", "SYSTEM", (0, 1))]

    def sample(self, timestamp, speed, level):
        values = [1200 if speed else 0, 92, round(max(0, speed - level * .29), 1), 3, 0, 1]
        return [{"timestamp": timestamp, "can_id": cid, "source": source, "value": value,
                 "frequency": 10, "expected_range": list(bounds)}
                for (cid, source, bounds), value in zip(self.IDS, values)]


class CANAnomalyDetector:
    """La evidencia proviene de sensores; nunca de la fase del guion ni de un LLM."""
    def analyze(self, messages, gps, imu, history):
        evidence = []
        expected = {cid for cid, _, _ in CANSimulationEngine.IDS}
        previous = history[-1] if history else None
        for msg in messages:
            value = msg["value"]
            if not math.isfinite(value) or not msg["expected_range"][0] <= value <= msg["expected_range"][1]:
                evidence.append(f"{msg['can_id']}: valor fuera de rango")
            if msg["can_id"] not in expected:
                evidence.append(f"{msg['can_id']}: mensaje inesperado")
            if not 8 <= msg["frequency"] <= 12:
                evidence.append(f"{msg['can_id']}: frecuencia anormal")
        can = next((m["value"] for m in messages if m["can_id"] == "0x201"), None)
        if can is None:
            can = 0
            evidence.append("0x201: mensaje ausente")
        residual = min(abs(gps-can), abs(imu-can))
        independent = abs(gps-imu) <= 3
        if independent and residual >= 3:
            evidence.append("GPS e IMU coinciden; CAN SPEED contradice ambas fuentes")
        if previous and abs(can-previous["can"]) > 8 and abs(gps-previous["gps"]) < 3:
            evidence.append("Cambio abrupto de CAN SPEED sin desaceleración física")
        recent = history[-7:]
        persistent = sum(row["residual"] >= 3 for row in recent)
        if persistent >= 3:
            evidence.append("Inconsistencia persistente en el historial reciente")
        score = min(99, round(12 + (min(62, residual * 2.2) if independent else 0) + persistent * 2.4 +
                              sum('rango' in e or 'frecuencia' in e or 'inesperado' in e or 'ausente' in e for e in evidence) * 12))
        return {"score": score, "trust": max(0, 100-score), "evidence": evidence,
                "correlation": {"gps_imu": independent, "gps_can": abs(gps-can) < 5, "imu_can": abs(imu-can) < 5},
                "sample": {"gps": gps, "imu": imu, "can": can, "residual": round(residual, 1)}}
