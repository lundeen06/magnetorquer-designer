"""Physics calculations for magnetorquer design."""

import numpy as np
from scipy.optimize import fsolve
from .config import PCBConfig


class PhysicsEngine:
    """Handles all physics calculations for magnetorquer design."""
    
    def __init__(self, config: PCBConfig):
        self.config = config
        self.copper_thickness = config.copper_weight * config.oz_to_m
        self.coil_layers = config.num_layers - 1  # One layer for connections

    def calculate_max_turns(self, trace_width: float) -> int:
        """Calculate maximum number of turns given trace width."""
        if trace_width <= 0:
            return 0
            
        # Reduce inner clearance needed - only need space for one trace and gap on each side
        min_inner_clearance = trace_width + 2 * self.config.min_trace_spacing
        
        # Calculate available space
        effective_inner_length = self.config.inner_length + 2 * min_inner_clearance
        effective_inner_width = self.config.inner_width + 2 * min_inner_clearance
        
        available_height = (self.config.outer_length - effective_inner_length) / 2
        available_width = (self.config.outer_width - effective_inner_width) / 2
        
        if available_height <= 0 or available_width <= 0:
            return 0
        
        # Each turn needs space for trace and spacing
        turn_pitch = trace_width + self.config.min_trace_spacing
        
        # Use the more constraining dimension
        max_turns_height = int(available_height / turn_pitch)
        max_turns_width = int(available_width / turn_pitch)
        return max(1, min(max_turns_height, max_turns_width))

    def calculate_turn_length(self, turn_number: int, trace_width: float) -> float:
        """Calculate length of a specific turn including connections."""
        offset = turn_number * (trace_width + self.config.min_trace_spacing)
        
        # Current rectangle dimensions
        current_length = self.config.outer_length - 2 * offset
        current_width = self.config.outer_width - 2 * offset
        
        # Main rectangular path
        perimeter = 2 * (current_length + current_width)
        
        # Add connection to next turn
        if turn_number < self.calculate_max_turns(trace_width) - 1:
            connection_length = trace_width + self.config.min_trace_spacing
        else:
            connection_length = trace_width + self.config.min_trace_spacing
            
        return perimeter + connection_length

    def calculate_turn_area(self, turn_number: int, trace_width: float) -> float:
        """Calculate area enclosed by a specific turn."""
        offset = turn_number * (trace_width + self.config.min_trace_spacing)
        length = self.config.outer_length - 2 * offset
        width = self.config.outer_width - 2 * offset
        return length * width

    def calculate_total_length(self, trace_width: float) -> float:
        """Calculate total wire length."""
        num_turns = self.calculate_max_turns(trace_width)
        if num_turns <= 0:
            return 0
        
        total_length = sum(self.calculate_turn_length(turn, trace_width) 
                          for turn in range(num_turns))
        return total_length * self.coil_layers

    def calculate_resistance(self, trace_width: float) -> float:
        """Calculate total resistance of coil."""
        total_length = self.calculate_total_length(trace_width)
        if total_length <= 0 or trace_width <= 0:
            return np.inf
            
        cross_section = self.copper_thickness * trace_width
        return self.config.copper_resistivity * total_length / cross_section

    def calculate_current(self, resistance: float, trace_width: float) -> float:
        """Calculate current given voltage, power, and current density constraints."""
        if resistance <= 0:
            return 0
        
        # Calculate maximum current from power limit
        # P = IV -> I = P/V
        max_current_from_power = self.config.max_power / self.config.voltage
        
        # Calculate maximum current from current density limit
        # J = I/A where A is cross-sectional area
        cross_section = trace_width * self.copper_thickness
        max_current_from_density = self.config.current_density_limit * cross_section
        
        # Calculate current from Ohm's law
        current_from_resistance = self.config.voltage / resistance
        
        # Take minimum of all constraints
        current = min(current_from_resistance, 
                     max_current_from_power,
                     max_current_from_density)
        
        return current

    def calculate_temperature_rise(self, power: float) -> float:
        """Calculate temperature rise in space (radiation only)."""
        # Stefan-Boltzmann constant
        stefan_boltzmann = 5.67e-8  # W/(m²·K⁴)
        
        # Radiating area (both sides of board)
        area = self.config.surface_area_multiplier * self.config.outer_length * self.config.outer_width
        
        # Space temperature (0°C in Kelvin)
        T_space = 273.15
        
        # Solve heat balance equation: P = εσA(T⁴ - T_space⁴)
        def heat_balance(T):
            radiation = (0.9 * stefan_boltzmann * area * (T**4 - T_space**4))
            return radiation - power
            
        T_final = fsolve(heat_balance, T_space + 5)[0]
        return T_final - T_space
    
    def calculate_inductance(self, trace_width: float) -> float:
        """Calculate inductance of PCB coil using Wheeler's formula for rectangular coils."""
        num_turns = self.calculate_max_turns(trace_width)
        if num_turns <= 0:
            return 0
            
        # Calculate average diameter 
        spacing = trace_width + self.config.min_trace_spacing
        avg_length = self.config.outer_length - spacing * num_turns
        avg_width = self.config.outer_width - spacing * num_turns
        avg_diameter = (avg_length + avg_width) / 2
        
        # Wheeler's formula for rectangular coils
        inductance = (31.33 * self.config.vacuum_permeability * 
                     num_turns**2 * avg_diameter / 8)
                     
        # Account for multiple layers
        inductance *= self.coil_layers
        
        return inductance

    def calculate_time_constant(self, trace_width: float) -> float:
        """Calculate the RL time constant (τ = L/R)."""
        inductance = self.calculate_inductance(trace_width)
        resistance = self.calculate_resistance(trace_width)
        
        if resistance <= 0:
            return 0
            
        tau = inductance / resistance
        return tau

    def calculate_time_to_percentage(self, trace_width: float, target_percentage: float) -> float:
        """Calculate time to reach a target percentage of final value."""
        tau = self.calculate_time_constant(trace_width)
        # Using the formula: percentage = 1 - e^(-t/tau)
        # Solving for t: t = -tau * ln(1 - percentage)
        return -tau * np.log(1 - target_percentage)

    def calculate_magnetic_moment(self, trace_width: float, current: float) -> float:
        """Calculate magnetic moment of coil."""
        num_turns = self.calculate_max_turns(trace_width)
        if num_turns <= 0 or current <= 0:
            return 0
        
        total_area = sum(self.calculate_turn_area(turn, trace_width) 
                        for turn in range(num_turns))
        return total_area * current * self.coil_layers

    def calculate_current_density(self, current: float, trace_width: float) -> float:
        """Calculate current density in A/m²."""
        cross_section = trace_width * self.copper_thickness
        if cross_section <= 0:
            return 0
        return current / cross_section

    def check_constraints(self, trace_width: float) -> bool:
        """Check all design constraints."""
        if (trace_width < self.config.min_trace_width or 
            trace_width > self.config.max_trace_width):
            return False
            
        resistance = self.calculate_resistance(trace_width)
        current = self.calculate_current(resistance, trace_width) 
        
        # Check current density limit
        current_density = self.calculate_current_density(current, trace_width)
        if current_density > self.config.current_density_limit:
            return False
        
        # Check power limit
        power = current * self.config.voltage
        if power > self.config.max_power:
            return False
        
        # Check thermal limit
        temp_rise = self.calculate_temperature_rise(power)
        if temp_rise > self.config.operating_temp - self.config.ambient_temp:
            return False
            
        return True