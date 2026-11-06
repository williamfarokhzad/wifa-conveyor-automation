import csv
from itertools import product
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from conveyor import simulate


def load(name):
    return json.loads(Path(f"examples/{name}.json").read_text())


class ConveyorTests(unittest.TestCase):
    def test_open_line_hand_trace(self):
        rows = simulate(**load("open"))
        self.assertEqual([r[2] for r in rows[:5]], [
            (1, None, None), (None, 1, None), (2, None, 1),
            (None, 2, None), (3, None, 2)])
        self.assertEqual([(r[0], r[4]) for r in rows if r[4]], [(3, 1), (5, 2), (7, 3), (9, 4)])

    def test_blocked_line_and_restart(self):
        rows = simulate(**load("blocked"))
        self.assertEqual([r[2:] for r in rows[6:10]], [
            ((3, 2, 1), 1, None), ((3, 2, 1), 1, None),
            ((3, 2, None), 1, 1), ((3, None, 2), 1, None)])
        self.assertEqual([(r[0], r[4]) for r in rows if r[4]], [(8, 1), (10, 2), (12, 3)])
        self.assertEqual(rows[-1][2:], ((None, 4, None), 0, 3))

    def test_single_zone_has_no_same_tick_replacement(self):
        rows = simulate(**load("single"))
        self.assertEqual([(r[0], r[4]) for r in rows if r[4]], [(3, 1), (5, 2)])
        self.assertEqual(rows[-1][2:], ((3,), 0, None))

    def test_conservation_fifo_and_no_double_movement(self):
        arrivals = [0, 0, 1, 3]
        for zones in (1, 2, 3, 4):
            for flags in product((False, True), repeat=6):
                blocked = [t for t, stop in enumerate(flags) if stop]
                exited = []
                last = {}
                for t, stop, slots, waiting, depart in simulate(zones, 6, arrivals, blocked):
                    current = {box: i for i, box in enumerate(slots) if box is not None}
                    self.assertEqual(len(current), sum(box is not None for box in slots))
                    if depart is not None:
                        self.assertFalse(stop)
                        self.assertEqual(last[depart], zones - 1)
                        exited.append(depart)
                    self.assertEqual(exited, list(range(1, len(exited) + 1)))
                    self.assertEqual(len(current) + waiting + len(exited),
                                     sum(start <= t for start in arrivals))
                    for box, position in current.items():
                        if box in last:
                            self.assertIn(position - last[box], (0, 1))
                            if position != last[box]:
                                self.assertNotIn(position, last.values())
                        else:
                            self.assertEqual(position, 0)
                    last = current

    def test_empty_line_stays_empty(self):
        self.assertEqual(simulate(2, 2, [], [1]),
                         [(0, False, (None, None), 0, None), (1, True, (None, None), 0, None)])

    def test_invalid_scenarios(self):
        for args in [(0, 1, [], []), (True, 1, [], []), (1, 0, [], []),
                     (1, 2, [2], []), (1, 2, [1, 0], []),
                     (1, 2, [], [1, 1]), (1, 2, [True], [])]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                simulate(*args)

    def test_cli_summary_and_csv(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "trace.csv"
            result = subprocess.run([sys.executable, "conveyor.py", "examples/blocked.json",
                                     "--csv", str(target)], text=True, capture_output=True, check=True)
            self.assertEqual(result.stdout.splitlines(), [
                "Departures (package@tick): 1@8, 2@10, 3@12",
                "On conveyor: 1; waiting upstream: 0"])
            with target.open(newline="") as source:
                rows = list(csv.DictReader(source))
            self.assertEqual(len(rows), 13)
            self.assertEqual(rows[7], dict(tick="7", exit_blocked="1", zone_1="3",
                                          zone_2="2", zone_3="1", waiting="1", departed=""))
            self.assertEqual(rows[8]["departed"], "1")


if __name__ == "__main__":
    unittest.main()
