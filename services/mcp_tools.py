"""
services/mcp_tools.py
─────────────────────
MCP-style tool definitions for the LLM to call.
Instead of injecting all context as text, the LLM can call these tools
to fetch specific data — more accurate, more scalable.

✏️ ON HACKATHON DAY:
  - Keep the TOOLS list structure identical
  - Change tool names and descriptions to match your domain
  - Update execute_tool() cases to call your domain's data functions

Example domain swaps:
  IoT     → get_all_devices, get_device_by_id, get_active_alerts
  HR      → get_all_employees, get_employee_by_id, get_open_positions
  Supply  → get_inventory, get_shipments, get_low_stock_items
"""

import json
from services.mock_data import (
    get_all_entities,
    get_entity_by_id,
    get_entities_by_status,
    get_alerts,
    build_llm_context,
)

# ── Tool Definitions (OpenAI-compatible format) ───────────────────────────────
# ✏️ Change names/descriptions on hackathon day — keep the structure

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_all_devices",
            "description": "Retrieve all IoT devices with their current status, sensor values, protocol, and location.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
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
                    "device_id": {
                        "type": "string",
                        "description": "The device ID, e.g. dev_001",
                    }
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
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_summary",
            "description": "Get a full plain-text summary of the entire system state — all devices and alerts.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]


# ── Tool Executor ─────────────────────────────────────────────────────────────
def execute_tool(name: str, args: dict) -> dict:
    """
    Execute a tool by name with given args.
    Returns a dict that gets serialized as JSON and sent back to the LLM.
    ✏️ Add cases here as you add new tools.
    """
    if name == "get_all_devices":
        devices = get_all_entities()
        return {"devices": devices, "total": len(devices)}

    elif name == "get_device_by_id":
        device_id = args.get("device_id", "")
        device = get_entity_by_id(device_id)
        if device:
            return {"device": device}
        return {"error": f"Device '{device_id}' not found"}

    elif name == "get_devices_by_status":
        status = args.get("status", "online")
        devices = get_entities_by_status(status)
        return {
            "status_filter": status,
            "devices": devices,
            "count": len(devices),
        }

    elif name == "get_active_alerts":
        alerts = get_alerts()
        return {"alerts": alerts, "total": len(alerts)}

    elif name == "get_system_summary":
        return {"summary": build_llm_context()}

    else:
        return {"error": f"Unknown tool: '{name}'. Available: {[t['function']['name'] for t in TOOLS]}"}
