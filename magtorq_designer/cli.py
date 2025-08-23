"""Beautiful CLI interface for Magtorq Designer."""

import typer
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint
from rich.layout import Layout
from rich.text import Text
from pathlib import Path
import json
import os
import webbrowser
from typing import Optional, Dict, Any

from .config import PCBConfig
from .optimizer import MagnetorquerDesigner
from .visualization import VisualizationEngine
from .pcb import PCBGenerator
from .analysis import DesignAnalyzer


app = typer.Typer(
    name="magnetorquer-designer",
    help="🧲 Magnetorquer Designer - Design and optimize PCB-based magnetorquer coils for spacecraft",
    add_completion=False
)

console = Console()


def print_banner():
    """Print the application banner."""
    banner = """
[white]███╗   ███╗  █████╗   ██████╗ ████████╗  ██████╗  ██████╗   ██████╗ 
████╗ ████║ ██╔══██╗ ██╔════╝ ╚══██╔══╝ ██╔═══██╗ ██╔══██╗ ██╔═══██╗
██╔████╔██║ ███████║ ██║  ███╗   ██║    ██║   ██║ ██████╔╝ ██║   ██║
██║╚██╔╝██║ ██╔══██║ ██║   ██║   ██║    ██║   ██║ ██╔══██╗ ██║▄▄ ██║
██║ ╚═╝ ██║ ██║  ██║ ╚██████╔╝   ██║    ╚██████╔╝ ██║  ██║ ╚██████╔╝
╚═╝     ╚═╝ ╚═╝  ╚═╝  ╚═════╝    ╚═╝     ╚═════╝  ╚═╝  ╚═╝  ╚══▀▀═╝[/white] 

[dim]Multi-physics magnetorquer design optimization tool for spacecraft attitude control.
Originally developed for Stanford SSI's 2U CubeSat SAMWISE.[/dim]
"""
    console.print(banner)


def create_constraints_interactively() -> Dict[str, Any]:
    """Create design constraints through interactive prompts."""
    console.print("\n📐 Design Constraints Setup", style="bold cyan")
    console.print("Let's configure your magnetorquer design parameters...\n")
    
    # Physical Constants (with reasonable defaults)
    console.print("⚡ Physical Constants", style="bold white")
    
    # Design Constraints  
    console.print("\n🎯 Design Requirements", style="bold white")
    
    num_layers = questionary.select(
        "Number of PCB layers:",
        choices=["4", "6", "8", "10"],
        default="6"
    ).ask()
    
    copper_weight = questionary.select(
        "Copper weight (oz):",
        choices=["1", "2", "3", "4"],
        default="2"
    ).ask()
    
    max_power = questionary.text(
        "Maximum power (W):",
        default="4.0",
        validate=lambda x: x.replace(".", "").replace("-", "").isdigit()
    ).ask()
    
    voltage = questionary.text(
        "Operating voltage (V):",
        default="8.2", 
        validate=lambda x: x.replace(".", "").replace("-", "").isdigit()
    ).ask()
    
    console.print("\n📏 Board Dimensions", style="bold white")
    
    outer_length = questionary.text(
        "Outer length (mm):",
        default="132.0",
        validate=lambda x: x.replace(".", "").isdigit()
    ).ask()
    
    outer_width = questionary.text(
        "Outer width (mm):",  
        default="61.0",
        validate=lambda x: x.replace(".", "").isdigit()
    ).ask()
    
    inner_length = questionary.text(
        "Inner cutout length (mm):",
        default="97.0",
        validate=lambda x: x.replace(".", "").isdigit()
    ).ask()
    
    inner_width = questionary.text(
        "Inner cutout width (mm):",
        default="25.0", 
        validate=lambda x: x.replace(".", "").isdigit()
    ).ask()
    
    console.print("\n🌡️ Thermal Limits", style="bold white")
    
    operating_temp = questionary.text(
        "Maximum operating temperature (°C):",
        default="65",
        validate=lambda x: x.replace("-", "").isdigit()
    ).ask()
    
    # Create the configuration dictionary
    config = {
        "physical_constants": {
            "vacuum_permeability": 1.25663706e-6,
            "copper_resistivity": 1.68e-8, 
            "temperature_coefficient": 0.00393,
            "oz_to_m": 0.0347e-3,
            "current_density_limit": 35e6
        },
        "thermal_properties": {
            "thermal_conductivity_copper": 385,
            "thermal_conductivity_fr4": 0.3,
            "fr4_thickness": 0.0016,
            "surface_area_multiplier": 2
        },
        "design_constraints": {
            "num_layers": int(num_layers),
            "copper_weight": float(copper_weight),
            "max_power": float(max_power),
            "voltage": float(voltage),
            "inner_length": float(inner_length) / 1000,  # Convert mm to m
            "inner_width": float(inner_width) / 1000,
            "outer_length": float(outer_length) / 1000,
            "outer_width": float(outer_width) / 1000,
            "operating_temp": float(operating_temp),
            "ambient_temp": 20.0
        },
        "manufacturing_constraints": {
            "min_trace_width": 0.00015,  # 0.15mm
            "max_trace_width": 0.0010,   # 1.0mm  
            "min_trace_spacing": 0.00015 # 0.15mm
        }
    }
    
    return config


