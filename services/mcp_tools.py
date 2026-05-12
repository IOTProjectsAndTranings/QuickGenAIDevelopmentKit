"""
services/mcp_tools.py
─────────────────────
MCP-style tool definitions.
✏️ ON HACKATHON DAY: change tool names/descriptions and execute_tool() cases.
"""

import json
from services.mock_data import (
    get_all_entities, get_entity_by_id,
    get_entities_by_status, get_alerts, build_llm_context,
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_all_devices",
            "description": "Retrieve all IoT devices with their current status, sensor values, protocol, and location.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_device_by_id",
            "description": "Get detailed information about a specific device using its ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_id": {"type": "string", "description": "The device ID, e.g. dev_001"}
                },
                "required": ["device_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_devices_by_status",
            "description": "Filter and retrieve devices by their operational status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["online", "offline", "warning"],
                        "description": "The status to filter by.",
                    }
                },
                "required": ["status"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_active_alerts",
            "description": "Get all active alerts and warnings currently raised in the system.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_summary",
            "description": "Get a full plain-text summary of the entire system state.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


def execute_tool(name: str, args: dict) -> dict:
    if name == "get_all_devices":
        devices = get_all_entities()
        return {"devices": devices, "total": len(devices)}

    elif name == "get_device_by_id":
        device = get_entity_by_id(args.get("device_id", ""))
        return {"device": device} if device else {"error": f"Device '{args.get('device_id')}' not found"}

    elif name == "get_devices_by_status":
        devices = get_entities_by_status(args.get("status", "online"))
        return {"status_filter": args.get("status"), "devices": devices, "count": len(devices)}

    elif name == "get_active_alerts":
        alerts = get_alerts()
        return {"alerts": alerts, "total": len(alerts)}

    elif name == "get_system_summary":
        return {"summary": build_llm_context()}

    else:
        return {"error": f"Unknown tool: '{name}'"}
