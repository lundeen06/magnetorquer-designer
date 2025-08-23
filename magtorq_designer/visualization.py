"""Visualization and plotting functionality."""

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np
import os
from typing import Dict, Any, List, Tuple
from pathlib import Path


class VisualizationEngine:
    """Handles visualization and plotting of magnetorquer designs."""
    
    def __init__(self):
        pass

    @staticmethod
    def ensure_output_directory(output_dir: str = "output") -> str:
        """Create output directory if it doesn't exist."""
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    @staticmethod
    def get_base_filename(design_file: str | Path) -> str:
        """Extract base filename from design file path."""
        filename = os.path.basename(str(design_file))
        if filename.endswith('-design.json'):
            return filename[:-12]  # Remove '-design.json'
        return os.path.splitext(filename)[0]

    def format_design_info(self, data: Dict[str, Any]) -> str:
        """Format complete design information for display."""
        info = []
        
        # Dimensions
        info.append("Dimensions:")
        info.append(f"  Outer: {data['dimensions']['outer']['length']:.1f}mm × {data['dimensions']['outer']['width']:.1f}mm")
        info.append(f"  Inner: {data['dimensions']['inner']['length']:.1f}mm × {data['dimensions']['inner']['width']:.1f}mm")
        
        # Traces
        info.append("\nTrace Design:")
        info.append(f"  Width: {data['traces']['width']:.3f}mm")
        info.append(f"  Spacing: {data['traces']['spacing']:.3f}mm")
        info.append(f"  Turns per layer: {data['traces']['turns_per_layer']}")
        info.append(f"  Total layers: {data['traces']['total_layers']}")
        info.append(f"  Total length: {data['traces']['total_length']:.2f}m")
        
        # Electrical
        info.append("\nElectrical Properties:")
        info.append(f"  Resistance: {data['electrical']['resistance']:.2f}Ω")
        info.append(f"  Voltage: {data['electrical']['voltage']:.1f}V")
        info.append(f"  Current: {data['electrical']['current']:.3f}A")
        info.append(f"  Current density: {data['electrical']['current_density']:.2f}A/mm²")
        info.append(f"  Power: {data['electrical']['power']:.2f}W")
        
        # Thermal
        info.append("\nThermal Analysis:")
        info.append("  Space Operation:")
        info.append(f"    Ambient: {data['thermal']['space']['ambient']:.1f}°C")
        info.append(f"    Rise: {data['thermal']['space']['temperature_rise']:.1f}°C")
        info.append(f"    Final: {data['thermal']['space']['final_temperature']:.1f}°C")

        # Dynamics
        info.append("\nDynamics Analysis:")
        info.append(f"    Inductance: {data['dynamics']['inductance']:.1f}μH")
        info.append(f"    Time constant: {data['dynamics']['time_constant']:.1f}ms")
        
        # Performance
        info.append("\nPerformance:")
        info.append(f"  Magnetic Moment: {data['performance']['magnetic_moment']:.4f} A·m²")
        
        return "\n".join(info)

    def generate_spiral_coordinates(self, params: Dict[str, float], layer_idx: int) -> List[Tuple[float, float]]:
        """Generate spiral coordinates for a magnetorquer layer."""
        outer_width = params['outer_width']
        outer_length = params['outer_length'] 
        inner_width = params['inner_width']
        inner_length = params['inner_length']
        trace_width = params['trace_width']
        trace_spacing = params['trace_spacing']
        num_turns = params['num_turns']
        
        # Calculate clearance
        min_inner_clearance = trace_width + 2 * trace_spacing
        effective_inner_length = inner_length + 2 * min_inner_clearance
        effective_inner_width = inner_width + 2 * min_inner_clearance
        
        paths = []
        turn_pitch = trace_width + trace_spacing
        
        # Direction: 0=right, 1=up, 2=left, 3=down
        direction = layer_idx % 2  # Alternate direction for different layers
        
        for turn in range(num_turns):
            offset = turn * turn_pitch
            
            # Calculate current rectangle
            current_outer_length = outer_length - 2 * offset  
            current_outer_width = outer_width - 2 * offset
            current_inner_length = effective_inner_length + 2 * offset
            current_inner_width = effective_inner_width + 2 * offset
            
            # Ensure we don't go beyond inner boundaries
            if current_outer_length <= current_inner_length or current_outer_width <= current_inner_width:
                break
                
            # Start position (bottom-left)
            start_x = -current_outer_width/2
            start_y = -current_outer_length/2
            
            # Create rectangular path
            corners = [
                (start_x, start_y),                           # Bottom-left
                (start_x + current_outer_width, start_y),     # Bottom-right
                (start_x + current_outer_width, start_y + current_outer_length), # Top-right
                (start_x, start_y + current_outer_length),    # Top-left
                (start_x, start_y),                           # Close the loop
            ]
            
            if direction == 1:  # Reverse for odd layers
                corners = corners[::-1]
                
            paths.extend(corners[:-1])  # Don't duplicate the closing point
            
        return paths

    def plot_layer(self, paths: List[Tuple[float, float]], params: Dict[str, float], 
                   design_data: Dict[str, Any], layer_num: int, 
                   output_dir: str, base_filename: str) -> None:
        """Plot a single layer of the magnetorquer."""
        fig, (ax_main, ax_info) = plt.subplots(1, 2, figsize=(16, 10), 
                                             gridspec_kw={'width_ratios': [3, 1]})
        
        if layer_num < params['num_layers'] - 1:
            # Regular coil layer
            if paths:
                # Convert paths to line segments for LineCollection
                segments = []
                for i in range(len(paths) - 1):
                    segments.append([paths[i], paths[i + 1]])
                
                lc = LineCollection(segments, colors='red', linewidths=2)
                ax_main.add_collection(lc)
        else:
            # H-bridge connection layer
            connector_width = 5.0
            connector_length = 8.0
            pin_radius = 0.6
            
            conn_x = params['outer_width']/2 + 1
            conn_y = 0
            
            connector = plt.Rectangle((conn_x, conn_y - connector_length/2),
                                    connector_width, connector_length,
                                    facecolor='lightgray', edgecolor='black')
            ax_main.add_patch(connector)
            
            pin_y_positions = [conn_y - 2, conn_y + 2]
            pin_x = conn_x + connector_width/2
            
            for i, pin_y in enumerate(pin_y_positions):
                pin = plt.Circle((pin_x, pin_y), pin_radius, 
                               facecolor='gold', edgecolor='black')
                ax_main.add_patch(pin)
                label = 'I' if i == 0 else 'O'
                ax_main.text(pin_x + 2*pin_radius, pin_y, label,
                          ha='left', va='center')
        
        # Draw board outline
        ax_main.add_patch(plt.Rectangle((-params['outer_width']/2, -params['outer_length']/2),
                                      params['outer_width'], params['outer_length'],
                                      fill=False, color='black', linewidth=2))
        ax_main.add_patch(plt.Rectangle((-params['inner_width']/2, -params['inner_length']/2),
                                      params['inner_width'], params['inner_length'],
                                      fill=False, color='black', linewidth=2))
        
        # Configure main plot
        ax_main.set_aspect('equal')
        margin = max(params['outer_width'], params['outer_length']) * 0.2
        ax_main.set_xlim(-params['outer_width']/2 - margin, params['outer_width']/2 + margin*1.5)
        ax_main.set_ylim(-params['outer_length']/2 - margin, params['outer_length']/2 + margin)
        
        title = f'{base_filename.replace("-", " ").title()} Layer {layer_num + 1}'
        if layer_num == params['num_layers'] - 1:
            title += ' (H-Bridge Connections)'
        ax_main.set_title(title)
        ax_main.grid(True, linestyle='--', alpha=0.3)
        
        # Add complete design information to right subplot
        ax_info.axis('off')
        info_text = self.format_design_info(design_data)
        ax_info.text(0, 1, info_text, 
                    fontsize=8, fontfamily='monospace',
                    verticalalignment='top',
                    bbox=dict(facecolor='white', alpha=0.8, pad=10))
        
        # Adjust layout and save
        plt.tight_layout()
        output_filename = f"{base_filename}-layer_{layer_num + 1}.png"
        output_path = os.path.join(output_dir, output_filename)
        plt.savefig(output_path, dpi=350, bbox_inches='tight')
        plt.close()  # Close the figure to free memory

    def create_layer_visualizations(self, design_data: Dict[str, Any], 
                                  design_file: str | Path,
                                  output_dir: str = "output") -> List[str]:
        """Create visualization of all layers with complete design information."""
        output_dir = self.ensure_output_directory(output_dir)
        base_filename = self.get_base_filename(design_file)
        
        params = {
            'inner_length': design_data['dimensions']['inner']['length'],
            'inner_width': design_data['dimensions']['inner']['width'],
            'outer_length': design_data['dimensions']['outer']['length'],
            'outer_width': design_data['dimensions']['outer']['width'],
            'trace_width': design_data['traces']['width'],
            'trace_spacing': design_data['traces']['spacing'],
            'num_turns': design_data['traces']['turns_per_layer'],
            'num_layers': design_data['traces']['total_layers']
        }
        
        output_files = []
        
        for i in range(params['num_layers']):
            paths = self.generate_spiral_coordinates(params, i)
            self.plot_layer(paths, params, design_data, i, output_dir, base_filename)
            output_files.append(f"{base_filename}-layer_{i + 1}.png")
        
        return output_files

    def create_summary_plot(self, design_data: Dict[str, Any], 
                          output_dir: str = "output",
                          base_filename: str = "magnetorquer") -> str:
        """Create a summary plot showing key design metrics."""
        plt.figure(figsize=(12, 8))
        
        # Extract key metrics
        moment = design_data['performance']['magnetic_moment']
        power = design_data['electrical']['power']
        temp_rise = design_data['thermal']['space']['temperature_rise']
        time_const = design_data['dynamics']['time_constant']
        
        # Create bar chart of key metrics
        metrics = ['Magnetic Moment\n(A·m²)', 'Power\n(W)', 'Temp Rise\n(°C)', 'Time Constant\n(ms)']
        values = [moment, power, temp_rise, time_const]
        
        bars = plt.bar(metrics, values, color=['blue', 'red', 'orange', 'green'])
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{value:.3f}', ha='center', va='bottom')
        
        plt.title(f'{base_filename.replace("-", " ").title()} - Key Performance Metrics')
        plt.ylabel('Value')
        plt.grid(True, alpha=0.3)
        
        # Save plot
        output_filename = f"{base_filename}-summary.png"
        output_path = os.path.join(output_dir, output_filename)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_filename