def display_results_table(results: Dict[str, Any]):
    """Display optimization results in a formatted table."""
    table = Table(title="🎯 Optimization Results", show_header=True, header_style="bold cyan")
    
    table.add_column("Parameter", style="cyan", width=25)
    table.add_column("Value", style="white", width=20)
    table.add_column("Unit", style="white", width=15)
    
    # Dimensions
    table.add_section()
    table.add_row("📏 Board Dimensions", "", "")
    table.add_row("  Outer (L×W)", 
                 f"{results['dimensions']['outer']['length']:.1f} × {results['dimensions']['outer']['width']:.1f}",
                 "mm")
    table.add_row("  Inner (L×W)",
                 f"{results['dimensions']['inner']['length']:.1f} × {results['dimensions']['inner']['width']:.1f}", 
                 "mm")
    
    # Trace Design
    table.add_section()
    table.add_row("🔧 Trace Design", "", "")
    table.add_row("  Width", f"{results['traces']['width']:.3f}", "mm")
    table.add_row("  Copper Weight", f"{results['traces']['copper_weight']:.0f}", "oz")
    table.add_row("  Spacing", f"{results['traces']['spacing']:.3f}", "mm") 
    table.add_row("  Turns/Layer", str(results['traces']['turns_per_layer']), "")
    table.add_row("  Total Layers", str(results['traces']['total_layers']), "")
    table.add_row("  Total Length", f"{results['traces']['total_length']:.2f}", "m")
    
    # Electrical Properties
    table.add_section() 
    table.add_row("⚡ Electrical", "", "")
    table.add_row("  Resistance", f"{results['electrical']['resistance']:.2f}", "Ω")
    table.add_row("  Current", f"{results['electrical']['current']:.3f}", "A")
    table.add_row("  Power", f"{results['electrical']['power']:.2f}", "W")
    table.add_row("  Current Density", f"{results['electrical']['current_density']:.2f}", "A/mm²")
    
    # Thermal Analysis
    table.add_section()
    table.add_row("🌡️ Thermal", "", "")
    table.add_row("  Temperature Rise", f"{results['thermal']['space']['temperature_rise']:.1f}", "°C")
    table.add_row("  Final Temperature", f"{results['thermal']['space']['final_temperature']:.1f}", "°C")
    
    # Performance
    table.add_section()
    table.add_row("🚀 Performance", "", "") 
    table.add_row("  Magnetic Moment", f"{results['performance']['magnetic_moment']:.4f}", "A·m²")
    table.add_row("  Inductance", f"{results['dynamics']['inductance']:.1f}", "μH")
    table.add_row("  Time Constant", f"{results['dynamics']['time_constant']:.2f}", "ms")
    
    console.print(table)


