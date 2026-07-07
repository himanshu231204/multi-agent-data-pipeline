import typer
import json
import os
from rich.console import Console
from rich.panel import Panel
from src.pipeline import run_pipeline

app = typer.Typer()
console = Console()

@app.command()
def run(
    input: str = typer.Argument(..., help="Path to your CSV file"),
    output: str = typer.Option(None, "--output", "-o", help="Save results to JSON file")
):
    """
    Multi-Agent Data Pipeline — 5 AI agents that process your CSV autonomously.
    
    Example:
        python main.py demo/sample_data.csv
        python main.py demo/sample_data.csv --output results.json
    """
    
    if not os.path.exists(input):
        console.print(f"[red]Error: File not found — {input}[/red]")
        raise typer.Exit(1)

    if not input.endswith(".csv"):
        console.print(f"[red]Error: File must be a CSV — {input}[/red]")
        raise typer.Exit(1)

    result = run_pipeline(input)

    if output:
        with open(output, "w") as f:
            json.dump(result.model_dump(), f, indent=2)
        console.print(f"[green]→ Results saved to {output}[/green]")

if __name__ == "__main__":
    app()