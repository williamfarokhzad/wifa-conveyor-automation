"""Discrete single-release conveyor model. No machine I/O."""
import argparse
from collections import deque
import csv
import json
from pathlib import Path


def simulate(zones, ticks, arrivals, blocked_ticks):
    """Return after-tick snapshots. Start empty; package IDs follow arrival order."""
    if type(zones) is not int or not 1 <= zones <= 20:
        raise ValueError("zones must be an integer from 1 to 20")
    if type(ticks) is not int or not 1 <= ticks <= 10000:
        raise ValueError("ticks must be an integer from 1 to 10000")
    for label, values in (("arrivals", arrivals), ("blocked_ticks", blocked_ticks)):
        if not isinstance(values, list) or any(
            type(t) is not int or not 0 <= t < ticks for t in values
        ):
            raise ValueError(f"{label} must contain integer ticks in [0, {ticks})")
    if arrivals != sorted(arrivals):
        raise ValueError("arrivals must be in nondecreasing order")
    if len(blocked_ticks) != len(set(blocked_ticks)):
        raise ValueError("blocked_ticks must not contain duplicates")
    scheduled = deque(enumerate(arrivals, start=1))
    blocked = set(blocked_ticks)
    queue = deque()
    slots = (None,) * zones
    rows = []
    for t in range(ticks):
        while scheduled and scheduled[0][1] == t:
            queue.append(scheduled.popleft()[0])
        before = slots
        after = list(before)
        departed = None
        if t not in blocked and before[-1] is not None:
            departed = before[-1]
            after[-1] = None
        for i in range(zones - 1):
            if before[i] is not None and before[i + 1] is None:
                after[i], after[i + 1] = None, before[i]
        if before[0] is None and queue:
            after[0] = queue.popleft()
        slots = tuple(after)
        rows.append((t, t in blocked, slots, len(queue), departed))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", type=Path)
    parser.add_argument("--csv", type=Path, help="optional trace destination")
    args = parser.parse_args()
    try:
        spec = json.loads(args.scenario.read_text(encoding="utf-8"))
        if not isinstance(spec, dict) or set(spec) != {"zones", "ticks", "arrivals", "blocked_ticks"}:
            raise ValueError("scenario needs zones, ticks, arrivals, and blocked_ticks")
        rows = simulate(**spec)
        if args.csv:
            with args.csv.open("w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["tick", "exit_blocked", *[f"zone_{i+1}" for i in range(spec["zones"])],
                                 "waiting", "departed"])
                writer.writerows((t, int(blocked), *slots, waiting, departed)
                                 for t, blocked, slots, waiting, departed in rows)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    departures = ", ".join(f"{box}@{t}" for t, _, _, _, box in rows if box is not None)
    print(f"Departures (package@tick): {departures or 'none'}")
    _, _, slots, waiting, _ = rows[-1]
    print(f"On conveyor: {sum(box is not None for box in slots)}; waiting upstream: {waiting}")


if __name__ == "__main__":
    main()
