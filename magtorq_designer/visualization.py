"""Visualization and plotting functionality."""

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np
import os
import webbrowser
from typing import Dict, Any, List, Tuple
from pathlib import Path
import plotly.graph_objects as go
import plotly.io as pio


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
        """Generate coordinates for a realistic spiral with connections between turns."""
        inner_length = params['inner_length']
        inner_width = params['inner_width']
        outer_length = params['outer_length']
        outer_width = params['outer_width']
        trace_width = params['trace_width']
        trace_spacing = params['trace_spacing']
        num_turns = params['num_turns']
        
        paths = []
        turn_length = trace_spacing + trace_width
        
        # Start from outer edge
        for n in range(num_turns):
            # Calculate dimensions for this turn
            y_track_length = outer_length - 2*n*(trace_spacing+trace_width)
            x_track_length = outer_width - 2*n*(trace_spacing+trace_width)
            
            # Calculate starting positions
            x_start = -outer_width/2 + n*(trace_spacing+trace_width)
            y_start = -outer_length/2 + n*(trace_spacing+trace_width)
            x_end = x_start + x_track_length
            y_end = y_start + y_track_length
            y_2_end = y_end - trace_spacing - trace_width
            x_2_end = x_start + trace_spacing + trace_width
            
            # First turn special handling
            if n == 0:
                if layer_idx == 0:
                    # Input connection
                    paths.extend([
                        (x_start, y_end-turn_length),
                        (x_start, y_end+1.5*turn_length)
                    ])
                else:
                    # Connection to previous layer
                    paths.extend([
                        (x_start, y_end-turn_length),
                        (x_start+turn_length, y_end),
                        (x_start+2*(layer_idx+1)*turn_length+5, y_end),
                        (x_start+2*(layer_idx+1)*turn_length+6.5*turn_length, y_end+1.5*turn_length)
                    ])
            
            # Main spiral segments
            # Left vertical
            paths.extend([
                (x_start, y_start+turn_length),
                (x_start, y_end-turn_length)
            ])
            # Top left corner  
            paths.extend([
                (x_start, y_start+turn_length),
                (x_start+turn_length, y_start)
            ])
            # Top horizontal
            paths.extend([
                (x_start+turn_length, y_start),
                (x_end-turn_length, y_start)
            ])
            # Top right corner
            paths.extend([
                (x_end-turn_length, y_start),
                (x_end, y_start+turn_length)
            ])
            # Right vertical
            paths.extend([
                (x_end, y_start+turn_length),
                (x_end, y_2_end)
            ])
            # Bottom right corner
            paths.extend([
                (x_end, y_2_end),
                (x_end-turn_length, y_2_end)
            ])
            # Bottom horizontal (partial)
            paths.extend([
                (x_end-turn_length, y_2_end),
                (x_2_end, y_2_end)
            ])
            
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

    def create_interactive_layer_viewer(self, design_data: Dict[str, Any], 
                                      design_file: str | Path,
                                      output_dir: str = "output") -> str:
        """Create interactive Plotly visualization with toggleable layers."""
        os.makedirs(output_dir, exist_ok=True)
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
        
        # Create figure
        fig = go.Figure()
        
        # Generate viridis color scheme for layers
        num_layers = params['num_layers'] - 1  # Exclude H-bridge layer
        viridis_colors = plt.cm.viridis(np.linspace(0, 1, max(num_layers, 1)))
        layer_colors = [f'rgb({int(r*255)}, {int(g*255)}, {int(b*255)})' 
                       for r, g, b, _ in viridis_colors]
        
        # Add PCB outline traces
        self._add_pcb_outline(fig, params)
        
        # Add coil layers
        for layer_idx in range(params['num_layers'] - 1):  # Exclude H-bridge layer
            color = layer_colors[layer_idx % len(layer_colors)]
            self._add_coil_layer(fig, params, layer_idx, color, base_filename)
        
        # Add H-bridge connection layer
        if params['num_layers'] > 0:
            self._add_hbridge_layer(fig, params)
        
        # Update layout
        fig.update_layout(
            title=f"{base_filename.replace('-', ' ').title()} - Interactive Layer View",
            xaxis_title="Width (mm)",
            yaxis_title="Length (mm)",
            template="plotly_white",
            showlegend=True,
            legend=dict(
                x=1.02,
                y=1,
                xanchor="left",
                yanchor="top"
            ),
            width=1200,
            height=800,
            xaxis=dict(
                scaleanchor="y",
                scaleratio=1,
                showgrid=True,
                gridcolor="lightgray"
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="lightgray"
            ),
            hovermode='closest'
        )
        
        # Add design information as annotation
        info_text = self._get_design_info_text(design_data)
        fig.add_annotation(
            x=0.02,
            y=0.98,
            xref="paper",
            yref="paper",
            text=info_text,
            showarrow=False,
            font=dict(family="monospace", size=10),
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="gray",
            borderwidth=1,
            xanchor="left",
            yanchor="top"
        )
        
        # Save interactive HTML
        output_filename = f"{base_filename}-interactive-layers.html"
        output_path = os.path.join(output_dir, output_filename)
        fig.write_html(output_path)
        
        return output_path

    def _add_pcb_outline(self, fig: go.Figure, params: Dict[str, float]):
        """Add PCB outline traces to the figure."""
        # Outer board outline
        outer_x = [-params['outer_width']/2, params['outer_width']/2, 
                  params['outer_width']/2, -params['outer_width']/2, -params['outer_width']/2]
        outer_y = [-params['outer_length']/2, -params['outer_length']/2,
                  params['outer_length']/2, params['outer_length']/2, -params['outer_length']/2]
        
        fig.add_trace(go.Scatter(
            x=outer_x, y=outer_y,
            mode='lines',
            name='PCB Outline',
            line=dict(color='black', width=3),
            showlegend=True,
            hovertemplate="PCB Outer Boundary<extra></extra>"
        ))
        
        # Inner cutout outline
        inner_x = [-params['inner_width']/2, params['inner_width']/2,
                  params['inner_width']/2, -params['inner_width']/2, -params['inner_width']/2]
        inner_y = [-params['inner_length']/2, -params['inner_length']/2,
                  params['inner_length']/2, params['inner_length']/2, -params['inner_length']/2]
        
        fig.add_trace(go.Scatter(
            x=inner_x, y=inner_y,
            mode='lines',
            name='Inner Cutout',
            line=dict(color='black', width=2, dash='dash'),
            showlegend=True,
            hovertemplate="Inner Cutout<extra></extra>"
        ))

    def _add_coil_layer(self, fig: go.Figure, params: Dict[str, float], 
                       layer_idx: int, color: str, base_filename: str):
        """Add a single coil layer to the figure with proper trace width visualization."""
        paths = self.generate_spiral_coordinates(params, layer_idx)
        
        if not paths:
            return
        
        trace_width_mm = params['trace_width']
        layer_name = f'Layer {layer_idx + 1}'
        
        # Create filled rectangles for each line segment to show actual trace width
        for i in range(len(paths) - 1):
            start = paths[i]
            end = paths[i + 1]
            
            # Calculate perpendicular offset for trace width
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            length = np.sqrt(dx*dx + dy*dy)
            
            if length > 0:
                # Unit vector perpendicular to trace direction
                perp_x = -dy / length * trace_width_mm / 2
                perp_y = dx / length * trace_width_mm / 2
                
                # Create rectangle for this trace segment
                rect_x = [
                    start[0] + perp_x, start[0] - perp_x,
                    end[0] - perp_x, end[0] + perp_x, start[0] + perp_x
                ]
                rect_y = [
                    start[1] + perp_y, start[1] - perp_y,
                    end[1] - perp_y, end[1] + perp_y, start[1] + perp_y
                ]
                
                # Add filled rectangle - only show legend for first segment
                fig.add_trace(go.Scatter(
                    x=rect_x,
                    y=rect_y,
                    mode='lines',
                    fill='toself',
                    fillcolor=color,
                    line=dict(color=color, width=0.5),
                    name=layer_name,
                    showlegend=(i == 0),  # Only show legend for first segment
                    legendgroup=layer_name,  # Group all segments under same layer
                    hovertemplate=f"{layer_name}<br>Trace Width: {trace_width_mm:.3f}mm<extra></extra>"
                ))
                                      
        # Note: base_filename used for context but not needed in this implementation


    def _add_hbridge_layer(self, fig: go.Figure, params: Dict[str, float]):
        """Add H-bridge connection layer to the figure."""
        # H-bridge connector dimensions
        connector_width = 5.0
        connector_length = 8.0
        pin_radius = 0.6
        
        conn_x = params['outer_width']/2 + 1
        conn_y = 0
        
        # Add connector rectangle
        connector_x = [conn_x, conn_x + connector_width, conn_x + connector_width, conn_x, conn_x]
        connector_y = [conn_y - connector_length/2, conn_y - connector_length/2,
                      conn_y + connector_length/2, conn_y + connector_length/2, conn_y - connector_length/2]
        
        fig.add_trace(go.Scatter(
            x=connector_x,
            y=connector_y,
            mode='lines',
            fill='toself',
            fillcolor='rgba(211,211,211,0.6)',
            line=dict(color='gray', width=2),
            name='H-Bridge Connector',
            showlegend=True,
            hovertemplate="H-Bridge Connection Layer<extra></extra>"
        ))
        
        # Add pins
        pin_y_positions = [conn_y - 2, conn_y + 2]
        pin_x = conn_x + connector_width/2
        
        for i, pin_y in enumerate(pin_y_positions):
            # Create circle for pin
            theta = np.linspace(0, 2*np.pi, 20)
            pin_x_coords = pin_x + pin_radius * np.cos(theta)
            pin_y_coords = pin_y + pin_radius * np.sin(theta)
            
            label = 'Input Pin' if i == 0 else 'Output Pin'
            fig.add_trace(go.Scatter(
                x=pin_x_coords,
                y=pin_y_coords,
                mode='lines',
                fill='toself',
                fillcolor='gold',
                line=dict(color='goldenrod', width=1),
                name=label,
                showlegend=True,
                hovertemplate=f"{label}<extra></extra>"
            ))

    def _get_design_info_text(self, design_data: Dict[str, Any]) -> str:
        """Get condensed design information for annotation."""
        info_lines = [
            f"<b>Design Specifications</b>",
            f"Magnetic Moment: {design_data['performance']['magnetic_moment']:.4f} A·m²",
            f"Power: {design_data['electrical']['power']:.2f}W",
            f"Current: {design_data['electrical']['current']:.3f}A", 
            f"Temp Rise: {design_data['thermal']['space']['temperature_rise']:.1f}°C",
            f"Layers: {design_data['traces']['total_layers']}",
            f"Turns/Layer: {design_data['traces']['turns_per_layer']}",
            f"Trace Width: {design_data['traces']['width']:.3f}mm",
            f"Copper Weight: {design_data['traces']['copper_weight']:.0f}oz"
        ]
        return "<br>".join(info_lines)

    def open_interactive_viewer(self, design_data: Dict[str, Any], 
                              design_file: str | Path) -> str:
        """Create and open interactive layer viewer in browser."""
        output_path = self.create_interactive_layer_viewer(design_data, design_file)
        webbrowser.open('file://' + os.path.abspath(output_path))
        return output_path