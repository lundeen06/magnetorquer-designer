"""Magnetorquer design optimization engine."""

from typing import Dict, Any, Tuple, List
import numpy as np
from scipy.optimize import minimize
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import webbrowser
import os

from .config import PCBConfig
from .physics import PhysicsEngine
from .analysis import DesignAnalyzer


class MagnetorquerDesigner:
    """Main optimization engine for magnetorquer design."""
    
    def __init__(self, config: PCBConfig):
        self.config = config
        self.physics = PhysicsEngine(config)
        self.analyzer = DesignAnalyzer(config)

    def objective_function(self, trace_width: float) -> float:
        """Objective function to maximize (negative because minimize() minimizes)."""
        if not self.physics.check_constraints(trace_width):
            return -1e-10  # Very small negative value for infeasible solutions
            
        resistance = self.physics.calculate_resistance(trace_width)
        current = self.physics.calculate_current(resistance, trace_width)
        moment = self.physics.calculate_magnetic_moment(trace_width, current)
        
        return -moment  # Negative because we want to maximize

    def optimize(self, num_points: int = 5000) -> Tuple[Dict[str, Any], 
                                                        Tuple[np.ndarray, np.ndarray, float, float],
                                                        Tuple[np.ndarray, np.ndarray, float, float], 
                                                        Tuple[np.ndarray, np.ndarray, float, float],
                                                        Tuple[np.ndarray, np.ndarray, float, float]]:
        """
        Optimize magnetorquer design.
        
        Returns:
            Tuple containing:
            - Design analysis dictionary
            - Moment data: (widths, moments, best_width, best_moment)
            - Thermal efficiency data: (widths, thermal_eff, best_width, best_thermal)
            - Power efficiency data: (widths, power_eff, best_width, best_power)  
            - Time constant data: (widths, time_constants, best_width, best_tau)
        """
        # Create trace width range
        widths = np.linspace(
            self.config.min_trace_width, 
            self.config.max_trace_width, 
            num_points
        )
        
        # Calculate performance curves
        moments, power_effs, thermal_effs = self.analyzer.analyze_efficiency_curves(widths)
        
        # Calculate time constants
        time_constants = []
        for width in widths:
            if self.physics.check_constraints(width):
                time_constants.append(self.physics.calculate_time_constant(width))
            else:
                time_constants.append(np.inf)
        time_constants = np.array(time_constants)
        
        # Find optimal points
        valid_moments = moments[moments > 0]
        if len(valid_moments) == 0:
            raise ValueError("No feasible solutions found. Check your constraints.")
        
        best_moment_idx = np.argmax(moments)
        best_power_idx = np.argmax(power_effs)  
        best_thermal_idx = np.argmax(thermal_effs)
        best_tau_idx = np.argmin(time_constants)
        
        # Extract best values
        best_moment_width = widths[best_moment_idx]
        best_moment = moments[best_moment_idx]
        
        best_power_width = widths[best_power_idx]
        best_power = power_effs[best_power_idx]
        
        best_thermal_width = widths[best_thermal_idx]
        best_thermal = thermal_effs[best_thermal_idx]
        
        best_tau_width = widths[best_tau_idx]
        best_tau = time_constants[best_tau_idx]
        
        # Analyze the optimal design
        result = self.analyzer.analyze_design(best_moment_width)
        
        # Return data in the format expected by the plotting function
        moment_data = (widths, moments, best_moment_width, best_moment)
        thermal_data = (widths, thermal_effs, best_thermal_width, best_thermal)
        power_data = (widths, power_effs, best_power_width, best_power)
        tau_data = (widths, time_constants, best_tau_width, best_tau)
        
        return result, moment_data, thermal_data, power_data, tau_data

    def create_analysis_plots(self, 
                            moment_data: Tuple[np.ndarray, np.ndarray, float, float],
                            power_data: Tuple[np.ndarray, np.ndarray, float, float],
                            base_filename: str) -> go.Figure:
        """Create interactive analysis plots."""
        widths, moments, best_moment_width, best_moment = moment_data
        _, power_eff, best_power_width, best_power = power_data
        
        # Create figure with subplots (1x2 grid)
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=(
                'Magnetic Moment vs Trace Width', 
                'Power Efficiency (Am²/W) vs Trace Width',
            ),
            horizontal_spacing=0.15,
        )

        # Plot 1: Moment vs Width
        fig.add_trace(
            go.Scatter(
                x=widths * 1000,  # Convert to mm
                y=moments,
                mode='lines',
                name='Magnetic Moment',
                line=dict(color='rgb(0, 123, 255)', width=2)
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=[best_moment_width * 1000],  # Convert to mm
                y=[best_moment],
                mode='markers',
                name='Maximum Moment',
                marker=dict(
                    color='rgb(220, 53, 69)',
                    size=12,
                    symbol='star-diamond',
                    line=dict(color='rgb(150, 20, 30)', width=2)
                )
            ),
            row=1, col=1
        )

        # Plot 2: Power Efficiency
        fig.add_trace(
            go.Scatter(
                x=widths * 1000,  # Convert to mm
                y=power_eff,
                mode='lines',
                name='Power Efficiency',
                line=dict(color='rgb(111, 66, 193)', width=2)
            ),
            row=1, col=2
        )
        
        fig.add_trace(
            go.Scatter(
                x=[best_power_width * 1000],  # Convert to mm
                y=[best_power],
                mode='markers',
                name='Best Power Efficiency',
                marker=dict(
                    color='rgb(128, 0, 128)',
                    size=12,
                    symbol='star-diamond',
                    line=dict(color='rgb(76, 0, 76)', width=2)
                )
            ),
            row=1, col=2
        )

        # Update axes labels
        fig.update_xaxes(
            title='Trace Width (mm)',
            gridcolor='lightgray',
            showgrid=True,
        )

        # Update y-axis titles
        fig.update_yaxes(title='Magnetic Moment (A·m²)', row=1, col=1)
        fig.update_yaxes(title='Moment/Power (A·m²/W)', row=1, col=2)

        # Update overall layout
        fig.update_layout(
            height=500,
            width=1400,
            showlegend=True,
            template='plotly_white',
            hovermode='x unified',
            title=f"{base_filename.replace('-', ' ').title()} Design Analysis Plots"
        )

        return fig

    def save_results(self, result: Dict[str, Any], 
                    moment_data: Tuple[np.ndarray, np.ndarray, float, float],
                    power_data: Tuple[np.ndarray, np.ndarray, float, float],
                    base_filename: str,
                    output_dir: str = "designs",
                    plots_dir: str = "plots") -> Tuple[str, str]:
        """Save optimization results and plots."""
        import json
        
        # Ensure directories exist
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(plots_dir, exist_ok=True)
        
        # Save JSON file
        json_filename = os.path.join(output_dir, f'{base_filename}-design.json')
        with open(json_filename, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Create and save plots
        fig = self.create_analysis_plots(moment_data, power_data, base_filename)
        
        html_filename = os.path.join(plots_dir, f'{base_filename}-design-analysis.html')
        png_filename = os.path.join(plots_dir, f'{base_filename}-design-analysis.png')
        
        fig.write_html(html_filename)
        pio.write_image(fig, png_filename)
        
        return json_filename, html_filename