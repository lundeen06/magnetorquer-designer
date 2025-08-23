"""
Magtorq Designer: A comprehensive tool for designing and optimizing 
PCB-based magnetorquer coils for spacecraft attitude control.
"""

__version__ = "0.1.0"
__author__ = "Lundeen Cahilly"
__email__ = "lundeen.cahilly@gmail.com"

from .config import PCBConfig
from .optimizer import MagnetorquerDesigner
from .analysis import DesignAnalyzer
from .visualization import VisualizationEngine
from .pcb import PCBGenerator

__all__ = [
    "PCBConfig",
    "MagnetorquerDesigner", 
    "DesignAnalyzer",
    "VisualizationEngine",
    "PCBGenerator",
]