@app.command()
def interactive():
    """🎯 Interactive magnetorquer design mode (recommended)."""
    print_banner()
    
    console.print("Welcome to the interactive magnetorquer designer! 🚀", style="bold white")
    console.print("This wizard will guide you through the complete design process.\n")
    
    # Main menu loop
    while True:
        choice = questionary.select(
            "What would you like to do?",
            choices=[
                "🎯 Design new magnetorquer",
                "📁 Load existing constraints",
                "📊 Analyze existing design", 
                "🔧 Generate KiCad PCB",
                "📈 View design plots",
                "❌ Exit"
            ]
        ).ask()
        
        if choice == "❌ Exit":
            console.print("\n👋 Thank you for using Magnetorquer Designer!", style="bold white")
            break
            
        elif choice == "🎯 Design new magnetorquer":
            design_new_magnetorquer()
            
        elif choice == "📁 Load existing constraints":
            load_and_optimize()
            
        elif choice == "📊 Analyze existing design":
            analyze_existing_design()
            
        elif choice == "🔧 Generate KiCad PCB":
            generate_pcb_files()
            
        elif choice == "📈 View design plots":
            view_design_plots()


def design_new_magnetorquer():
    """Design a new magnetorquer from scratch."""
    try:
        # Create constraints interactively
        config_dict = create_constraints_interactively()
        
        # Ask for save location
        save_name = questionary.text(
            "\n💾 Save this configuration as:",
            default="my-magnetorquer"
        ).ask()
        
        if not save_name:
            save_name = "my-magnetorquer"
            
        # Ensure directories exist
        os.makedirs("constraints", exist_ok=True)
        os.makedirs("designs", exist_ok=True)
        os.makedirs("plots", exist_ok=True)
        os.makedirs("output", exist_ok=True)
        
        # Save constraints
        constraints_file = f"constraints/{save_name}-constraints.json"
        with open(constraints_file, 'w') as f:
            json.dump(config_dict, f, indent=2)
        
        console.print(f"\n💾 Saved constraints to: {constraints_file}", style="green")
        
        # Run optimization
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("🔄 Optimizing magnetorquer design...", total=None)
            
            config = PCBConfig.from_json(config_dict)
            designer = MagnetorquerDesigner(config)
            result, moment_data, thermal_data, power_data, tau_data = designer.optimize()
        
        # Display results
        console.print("\n✅ Optimization completed successfully!", style="bold green")
        display_results_table(result)
        
        # Save results 
        json_file, html_file = designer.save_results(result, moment_data, power_data, save_name)
        console.print(f"\n📁 Results saved:")
        console.print(f"  📊 Design specs: {json_file}", style="cyan")
        console.print(f"  📈 Analysis plots: {html_file}", style="cyan")
        
        # Ask what to do next
        next_action = questionary.select(
            "\nWhat would you like to do next?",
            choices=[
                "📈 Open analysis plots",
                "🖼️ Generate layer visualizations", 
                "🔧 Generate KiCad script",
                "🔙 Return to main menu"
            ]
        ).ask()
        
        if next_action == "📈 Open analysis plots":
            webbrowser.open('file://' + os.path.abspath(html_file))
            
        elif next_action == "🖼️ Generate layer visualizations":
            generate_visualizations(result, f"designs/{save_name}-design.json")
            
        elif next_action == "🔧 Generate KiCad script":
            generate_kicad_script(result, save_name)
            
    except Exception as e:
        console.print(f"\n❌ Error during design: {e}", style="bold red")


