"""Conservative deltas from Codex cumulative token snapshots. No I/O."""

FIELDS = ("input_tokens", "output_tokens", "cached_input_tokens", "cache_eligible_input_tokens", "used_tokens")


def count(value):
    return value if type(value) is int and value >= 0 else None


def counters(value):
    if not isinstance(value, dict):
        return None
    incoming, outgoing = (count(value.get(key)) for key in ("input_tokens", "output_tokens"))
    if incoming is None or outgoing is None:
        return None
    cached = count(value.get("cached_input_tokens"))
    if cached is not None and cached > incoming:
        return None
    return incoming, outgoing, cached


class TokenCounter:
    def __init__(self):
        self.previous = None

    def read(self, payload):
        """Advance even outside the report window, retaining the prior baseline.

        A first snapshot is attributable only if it equals the last response (or
        is zero). Decreases rebaseline without counting the reset. A missing
        cache field never becomes zero. Reasoning is already inside output.
        """
        result = {"coverage": {"snapshots": 1}}
        info = payload.get("info")
        if not isinstance(info, dict) or info.get("total_token_usage") is None:
            result["coverage"]["missing_usage"] = 1
            return result
        current = counters(info["total_token_usage"])
        if current is None:
            self.previous = None
            result["coverage"]["invalid_usage"] = 1
            return result
        previous, self.previous = self.previous, current
        if previous is None:
            last = counters(info.get("last_token_usage"))
            if current[:2] != (0, 0) and (last is None or current[:2] != last[:2]):
                result["coverage"]["unknown_baseline"] = 1
                return result
            previous = (0, 0, 0)
        elif current == previous:
            result["coverage"]["duplicates"] = 1
            return result
        if any(a is not None and b is not None and a < b for a, b in zip(current, previous)):
            result["coverage"]["counter_resets"] = 1
            return result
        incoming, outgoing = (current[i] - previous[i] for i in (0, 1))
        cached = current[2] - previous[2] if current[2] is not None and previous[2] is not None else None
        if cached is not None and cached > incoming:
            result["coverage"]["invalid_usage"] = 1
            return result
        # Cache-field corrections without a new input/output count cannot be
        # attributed to this date. Preserve the corrected baseline only.
        if incoming == outgoing == 0 and current != (0, 0, 0):
            result["coverage"]["duplicates"] = 1
            return result
        result.update(input_tokens=incoming, output_tokens=outgoing)
        result["coverage"]["measured"] = 1
        if cached is not None:
            result.update(cached_input_tokens=cached, cache_eligible_input_tokens=incoming, used_tokens=incoming - cached + outgoing)
            result["coverage"]["cache_known"] = 1
        return result


def empty_totals():
    return dict.fromkeys(FIELDS, None) | {"coverage": {}, "sessions": []}


def add_tokens(target, item, session=None):
    for key in FIELDS:
        value = item.get(key)
        if value is not None:
            target[key] = (target[key] or 0) + value
    for key, value in item.get("coverage", {}).items():
        target["coverage"][key] = target["coverage"].get(key, 0) + value
    sessions = item.get("sessions", [])
    if session and item.get("coverage", {}).get("measured"):
        sessions = [*sessions, session]
    target["sessions"] = sorted(set(target["sessions"]) | set(sessions))


def summarize(rows):
    result = empty_totals()
    for row in rows:
        add_tokens(result, row["tokens"])
    eligible = result["cache_eligible_input_tokens"]
    result["cache_hit_rate"] = result["cached_input_tokens"] / eligible if eligible else None
    return result
