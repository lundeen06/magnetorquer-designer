# Magnetorquer Designer - PCB-based magnetorquer optimization for spacecraft attitude control

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

```
███╗   ███╗  █████╗   ██████╗ ████████╗  ██████╗  ██████╗   ██████╗ 
████╗ ████║ ██╔══██╗ ██╔════╝ ╚══██╔══╝ ██╔═══██╗ ██╔══██╗ ██╔═══██╗
██╔████╔██║ ███████║ ██║  ███╗   ██║    ██║   ██║ ██████╔╝ ██║   ██║
██║╚██╔╝██║ ██╔══██║ ██║   ██║   ██║    ██║   ██║ ██╔══██╗ ██║▄▄ ██║
██║ ╚═╝ ██║ ██║  ██║ ╚██████╔╝   ██║    ╚██████╔╝ ██║  ██║ ╚██████╔╝
╚═╝     ╚═╝ ╚═╝  ╚═╝  ╚═════╝    ╚═╝     ╚═════╝  ╚═╝  ╚═╝  ╚══▀▀═╝ 
```

**Multi-physics magnetorquer design optimization tool for spacecraft attitude control systems. Originally developed for Stanford SSI's 2U CubeSat SAMWISE.**

## Design Challenge

Spacecraft attitude control systems require magnetorquers that deliver maximum magnetic moment within strict power, thermal, and manufacturing constraints. Traditional design approaches rely on iterative prototyping and testing, resulting in suboptimal performance and extended development cycles.

The fundamental challenge lies in the coupled nature of magnetorquer design parameters: trace geometry affects resistance, which determines current capacity, which impacts both magnetic moment and thermal dissipation. Optimizing these interdependent variables simultaneously requires sophisticated multi-physics modeling.

Magnetorquer Designer solves this optimization problem using physics-based modeling and advanced numerical methods, delivering manufacturing-ready designs that maximize performance within mission constraints.

## Applications

- **CubeSats & Small Satellites** - Attitude control systems optimized for power and thermal budgets
- **Spacecraft Development** - Professional-grade magnetorquer design for mission-critical applications  
- **Research & Development** - Design optimization for specific mission requirements
- **Educational Projects** - Engineering education with real spacecraft design tools
- **Rapid Prototyping** - Accelerated development from requirements to manufacturing

Successfully deployed on Stanford SSI's SAMWISE CubeSat and other spacecraft missions.

## Design Workflow

1. **Requirements Definition** - Specify power budget, thermal limits, PCB constraints, and performance goals
2. **Multi-Physics Optimization** - Advanced algorithms balance magnetic, thermal, electrical, and manufacturing constraints
3. **Performance Analysis** - Complete design specifications with trade-off visualizations
4. **Manufacturing Output** - KiCad PCB files, layer visualizations, and manufacturing documentation
5. **Implementation** - Ready-to-manufacture designs with validated performance

## Key Capabilities

- **Multi-Physics Optimization** - Simultaneous magnetic, thermal, electrical, and manufacturing constraint satisfaction
- **Space-Grade Thermal Modeling** - Radiation-only heat transfer analysis for vacuum operation
- **Manufacturing Integration** - Direct KiCad PCB generation and manufacturing documentation
- **Interactive Design Interface** - Guided workflow with professional visualization tools
- **Physics-Based Analysis** - Rigorous inductance modeling, current density analysis, and thermal calculations
- **Performance Visualization** - Interactive plots showing design trade-offs and optimization results

<img src="output/z-magnetorquer-layer_2.png" width="600" alt="Magnetorquer Layer Example">

## Installation & Usage

### Installation

```bash
git clone https://github.com/yourusername/magtorq-designer
cd magtorq-designer
pip install -e .
```

### Interactive Mode (Recommended)

```bash
magnetorquer-designer
```

Launches an interactive design workflow with guided parameter input and real-time optimization.

### Command Line Interface

```bash
# Optimize from constraints file
magnetorquer-designer optimize constraints/my-design-constraints.json

# Generate layer visualizations
magnetorquer-designer visualize designs/my-design.json  

# Generate KiCad PCB files
magnetorquer-designer pcb designs/my-design.json
```

