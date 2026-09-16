def emit(state, kind, message):
    state["event_sequence"] += 1
    state["events"].append({"sequence": state["event_sequence"], "elapsed": state["elapsed"], "kind": kind, "message": message})
    state["events"] = state["events"][-80:]
