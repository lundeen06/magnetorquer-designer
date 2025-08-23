"""PCB generation utilities for KiCad integration."""

from typing import Dict, Any, Optional, List
import json
import os


class PCBGenerator:
    """Handles PCB generation for KiCad integration."""
    
    def __init__(self):
        self.kicad_available = self._check_kicad_availability()
    
    def _check_kicad_availability(self) -> bool:
        """Check if KiCad Python API is available."""
        try:
            import pcbnew
            return True
        except ImportError:
            return False

    def generate_kicad_script(self, design_data: Dict[str, Any]) -> str:
        """Generate KiCad Python script from design data."""
        
        script = f'''#!/usr/bin/env python3

"""
Optimized KiCad script for magnetorquer coil generation
Run this directly in KiCad's PCB Editor Python Console (Tools > Scripting Console)

USAGE: Copy and paste this entire script into the KiCad python console, then run main()
"""

from pcbnew import *

# Design parameters (from optimized design)
DESIGN_PARAMS = {json.dumps(design_data, indent=2)}

def get_inner_copper_layer_ids(board):
    """Get layer IDs for inner copper layers"""
    layer_count = board.GetCopperLayerCount()
    inner_layers = []
    
    if layer_count > 2:
        for i in range(1, layer_count - 1):
            inner_layers.append(i)
    
    return inner_layers

def delete_all_tracks(board):
    """Delete all existing tracks on the board"""
    for track in list(board.GetTracks()):
        board.RemoveNative(track)

def draw_trace(board, x0, y0, x1, y1, width, layer):
    """Draw a trace segment"""
    track = PCB_TRACK(board)
    track.SetStart(VECTOR2I(int(x0 * 1000000), int(y0 * 1000000)))  # Convert to nanometers
    track.SetEnd(VECTOR2I(int(x1 * 1000000), int(y1 * 1000000)))
    track.SetWidth(int(width * 1000000))  # Convert to nanometers
    track.SetLayer(layer)
    board.Add(track)
    return track

def draw_via(board, x, y, hole_size, outer_diameter):
    """Draw a via at specified position"""
    via = PCB_VIA(board)
    via.SetPosition(VECTOR2I(int(x * 1000000), int(y * 1000000)))  # Convert to nanometers
    via.SetDrillDefault()
    via.SetWidth(int(outer_diameter * 1000000))  # Convert to nanometers
    board.Add(via)
    return via

def generate_coil_traces(board, design_params):
    """Generate magnetorquer coil traces based on design parameters"""
    # Clear existing tracks
    delete_all_tracks(board)
    
    # Extract parameters
    dimensions = design_params['dimensions']
    traces = design_params['traces']
    
    outer_length = dimensions['outer']['length'] / 1000  # Convert mm to meters
    outer_width = dimensions['outer']['width'] / 1000
    inner_length = dimensions['inner']['length'] / 1000
    inner_width = dimensions['inner']['width'] / 1000
    
    trace_width = traces['width'] / 1000  # Convert mm to meters
    trace_spacing = traces['spacing'] / 1000
    turns_per_layer = traces['turns_per_layer']
    total_layers = traces['total_layers']
    
    # Get layer information
    inner_layers = get_inner_copper_layer_ids(board)
    coil_layers = min(total_layers - 1, len(inner_layers) + 2)  # Include top and bottom
    
    # Generate traces for each layer
    layers_to_use = [F_Cu] + inner_layers[:coil_layers-2] + [B_Cu] if coil_layers > 1 else [F_Cu]
    
    for layer_idx, layer in enumerate(layers_to_use):
        if layer_idx >= coil_layers - 1:  # Skip H-bridge layer
            break
            
        # Calculate clearance
        min_inner_clearance = trace_width + 2 * trace_spacing
        effective_inner_length = inner_length + 2 * min_inner_clearance
        effective_inner_width = inner_width + 2 * min_inner_clearance
        
        turn_pitch = trace_width + trace_spacing
        
        for turn in range(turns_per_layer):
            offset = turn * turn_pitch
            
            # Calculate current rectangle dimensions
            current_outer_length = outer_length - 2 * offset
            current_outer_width = outer_width - 2 * offset
            current_inner_length = effective_inner_length + 2 * offset
            current_inner_width = effective_inner_width + 2 * offset
            
            # Check if we can fit this turn
            if current_outer_length <= current_inner_length or current_outer_width <= current_inner_width:
                break
            
            # Calculate corner positions (centered at origin)
            half_length = current_outer_length / 2
            half_width = current_outer_width / 2
            
            # Define rectangle corners
            corners = [
                (-half_width, -half_length),  # Bottom-left
                (half_width, -half_length),   # Bottom-right
                (half_width, half_length),    # Top-right
                (-half_width, half_length),   # Top-left
            ]
            
            # Draw the rectangular turn
            for i in range(len(corners)):
                start = corners[i]
                end = corners[(i + 1) % len(corners)]
                draw_trace(board, start[0], start[1], end[0], end[1], trace_width, layer)
    
    # Add connection vias between layers if multiple layers
    if len(layers_to_use) > 1:
        # Place via at outer edge for layer connections
        via_x = outer_width / 2 - trace_width
        via_y = 0
        draw_via(board, via_x, via_y, 0.0002, 0.0004)  # 0.2mm hole, 0.4mm outer diameter

def main():
    """Main function to generate magnetorquer coil"""
    # Get the current board
    board = GetBoard()
    if not board:
        print("Error: No board found. Please open a PCB in KiCad first.")
        return
    
    try:
        # Generate coil traces
        generate_coil_traces(board, DESIGN_PARAMS)
        
        # Refresh the display
        Refresh()
        
        print("Magnetorquer coil generated successfully!")
        print(f"Magnetic moment: {{DESIGN_PARAMS['performance']['magnetic_moment']:.4f}} A·m²")
        print(f"Power: {{DESIGN_PARAMS['electrical']['power']:.2f}} W")
        print(f"Current: {{DESIGN_PARAMS['electrical']['current']:.3f}} A")
        
    except Exception as e:
        print(f"Error generating coil: {{e}}")

# Uncomment the next line to run automatically (or call main() manually)
# main()
'''
        
        return script

    def save_kicad_script(self, design_data: Dict[str, Any], 
                         output_dir: str = "output",
                         base_filename: str = "magnetorquer") -> str:
        """Save KiCad script to file."""
        os.makedirs(output_dir, exist_ok=True)
        
        script_content = self.generate_kicad_script(design_data)
        script_filename = os.path.join(output_dir, f"{base_filename}-kicad.py")
        
        with open(script_filename, 'w') as f:
            f.write(script_content)
        
        return script_filename

    def get_kicad_instructions(self) -> str:
        """Get instructions for using the generated KiCad script."""
        instructions = '''
KiCad PCB Generation Instructions:

1. Open KiCad PCB Editor
2. Create a new PCB or open an existing one
3. Set up your board with the correct number of layers (as specified in your design)
4. Open the Python console: Tools > Scripting Console
5. Copy and paste the generated KiCad script into the console
6. Run main() in the console

The script will:
- Clear any existing tracks
- Generate coil traces on appropriate layers
- Add vias for layer connections
- Display generation results

Note: Make sure your PCB board size matches or exceeds the outer dimensions
specified in your magnetorquer design.
'''
        return instructions

    def export_design_summary(self, design_data: Dict[str, Any],
                            output_dir: str = "output", 
                            base_filename: str = "magnetorquer") -> str:
        """Export a comprehensive design summary."""
        os.makedirs(output_dir, exist_ok=True)
        
        summary = {
            "design_specifications": design_data,
            "manufacturing_notes": {
                "pcb_requirements": {
                    "layers": design_data['traces']['total_layers'],
                    "min_trace_width": f"{design_data['traces']['width']:.3f} mm",
                    "min_trace_spacing": f"{design_data['traces']['spacing']:.3f} mm",
                    "outer_dimensions": f"{design_data['dimensions']['outer']['length']} x {design_data['dimensions']['outer']['width']} mm",
                    "inner_cutout": f"{design_data['dimensions']['inner']['length']} x {design_data['dimensions']['inner']['width']} mm"
                },
                "electrical_specs": {
                    "operating_voltage": f"{design_data['electrical']['voltage']} V",
                    "max_current": f"{design_data['electrical']['current']:.3f} A",
                    "power_consumption": f"{design_data['electrical']['power']:.2f} W",
                    "resistance": f"{design_data['electrical']['resistance']:.2f} Ω"
                },
                "performance": {
                    "magnetic_moment": f"{design_data['performance']['magnetic_moment']:.4f} A·m²",
                    "time_constant": f"{design_data['dynamics']['time_constant']:.2f} ms",
                    "thermal_rise": f"{design_data['thermal']['space']['temperature_rise']:.1f} °C"
                }
            },
            "kicad_instructions": self.get_kicad_instructions()
        }
        
        summary_filename = os.path.join(output_dir, f"{base_filename}-manufacturing-summary.json")
        with open(summary_filename, 'w') as f:
            json.dump(summary, f, indent=2)
        
        return summary_filename