def load_and_optimize():
    """Load existing constraints file and optimize."""
    # Find constraint files
    if not os.path.exists("constraints"):
        console.print("❌ No constraints directory found. Please create a new design first.", style="red")
        return
        
    constraint_files = [f for f in os.listdir("constraints") if f.endswith("-constraints.json")]
    
    if not constraint_files:
        console.print("❌ No constraint files found in constraints/ directory.", style="red")
        return
    
    # Select constraints file
    selected_file = questionary.select(
        "Select constraints file:",
        choices=constraint_files
    ).ask()
    
    if not selected_file:
        return
        
    try:
        constraints_path = f"constraints/{selected_file}"
        config = PCBConfig.from_file(constraints_path)
        
        base_name = selected_file.replace("-constraints.json", "")
        
        # Run optimization
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("🔄 Optimizing design...", total=None)
            
            designer = MagnetorquerDesigner(config)
            result, moment_data, thermal_data, power_data, tau_data = designer.optimize()
        
        console.print("\n✅ Optimization completed!", style="bold white") 
        display_results_table(result)
        
        # Save results
        json_file, html_file = designer.save_results(result, moment_data, power_data, base_name)
        console.print(f"\n📁 Results saved to: {json_file}", style="cyan")
        
    except Exception as e:
        console.print(f"\n❌ Error: {e}", style="bold red")


def analyze_existing_design():
    """Analyze an existing design file."""
    if not os.path.exists("designs"):
        console.print("❌ No designs directory found.", style="red")
        return
        
    design_files = [f for f in os.listdir("designs") if f.endswith("-design.json")]
    
    if not design_files:
        console.print("❌ No design files found in designs/ directory.", style="red")
        return
    
    selected_file = questionary.select(
        "Select design file to analyze:",
        choices=design_files
    ).ask()
    
    if not selected_file:
        return
        
    try:
        with open(f"designs/{selected_file}", 'r') as f:
            design_data = json.load(f)
        
        display_results_table(design_data)
        
    except Exception as e:
        console.print(f"\n❌ Error loading design: {e}", style="bold red")


