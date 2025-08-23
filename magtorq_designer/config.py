"""Configuration management for magnetorquer design."""

from dataclasses import dataclass
from typing import Dict, Any
import json
from pathlib import Path


@dataclass
class PCBConfig:
    """Configuration loaded from JSON file"""
    # Physical constants
    vacuum_permeability: float
    copper_resistivity: float
    temperature_coefficient: float
    oz_to_m: float
    current_density_limit: float
    
    # Thermal properties
    thermal_conductivity_copper: float
    thermal_conductivity_fr4: float
    fr4_thickness: float
    surface_area_multiplier: float
    
    # Design constraints
    num_layers: int
    copper_weight: float
    max_power: float
    voltage: float
    inner_length: float
    inner_width: float
    outer_length: float
    outer_width: float
    operating_temp: float
    ambient_temp: float
    
    # Manufacturing constraints
    min_trace_width: float
    max_trace_width: float
    min_trace_spacing: float
    
    @classmethod
    def from_json(cls, config: Dict[str, Any]) -> 'PCBConfig':
        """Create PCBConfig from JSON dictionary"""
        return cls(
            # Physical constants
            vacuum_permeability=config['physical_constants']['vacuum_permeability'],
            copper_resistivity=config['physical_constants']['copper_resistivity'],
            temperature_coefficient=config['physical_constants']['temperature_coefficient'],
            oz_to_m=config['physical_constants']['oz_to_m'],
            current_density_limit=config['physical_constants']['current_density_limit'],
            
            # Thermal properties
            thermal_conductivity_copper=config['thermal_properties']['thermal_conductivity_copper'],
            thermal_conductivity_fr4=config['thermal_properties']['thermal_conductivity_fr4'],
            fr4_thickness=config['thermal_properties']['fr4_thickness'],
            surface_area_multiplier=config['thermal_properties']['surface_area_multiplier'],
            
            # Design constraints
            num_layers=config['design_constraints']['num_layers'],
            copper_weight=config['design_constraints']['copper_weight'],
            max_power=config['design_constraints']['max_power'],
            voltage=config['design_constraints']['voltage'],
            inner_length=config['design_constraints']['inner_length'],
            inner_width=config['design_constraints']['inner_width'],
            outer_length=config['design_constraints']['outer_length'],
            outer_width=config['design_constraints']['outer_width'],
            operating_temp=config['design_constraints']['operating_temp'],
            ambient_temp=config['design_constraints']['ambient_temp'],
            
            # Manufacturing constraints
            min_trace_width=config['manufacturing_constraints']['min_trace_width'],
            max_trace_width=config['manufacturing_constraints']['max_trace_width'],
            min_trace_spacing=config['manufacturing_constraints']['min_trace_spacing']
        )

    @classmethod
    def from_file(cls, file_path: str | Path) -> 'PCBConfig':
        """Load configuration from JSON file"""
        with open(file_path, 'r') as f:
            config_data = json.load(f)
        return cls.from_json(config_data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary format"""
        return {
            "physical_constants": {
                "vacuum_permeability": self.vacuum_permeability,
                "copper_resistivity": self.copper_resistivity,
                "temperature_coefficient": self.temperature_coefficient,
                "oz_to_m": self.oz_to_m,
                "current_density_limit": self.current_density_limit,
            },
            "thermal_properties": {
                "thermal_conductivity_copper": self.thermal_conductivity_copper,
                "thermal_conductivity_fr4": self.thermal_conductivity_fr4,
                "fr4_thickness": self.fr4_thickness,
                "surface_area_multiplier": self.surface_area_multiplier,
            },
            "design_constraints": {
                "num_layers": self.num_layers,
                "copper_weight": self.copper_weight,
                "max_power": self.max_power,
                "voltage": self.voltage,
                "inner_length": self.inner_length,
                "inner_width": self.inner_width,
                "outer_length": self.outer_length,
                "outer_width": self.outer_width,
                "operating_temp": self.operating_temp,
                "ambient_temp": self.ambient_temp,
            },
            "manufacturing_constraints": {
                "min_trace_width": self.min_trace_width,
                "max_trace_width": self.max_trace_width,
                "min_trace_spacing": self.min_trace_spacing,
            }
        }

    def save_to_file(self, file_path: str | Path) -> None:
        """Save configuration to JSON file"""
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)