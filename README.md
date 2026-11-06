# Conveyor automation: simulate a three zone buffer

Use a Python model to answer one question: when the downstream machine stops taking boxes, where does each box wait and in what order does the line restart?

The complete lesson is at https://wifarobotics.com/learn/conveyor-automation/. This project is an offline model. It contains no PLC code, actuator output, or hardware test.

## Start from zero

1. Install Python 3.10 or newer from https://www.python.org/downloads/. On Windows, the Python launcher may use the command `py -3` instead of `python3`.
2. Open the green Code menu on the project page, select Download ZIP, and extract it. Alternatively, with Git installed, run `git clone https://github.com/williamfarokhzad/wifa-conveyor-automation.git`.
3. Open a terminal in the extracted folder containing `conveyor.py`. Confirm `python3 --version` reports Python 3.10 or newer. No package installation is needed to run the model or tests.

## Run and inspect

```sh
python3 conveyor.py examples/open.json
python3 conveyor.py examples/blocked.json --csv blocked-trace.csv
python3 conveyor.py examples/single.json
python3 -m unittest discover -s tests -v
```

| Scenario | Departures as package@tick | On conveyor | Waiting upstream |
|---|---|---:|---:|
| open | 1@3, 2@5, 3@7, 4@9 | 0 | 0 |
| blocked | 1@8, 2@10, 3@12 | 1 | 0 |
| single | 1@3, 2@5 | 1 | 0 |

Open the CSV in a text editor or spreadsheet. Rows show the state **after** each tick, from tick zero. Blank zone cells mean empty. The value 1 in the exit_blocked column means that the modeled downstream receiver refuses a package on that tick. Waiting counts packages outside the conveyor.

The scenario fields are `zones` (1 to 20), `ticks` (1 to 10,000), `arrivals` (sorted zero based tick numbers; repeats allow simultaneous arrivals), and `blocked_ticks` (distinct zero based tick numbers). The line begins empty. The model uses a queue and a start of tick snapshot to decide transfers. Each package moves at most one step per tick. A slot occupied at the start cannot accept a replacement in that tick. With three zones, the first package enters on tick 0, reaches the last zone on tick 2, and exits on tick 3 if allowed.

## Try a change

Copy blocked.json and change ticks from 13 to 15. Predict the last departure before running. Package 4 is in zone 2 after tick 12, enters zone 3 on tick 13, and departs on tick 14. If you remove every blocked tick, compare against the open case. Changing the number of zones affects storage and initial transit time. Ticks here have no physical duration.

## Troubleshooting

If Python cannot find conveyor.py, move into the folder where it was extracted. If Windows does not recognize python3, use py -3. If the scenario is rejected, use strict JSON, keep arrivals sorted, and use tick numbers smaller than ticks. If a parcel remains when the run ends, extend ticks; the final row is only a snapshot, and a package cannot depart while the exit is blocked. If the CSV cannot be written, close the spreadsheet holding it and use a writable path.

## What the model leaves out

A simulated slot is an occupancy bit plus a package ID. It does not represent package length, overhang, braking distance, a photoeye signal, drive response, communication delay or an emergency stop. The model does not establish physical clearance, safety, or production throughput. It implements conservative teaching logic inspired by single release, not a vendor controller.

The figures are in diagrams/. To regenerate them separately, install Pillow in a virtual environment, make DejaVu Sans and DejaVu Sans Bold available to Pillow, then run `python3 diagrams/render.py`. This is optional and independent of the simulator. Their descriptions are in diagrams/ALT.md.
