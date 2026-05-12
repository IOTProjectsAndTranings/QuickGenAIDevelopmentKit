"""
services/mock_data.py
─────────────────────
⚠️  ON HACKATHON DAY — this is the ONLY file to swap domain data in.
Change DOMAIN_ENTITIES and ALERTS to match your problem statement.

Fixes applied:
  - M4: Status comparison is now case-insensitive
"""

from typing import List, Dict, Any

# ── ✏️ CHANGE THIS ON HACKATHON DAY ──────────────────────────────────────────
DOMAIN_NAME = "IoT Device Management"

DOMAIN_ENTITIES: List[Dict[str, Any]] = [
    {"id": "dev_001", "name": "Temperature Sensor - Zone A", "status": "online",  "protocol": "MQTT",  "value": 24.5,  "unit": "°C",  "location": "Floor 1"},
    {"id": "dev_002", "name": "Pressure Gauge - Zone B",     "status": "offline", "protocol": "CoAP",  "value": None,  "unit": "bar", "location": "Floor 2"},
    {"id": "dev_003", "name": "Flow Meter - Zone C",         "status": "online",  "protocol": "HTTP",  "value": 120.3, "unit": "L/m", "location": "Floor 3"},
    {"id": "dev_004", "name": "Humidity Sensor - Zone A",    "status": "warning", "protocol": "MQTT",  "value": 88.0,  "unit": "%",   "location": "Floor 1"},
    {"id": "dev_005", "name": "Gas Detector - Zone D",       "status": "online",  "protocol": "LwM2M", "value": 0.02,  "unit": "ppm", "location": "Floor 4"},
]

ALERTS: List[Dict[str, Any]] = [
    {"id": "alr_001", "device_id": "dev_002", "type": "CONNECTION_LOST",    "severity": "high",   "message": "Device offline for 2 hours"},
    {"id": "alr_002", "device_id": "dev_004", "type": "THRESHOLD_EXCEEDED", "severity": "medium", "message": "Humidity above 85%"},
]
# ─────────────────────────────────────────────────────────────────────────────


def get_all_entities() -> List[Dict]:
    return DOMAIN_ENTITIES


def get_entity_by_id(entity_id: str) -> Dict | None:
    return next((e for e in DOMAIN_ENTITIES if e["id"] == entity_id), None)


def get_entities_by_status(status: str) -> List[Dict]:
    # M4: case-insensitive comparison
    return [e for e in DOMAIN_ENTITIES if e["status"].lower() == status.lower()]


def get_alerts() -> List[Dict]:
    return ALERTS


def build_llm_context() -> str:
    lines = []
    for e in DOMAIN_ENTITIES:
        val = f"{e['value']} {e['unit']}" if e["value"] is not None else "N/A"
        lines.append(
            f"- {e['name']} [{e['id']}]: status={e['status']}, "
            f"value={val}, protocol={e.get('protocol','?')}, location={e.get('location','?')}"
        )
    alert_lines = [
        f"- ALERT [{a['severity'].upper()}]: {a['message']} (device: {a['device_id']})"
        for a in ALERTS
    ]
    return (
        f"Domain: {DOMAIN_NAME}\n"
        f"Entities:\n" + "\n".join(lines) + "\n\n"
        f"Active Alerts:\n" + "\n".join(alert_lines)
    )
