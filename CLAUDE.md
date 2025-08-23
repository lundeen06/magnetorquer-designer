# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Core Development Commands

### Design Optimization
```bash
# Run the magnetorquer design optimizer with a constraints file
python design.py constraints/xy-magnetorquer-constraints.json
python design.py constraints/z-magnetorquer-constraints.json
```

### Generate Visualizations
```bash
# Create layer-by-layer PNG visualizations from a design file
python 2d-sketch.py designs/xy-magnetorquer-design.json
python 2d-sketch.py designs/z-magnetorquer-design.json
```

### KiCad PCB Generation
1. Open KiCad PCB Editor
2. Open Python console (Tools > Scripting Console)
3. Copy and paste functions from `kicad.py` into the console
4. Update `DESIGN_PARAMS` dictionary with values from your `design.json` file
5. Run `main()` in the console

## Architecture Overview

### Core Components

**`design.py`** - Main optimization engine
- Contains `MagnetorquerDesigner` class with physics-based optimization
- Uses SLSQP (Sequential Least Squares Programming) to maximize magnetic moment
- Balances constraints: thermal limits, power limits, manufacturing constraints
- Outputs design specifications as JSON and interactive Plotly analysis plots

**`2d-sketch.py`** - Visualization generator
- Takes design JSON files and generates layer-by-layer PNG visualizations
- Shows spiral coil patterns, trace routing, and H-bridge connections
- Includes complete design specifications as text overlay

**`kicad.py`** - PCB generation utilities
- Functions for creating KiCad PCB traces programmatically
- Must be run inside KiCad's Python console environment
- Generates actual PCB layouts from optimized designs

### Configuration System

**Constraints Files** (`constraints/`)
- JSON configuration files defining design parameters
- Structure: `physical_constants`, `thermal_properties`, `design_constraints`, `manufacturing_constraints`
- Separate files for different magnetorquer orientations (xy vs z)

**Design Files** (`designs/`)
- JSON output from optimization containing complete design specifications
- Used as input for visualization and KiCad generation
- Contains dimensions, traces, electrical properties, thermal analysis, and performance metrics

### Optimization Physics

The optimization process solves a complex multi-physics problem:

1. **Magnetic Moment Maximization**: μ = n × I × A × L (turns × current × area × layers)
2. **Thermal Analysis**: Solves heat equation with temperature-dependent resistance
3. **Current Limitations**: Constrained by voltage, thermal limits, and current density
4. **Manufacturing Constraints**: Minimum trace width/spacing, layer count limitations

Key constraint equations:
- Power: I²R ≤ P_max
- Thermal: T_final ≤ T_max  
- Current density: I/(w×t) ≤ j_max
- Geometry: n_turns × (w + s) ≤ available_space

### Project Structure
```
constraints/           # Input constraint files
designs/              # Generated design specifications (JSON)
output/               # Layer visualization images (PNG)
plots/                # Analysis plots (HTML/PNG)
```

## Dependencies
- Python 3.7+
- NumPy, SciPy (optimization and math)
- Matplotlib (visualization)
- Plotly (interactive plots)
- KiCad 6.0+ (for PCB generation)

## Development Notes

- The system is optimized for spacecraft magnetorquer design with specific thermal and power constraints
- Each run generates interactive HTML plots that automatically open in browser
- Design files are used as intermediate format between optimization and downstream tools
- KiCad integration requires manual console execution due to KiCad's Python environment limitations