CHANNELS = [
    ("RF-PRIMARY", "RF", 12, 43, 24.8),
    ("RF-DIRECTIONAL", "RF", 8, 58, 27.2),
    ("OPTICAL-LINK", "OPTICAL", 24, 12, 35),
    ("SATELLITE-FALLBACK", "SATELLITE", 1.5, 620, 16),
]


def metrics(interference=0):
    result = []
    for index, (name, kind, bandwidth, latency, snr) in enumerate(CHANNELS):
        impact = interference * (1, .72, .22, .12)[index]
        quality = round(max(0, 96 - impact), 1)
        loss = round(min(100, 1.2 + impact * .73), 1)
        result.append({"id": name, "type": kind, "status": "DEGRADED" if quality < 55 else "ONLINE",
                       "bandwidth": round(bandwidth * quality / 100, 2), "latency": round(latency + impact * 3),
                       "packet_loss": loss, "snr": round(snr - impact * .27, 1), "signal_quality": quality,
                       "reliability": round(1 - loss / 100, 3), "encrypted": True, "available": quality > 5})
    return result
