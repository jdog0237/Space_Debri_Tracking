# Space_Debri_Tracking
This is a Space Debris Tracking and Collision Risk Dashboard that will complete the set goals using vector mathematics, numerical simulation, and modular software design to deliver an end-to-end collision awareness system

GOALS:
To accept publicly available or synthetic debris catalogs containing position and velocity data for orbital objects. 

Using a simplified but effective constant-velocity propagation model, the system will simulate short-term motion over configurable time windows. For each debris object, the system computes key encounter metrics relative to a target spacecraft, including the minimum separation distance, time of closest approach, and relative velocity at encounter.

These metrics will then be combined into a transparent, interpretable risk score that allows objects to be ranked by collision severity. Results will be presented through a lightweight, interactive dashboard designed to resemble mission-operations tooling rather than high-fidelity orbital mechanics software. 

The interface will include a sortable alert table highlighting high-risk objects, a timeline of predicted close approaches, and simple visualizations of object motion and encounter geometry. 

The emphasis is on clarity, explainability, and rapid situational awareness rather than precise long-term orbital prediction.

## Running the project

From the repository root:

```bash
python3 main.py
```

## FR-1.1 CSV debris catalog format

The catalog CSV must include a header row and the following columns:

- `id` (or `debris_id` / `object_id`)
- `x`, `y`, `z` (position components)
- `vx`, `vy`, `vz` (velocity components)

Example:

```csv
id,x,y,z,vx,vy,vz
DEB-001,1000,2000,3000,1.2,-0.4,0.0
DEB-002,-500,0,1200,0.0,7.5,-1.1
```

Notes:

- Values must be numeric and finite (no blanks, `NaN`, or `inf`).
- Debris IDs must be non-empty and unique.

## Running tests

```bash
python3 -m unittest discover -s tests -q
```

