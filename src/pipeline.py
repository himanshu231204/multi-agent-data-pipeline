import os
import json
import pandas as pd
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel
from src.models import PipelineResult
from src.agents import cleaner, validator, transformer, anomaly, summariser, pii_anonymiser

console = Console()

def load_csv(file_path: str) -> tuple[pd.DataFrame, str, int]:
    df = pd.read_csv(file_path)
    total_rows = len(df)
    preview = df.head(20).to_csv(index=False)
    return df, preview, total_rows

def run_pipeline(file_path: str) -> PipelineResult:
    file_name = os.path.basename(file_path)
    
    console.print(Panel.fit(
        f"[bold green]MULTI-AGENT DATA PIPELINE[/bold green]\n[dim]Processing: {file_name}[/dim]",
        border_style="green"
    ))

    df, preview, total_rows = load_csv(file_path)
    console.print(f"\n[cyan]→ Loaded {total_rows} rows from {file_name}[/cyan]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:

        task1 = progress.add_task("[green]Agent 1/6 — Cleaner...", total=None)
        cleaner_result = cleaner.run(preview, total_rows)
        progress.update(task1, description="[green]Agent 1/6 — Cleaner ✓")
        progress.stop_task(task1)

        task2 = progress.add_task("[cyan]Agent 2/6 — PII Anonymiser...", total=None)
        pii_result = pii_anonymiser.run(preview, total_rows)
        
        safe_preview = pii_result.anonymised_preview  
        
        progress.update(task2, description="[cyan]Agent 2/6 — PII Anonymiser ✓")
        progress.stop_task(task2)

        task3 = progress.add_task("[blue]Agent 3/6 — Validator...", total=None)
        validator_result = validator.run(preview, total_rows)
        progress.update(task3, description="[blue]Agent 3/6 — Validator ✓")
        progress.stop_task(task3)

        task4 = progress.add_task("[yellow]Agent 4/6 — Transformer...", total=None)
        transformer_result = transformer.run(preview, total_rows)
        progress.update(task4, description="[yellow]Agent 4/6 — Transformer ✓")
        progress.stop_task(task4)

        task5 = progress.add_task("[red]Agent 5/6 — Anomaly Detector...", total=None)
        anomaly_result = anomaly.run(preview, total_rows)
        progress.update(task5, description="[red]Agent 5/6 — Anomaly Detector ✓")
        progress.stop_task(task5)

        context = f"""
        Cleaner found {len(cleaner_result.issues_fixed)} issues affecting {cleaner_result.rows_affected} rows.
        Validator score: {validator_result.completeness_score}% completeness, {len(validator_result.violations)} violations.
        Transformer applied {len(transformer_result.transformations_applied)} transformations.
        Anomaly detector found {anomaly_result.anomaly_count} anomalies with risk score {anomaly_result.anomaly_score}/10.
        """

        task6 = progress.add_task("[magenta]Agent 6/6 — Summariser...", total=None)
        summariser_result = summariser.run(preview, total_rows, context)
        progress.update(task6, description="[magenta]Agent 6/6 — Summariser ✓")
        progress.stop_task(task6)

    result = PipelineResult(
        file_name=file_name,
        total_rows=total_rows,
        cleaner=cleaner_result,
        pii=pii_result,
        validator=validator_result,
        transformer=transformer_result,
        anomaly=anomaly_result,
        summariser=summariser_result,
        status="complete"
    )

    _print_summary(result)
    return result

def _print_summary(result: PipelineResult):
    console.print("\n")
    table = Table(title="Pipeline Results", border_style="green")
    table.add_column("Agent", style="cyan")
    table.add_column("Result", style="white")

    table.add_row(
        "Cleaner",
        f"{result.cleaner.rows_affected} rows fixed, {len(result.cleaner.issues_fixed)} issues"
    )

    table.add_row(
        "PII Anonymiser",
        f"{result.pii.rows_affected} rows masked, types: {', '.join(result.pii.pii_types_detected) or 'none detected'}"
    )

    table.add_row(
        "Validator",
        f"{result.validator.completeness_score}% complete, {len(result.validator.violations)} violations"
    )
    table.add_row(
        "Transformer",
        f"{result.transformer.rows_transformed} rows transformed, {len(result.transformer.new_columns)} new columns"
    )
    table.add_row(
        "Anomaly",
        f"{result.anomaly.anomaly_count} anomalies, risk score {result.anomaly.anomaly_score}/10"
    )
    table.add_row(
        "Summariser",
        f"{len(result.summariser.recommendations)} recommendations"
    )

    console.print(table)
    console.print(f"\n[bold green]✓ Pipeline complete — {result.total_rows} rows processed[/bold green]\n")