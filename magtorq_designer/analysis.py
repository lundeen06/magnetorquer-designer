"""Design analysis and performance metrics."""

from typing import Dict, Any, Tuple
import numpy as np
from .config import PCBConfig
from .physics import PhysicsEngine


class DesignAnalyzer:
    """Analyzes magnetorquer design results and calculates performance metrics."""
    
    def __init__(self, config: PCBConfig):
        self.config = config
        self.physics = PhysicsEngine(config)

    def calculate_power_efficiency(self, moment: float, current: float) -> float:
        """Calculate power efficiency as magnetic moment per watt of input power."""
        power = current * self.config.voltage
        
        if power <= 0:
            return 0
            
        return moment / power  # Units: (A·m²) / W = A·m²/W

    def calculate_thermal_efficiency(self, moment: float, current: float) -> float:
        """Calculate thermal efficiency as moment per degree C rise."""
        power = current * self.config.voltage
        temp_rise = self.physics.calculate_temperature_rise(power)
        
        if temp_rise <= 0:
            return 0
            
        return moment / temp_rise

    def analyze_design(self, trace_width: float) -> Dict[str, Any]:
        """Analyze design results for given trace width."""
        # Basic calculations
        resistance = self.physics.calculate_resistance(trace_width)
        current = self.physics.calculate_current(resistance, trace_width)
        num_turns = self.physics.calculate_max_turns(trace_width)
        total_length = self.physics.calculate_total_length(trace_width)
        
        # Performance metrics
        power = current * self.config.voltage
        temp_rise = self.physics.calculate_temperature_rise(power)
        moment = self.physics.calculate_magnetic_moment(trace_width, current)
        current_density = self.physics.calculate_current_density(current, trace_width)
        
        # Time constant metrics
        inductance = self.physics.calculate_inductance(trace_width)
        time_constant = self.physics.calculate_time_constant(trace_width)
        time_to_99_percent = self.physics.calculate_time_to_percentage(trace_width, 0.99)
        
        return {
            "dimensions": {
                "inner": {
                    "length": round(self.config.inner_length * 1000, 1),    # mm
                    "width": round(self.config.inner_width * 1000, 1)       # mm
                },
                "outer": {
                    "length": round(self.config.outer_length * 1000, 1),    # mm
                    "width": round(self.config.outer_width * 1000, 1)       # mm
                }
            },
            "traces": {
                "width": round(trace_width * 1000, 3),                      # mm      
                "spacing": round(self.config.min_trace_spacing * 1000, 3),  # mm
                "turns_per_layer": num_turns,                               # [dimensionless]
                "total_layers": self.config.num_layers,                     # [dimensionless]
                "total_length": round(total_length, 1),                     # m
                "copper_weight": self.config.copper_weight                  # oz
            },
            "electrical": {
                "resistance": round(resistance, 2),                         # Ω
                "voltage": round(self.config.voltage, 2),                   # V
                "current": round(current, 2),                               # A
                "power": round(power, 2),                                   # W
                "current_density": round(current_density/1e6, 2)            # A/mm^2
            },
            "thermal": {
                "space": {
                    "ambient": 0.0,                                         # ºC
                    "temperature_rise": round(temp_rise, 2),                # ºC
                    "final_temperature": round(temp_rise, 2)                # ºC
                }
            },
            "dynamics": {
                "inductance": round(inductance * 1000, 3),                  # μH
                "time_constant": round(time_constant * 1000, 2),            # ms
                "time_to_99_percent": round(time_to_99_percent * 1000, 2),  # ms
                "max_moment_99_percent": round(moment * 0.99, 4)             # A·m²
            },
            "performance": {
                "magnetic_moment": round(moment, 4)                         # A·m²
            },
        }

    def analyze_efficiency_curves(self, trace_widths: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Analyze efficiency curves for given trace width range."""
        moments = []
        power_efficiencies = []
        thermal_efficiencies = []
        
        for width in trace_widths:
            if not self.physics.check_constraints(width):
                moments.append(0)
                power_efficiencies.append(0)
                thermal_efficiencies.append(0)
                continue
                
            resistance = self.physics.calculate_resistance(width)
            current = self.physics.calculate_current(resistance, width)
            moment = self.physics.calculate_magnetic_moment(width, current)
            
            moments.append(moment)
            power_efficiencies.append(self.calculate_power_efficiency(moment, current))
            thermal_efficiencies.append(self.calculate_thermal_efficiency(moment, current))
        
        return np.array(moments), np.array(power_efficiencies), np.array(thermal_efficiencies)

    def find_optimal_designs(self, trace_widths: np.ndarray) -> Dict[str, Tuple[float, float]]:
        """Find optimal trace widths for different criteria."""
        moments, power_effs, thermal_effs = self.analyze_efficiency_curves(trace_widths)
        
        # Find best designs
        best_moment_idx = np.argmax(moments)
        best_power_idx = np.argmax(power_effs)
        best_thermal_idx = np.argmax(thermal_effs)
        
        # Calculate time constants for comparison
        time_constants = []
        for width in trace_widths:
            if self.physics.check_constraints(width):
                time_constants.append(self.physics.calculate_time_constant(width))
            else:
                time_constants.append(np.inf)
        
        time_constants = np.array(time_constants)
        best_tau_idx = np.argmin(time_constants)
        
        return {
            "max_moment": (trace_widths[best_moment_idx], moments[best_moment_idx]),
            "max_power_efficiency": (trace_widths[best_power_idx], power_effs[best_power_idx]),
            "max_thermal_efficiency": (trace_widths[best_thermal_idx], thermal_effs[best_thermal_idx]),
            "min_time_constant": (trace_widths[best_tau_idx], time_constants[best_tau_idx]),
        }

    def get_design_summary(self, trace_width: float) -> str:
        """Get a formatted summary of the design."""
        analysis = self.analyze_design(trace_width)
        
        summary = []
        summary.append("=== Magnetorquer Design Summary ===")
        summary.append(f"Trace Width: {analysis['traces']['width']:.3f} mm")
        summary.append(f"Turns per Layer: {analysis['traces']['turns_per_layer']}")
        summary.append(f"Total Layers: {analysis['traces']['total_layers']}")
        summary.append(f"Magnetic Moment: {analysis['performance']['magnetic_moment']:.4f} A·m²")
        summary.append(f"Current: {analysis['electrical']['current']:.3f} A")
        summary.append(f"Power: {analysis['electrical']['power']:.2f} W")
        summary.append(f"Temperature Rise: {analysis['thermal']['space']['temperature_rise']:.1f} °C")
        summary.append(f"Time Constant: {analysis['dynamics']['time_constant']:.2f} ms")
        
        return "\n".join(summary)