def generate_visualizations(design_data: Dict[str, Any], design_file: str):
    """Generate layer visualizations."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("🖼️ Generating layer visualizations...", total=None)
            
            viz = VisualizationEngine()
            output_files = viz.create_layer_visualizations(design_data, design_file)
        
        console.print(f"\n✅ Generated {len(output_files)} layer visualizations:", style="bold white")
        for file in output_files:
            console.print(f"  🖼️ output/{file}", style="cyan")
            
    except Exception as e:
        console.print(f"\n❌ Error generating visualizations: {e}", style="bold red")


def generate_kicad_script(design_data: Dict[str, Any], base_name: str):
    """Generate KiCad script."""
    try:
        pcb_gen = PCBGenerator()
        script_file = pcb_gen.save_kicad_script(design_data, base_filename=base_name)
        summary_file = pcb_gen.export_design_summary(design_data, base_filename=base_name)
        
        console.print(f"\n✅ KiCad files generated:", style="bold white")
        console.print(f"  🔧 Script: {script_file}", style="cyan")
        console.print(f"  📋 Summary: {summary_file}", style="cyan")
        
        console.print(f"\n📖 KiCad Instructions:", style="bold white")
        console.print(pcb_gen.get_kicad_instructions())
        
    except Exception as e:
        console.print(f"\n❌ Error generating KiCad files: {e}", style="bold red")


def generate_pcb_files():
    """Generate KiCad PCB files from existing design."""
    if not os.path.exists("designs"):
        console.print("❌ No designs directory found.", style="red")
        return
        
    design_files = [f for f in os.listdir("designs") if f.endswith("-design.json")]
    
    if not design_files:
        console.print("❌ No design files found.", style="red")
        return
    
    selected_file = questionary.select(
        "Select design file for PCB generation:",
        choices=design_files
    ).ask()
    
    if not selected_file:
        return
        
    try:
        with open(f"designs/{selected_file}", 'r') as f:
            design_data = json.load(f)
        
        base_name = selected_file.replace("-design.json", "")
        generate_kicad_script(design_data, base_name)
        
    except Exception as e:
        console.print(f"\n❌ Error: {e}", style="bold red")


def view_design_plots():
    """View existing design plots."""
    if not os.path.exists("plots"):
        console.print("❌ No plots directory found.", style="red")
        return
        
    plot_files = [f for f in os.listdir("plots") if f.endswith("-design-analysis.html")]
    
    if not plot_files:
        console.print("❌ No plot files found.", style="red")
        return
    
    selected_file = questionary.select(
        "Select plot file to view:",
        choices=plot_files
    ).ask()
    
    if not selected_file:
        return
        
    plot_path = os.path.abspath(f"plots/{selected_file}")
    webbrowser.open('file://' + plot_path)
    console.print(f"📈 Opened plot: {selected_file}", style="white")


@app.command()
def optimize(
    constraints_file: Path = typer.Argument(..., help="Path to constraints JSON file"),
    output_dir: Optional[str] = typer.Option("designs", help="Output directory for results")
):
    """🚀 Optimize magnetorquer design from constraints file."""
    
    if not constraints_file.exists():
        console.print(f"❌ Constraints file not found: {constraints_file}", style="bold red")
        raise typer.Exit(1)
    
    try:
        # Load configuration
        config = PCBConfig.from_file(constraints_file)
        base_name = constraints_file.stem.replace("-constraints", "")
        
        # Run optimization
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Optimizing design...", total=None)
            
            designer = MagnetorquerDesigner(config)
            result, moment_data, thermal_data, power_data, tau_data = designer.optimize()
        
        # Save results
        json_file, html_file = designer.save_results(result, moment_data, power_data, base_name, output_dir)
        
        console.print("✅ Optimization completed successfully!", style="bold white")
        console.print(f"📁 Results saved to: {json_file}", style="cyan")
        console.print(f"📈 Analysis plots: {html_file}", style="cyan")
        
        display_results_table(result)
        
    except Exception as e:
        console.print(f"❌ Error during optimization: {e}", style="bold red")
        raise typer.Exit(1)


@app.command()
def visualize(
    design_file: Path = typer.Argument(..., help="Path to design JSON file"),
    output_dir: Optional[str] = typer.Option("output", help="Output directory for visualizations")
):
    """🖼️ Generate layer visualizations from design file."""
    
    if not design_file.exists():
        console.print(f"❌ Design file not found: {design_file}", style="bold red")
        raise typer.Exit(1)
    
    try:
        with open(design_file, 'r') as f:
            design_data = json.load(f)
        
        viz = VisualizationEngine()
        output_files = viz.create_layer_visualizations(design_data, design_file, output_dir)
        
        console.print(f"✅ Generated {len(output_files)} visualizations:", style="bold white")
        for file in output_files:
            console.print(f"  🖼️ {output_dir}/{file}", style="cyan")
            
    except Exception as e:
        console.print(f"❌ Error generating visualizations: {e}", style="bold red")
        raise typer.Exit(1)


@app.command() 
def pcb(
    design_file: Path = typer.Argument(..., help="Path to design JSON file"),
    output_dir: Optional[str] = typer.Option("output", help="Output directory for PCB files")
):
    """🔧 Generate KiCad PCB files from design."""
    
    if not design_file.exists():
        console.print(f"❌ Design file not found: {design_file}", style="bold red")
        raise typer.Exit(1)
    
    try:
        with open(design_file, 'r') as f:
            design_data = json.load(f)
        
        base_name = design_file.stem.replace("-design", "")
        
        pcb_gen = PCBGenerator()
        script_file = pcb_gen.save_kicad_script(design_data, output_dir, base_name)
        summary_file = pcb_gen.export_design_summary(design_data, output_dir, base_name)
        
        console.print("✅ KiCad files generated:", style="bold white")
        console.print(f"  🔧 Script: {script_file}", style="cyan")
        console.print(f"  📋 Summary: {summary_file}", style="cyan")
        
        console.print("\n📖 Usage Instructions:", style="bold white")
        console.print(pcb_gen.get_kicad_instructions())
        
    except Exception as e:
        console.print(f"❌ Error generating PCB files: {e}", style="bold red")
        raise typer.Exit(1)


def main():
    """Main entry point."""
    import sys
    # If no arguments provided, default to interactive mode
    if len(sys.argv) == 1:
        interactive()
    else:
        app()


if __name__ == "__main__":
    main()