## Optimization Physics

### Objective Function

Maximize magnetic moment subject to multi-physics constraints:

```
μ = n × I × A × L
where:
n = number of turns per layer
I = operating current  
A = area per turn
L = number of layers
```

### Thermal Constraint Model

Space operation thermal equilibrium (radiation-only heat transfer):

```
Power dissipation: P = I²R
Thermal balance: P = εσA(T⁴ - T_space⁴)
where:
ε = surface emissivity
σ = Stefan-Boltzmann constant
A = radiating surface area
T = operating temperature
```

### Electrical Constraints

Current limitations from multiple sources:

```
I = min(V/R, P_max/V, j_max × A_copper)
where:
V/R = voltage/resistance limit
P_max/V = power budget limit  
j_max × A_copper = current density limit
```

### Manufacturing Constraints

PCB fabrication and assembly limits:

```
Trace width: w ≥ w_min (typically 0.15mm)
Trace spacing: s ≥ s_min (typically 0.15mm)  
Current density: j ≤ j_max (typically 35 A/mm² for 2oz Cu)
```

### Optimization Algorithm

Sequential Least Squares Programming (SLSQP) with constraint formulation:

```python
# Constraint equations
g1: I²R ≤ P_max                    # Power limit
g2: T_final ≤ T_max                # Thermal limit  
g3: I/(w×t) ≤ j_max               # Current density
g4: n×(w+s) ≤ (d_outer-d_inner)/2 # Geometric fit
g5: w ≥ w_min, s ≥ s_min          # Manufacturing
```

## Design Trade-offs

Understanding fundamental magnetorquer design trade-offs:

- **Power vs Performance** - Higher power enables greater magnetic moment, limited by thermal constraints
- **Geometry vs Efficiency** - Larger coil areas improve efficiency but may exceed size constraints  
- **Manufacturing vs Performance** - Tighter tolerances enable better designs at higher cost
- **Complexity vs Reliability** - More PCB layers increase performance but reduce reliability

## Output Documentation

### Design Files
- `designs/design-name.json` - Complete design specifications and performance metrics
- `plots/design-name-analysis.html` - Interactive optimization and trade-off analysis
- `output/design-name-layer_*.png` - Individual PCB layer visualizations
- `output/design-name-kicad.py` - KiCad Python script for PCB generation

### Performance Metrics
- Magnetic moment and efficiency calculations
- Thermal analysis and temperature rise predictions  
- Electrical characteristics and power consumption
- Manufacturing specifications and constraints verification

## Mission Heritage

**Stanford SSI SAMWISE CubeSat**
- Mission: 2U CubeSat with attitude determination and control
- Performance: 0.135 A⋅m² magnetic moment at 1W power consumption
- Thermal: <40°C temperature rise in space environment
- Implementation: 6-layer PCB with 0.24mm optimized trace geometry
- Status: Successfully deployed and operating in orbit

## Technical Requirements

### Design Inputs
- Mission power budget and thermal limits
- PCB dimensional constraints and layer count
- Manufacturing capabilities (trace width/spacing limits)
- Attitude control performance requirements

### Manufacturing Prerequisites  
- PCB fabrication capabilities matching design specifications
- Standard multilayer PCB assembly processes
- Access to KiCad or compatible PCB design tools

## Architecture

- `config.py` - Configuration management and constraint handling
- `physics.py` - Electrical, thermal, and magnetic field calculations  
- `optimizer.py` - Multi-physics optimization engine with SLSQP solver
- `analysis.py` - Performance metrics and design trade-off analysis
- `visualization.py` - PCB layer plotting and result visualization
- `pcb.py` - KiCad integration and PCB file generation
- `cli.py` - Interactive command-line interface

## Dependencies

- NumPy, SciPy - Numerical computation and optimization
- Matplotlib - Static visualization and plotting
- Plotly - Interactive analysis plots and dashboards  
- Rich, Questionary - Professional command-line interface
- KiCad 6.0+ - PCB design and manufacturing file generation

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Advancing spacecraft attitude control through optimized magnetorquer design.**