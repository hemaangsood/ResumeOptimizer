from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import openai
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.progress import Progress
from rich.prompt import Prompt

from cache import SQLiteCache
from modelHandler import ModelHandler
from texHandler import TexToJsonNormalizer
from dotenv import load_dotenv

console = Console()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse a LaTeX resume, optimize it against a JD, and generate a PDF."
    )
    parser.add_argument(
        "--jd",
        help="Job description text. Use this, --jd-file, or pipe via stdin.",
    )
    parser.add_argument(
        "--jd-file",
        help="Path to a text file containing the job description.",
    )
    parser.add_argument(
        "--resume-tex",
        default=None,
        help="Path to the source LaTeX resume. Defaults to Tech/HemaangRes.tex.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for generated files. Defaults to output/.",
    )
    parser.add_argument(
        "--skip-compile",
        action="store_true",
        help="Generate the .tex file but do not run pdflatex.",
    )
    return parser.parse_args()


def load_job_description(args: argparse.Namespace) -> str:
    if sum([bool(args.jd), bool(args.jd_file), not sys.stdin.isatty()]) > 1:
        console.print("[red]Error:[/red] Provide only one of --jd, --jd-file, or stdin.")
        sys.exit(1)

    if args.jd:
        jd_text = args.jd
        if jd_text.strip() == "":
            console.print("[red]Error:[/red] --jd provided but empty.")
            sys.exit(1)
        return jd_text

    if args.jd_file:
        jd_text = Path(args.jd_file).read_text(encoding="utf-8")
        if jd_text.strip() == "":
            console.print("[red]Error:[/red] --jd-file provided but file is empty.")
            sys.exit(1)
        return jd_text

    if not sys.stdin.isatty():
        console.print("[cyan]Reading job description from stdin...[/cyan]")
        jd_text = sys.stdin.read()
        if jd_text.strip() == "":
            console.print("[red]Error:[/red] Stdin provided but empty.")
            sys.exit(1)
        return jd_text

    mode = Prompt.ask(
        "No JD provided. Enter mode",
        choices=["single", "multi"],
        default="multi",
    )
    if mode == "single":
        jd_text = Prompt.ask("Enter job description")
        if jd_text.strip() == "":
            console.print("[red]Error:[/red] Job description cannot be empty.")
            sys.exit(1)
        return jd_text

    console.print("[cyan]Paste JD text. Type END on a new line when done.[/cyan]")
    lines: list[str] = []
    while True:
        line = console.input()
        if line.strip() == "END":
            break
        lines.append(line)

    jd_text = "\n".join(lines)
    if jd_text.strip() == "":
        console.print("[red]Error:[/red] Job description cannot be empty.")
        sys.exit(1)
    return jd_text


def compile_pdf(out_dir: Path) -> None:
    try:
        subprocess.run(["initexmf", "--set-config-value", "[MPM]AutoInstall=1"], check=True)
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "doc.tex"],
            cwd=out_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        if result.stdout:
            console.print(result.stdout)
        if result.stderr:
            console.print(f"[yellow]{result.stderr}[/yellow]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]PDF compilation failed:[/red] {e}")
        sys.exit(1)
    finally:
        subprocess.run(["initexmf", "--set-config-value", "[MPM]AutoInstall=0"], check=False)


def main() -> None:
    args = parse_args()

    project_dir = Path(__file__).resolve()
    load_dotenv(project_dir / ".env")

    jd_text = load_job_description(args)
    resume_tex_path = Path(args.resume_tex) if args.resume_tex else project_dir / "Resume.tex"
    output_dir = Path(args.output_dir) if args.output_dir else project_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    with Progress(console=console) as progress:
        task_id = progress.add_task("[cyan]Processing resume...", total=5)

        console.print(f"\n[bold cyan]Resume Builder[/bold cyan]")
        console.print(f"[dim]Resume: {resume_tex_path}[/dim]")
        console.print(f"[dim]Output: {output_dir}[/dim]\n")

        progress.update(task_id, advance=0.5, description="[cyan]Initializing OpenAI client...")
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        cache = SQLiteCache()
        model_handler = ModelHandler(client=client, model="gpt-4o-mini", cache=cache)
        tex_handler = TexToJsonNormalizer()

        progress.update(task_id, advance=0.5, description="[cyan]Parsing LaTeX resume...")
        file_text = resume_tex_path.read_text(encoding="utf-8")
        prompt = tex_handler._build_prompt(file_text)
        resume_json_dict = model_handler.prompt_for_json(prompt, cache_key=file_text, use_cache=False)

        # JD is required and may contain newline characters; always optimize
        progress.update(task_id, advance=1, description="[cyan]Optimizing resume against JD...")
        resume_json_str = json.dumps(resume_json_dict)
        optimize_prompt = tex_handler._build_optimize_prompt(resume_json_str, jd_text)
        optimized_resume_dict = model_handler.prompt_for_json(optimize_prompt)

        progress.update(task_id, advance=1, description="[cyan]Generating LaTeX...")
        latex_content = tex_handler.to_latex(optimized_resume_dict)

        progress.update(task_id, advance=1, description="[cyan]Writing output files...")
        tex_path = output_dir / "doc.tex"
        tex_path.write_text(latex_content, encoding="utf-8")

        (output_dir / "resume.json").write_text(
            json.dumps(resume_json_dict, indent=2),
            encoding="utf-8",
        )
        (output_dir / "optimized_resume.json").write_text(
            json.dumps(optimized_resume_dict, indent=2),
            encoding="utf-8",
        )

        progress.update(task_id, advance=0.5, description="[green]Done!")

    console.print("\n" + "=" * 60)
    console.print(Panel("[bold cyan]Parsed Resume[/bold cyan]", expand=False))
    console.print(Syntax(json.dumps(resume_json_dict, indent=2), "json", theme="monokai", line_numbers=False))

    console.print("\n" + "=" * 60)
    console.print(Panel("[bold yellow]Optimized Resume[/bold yellow]", expand=False))
    console.print(Syntax(json.dumps(optimized_resume_dict, indent=2), "json", theme="monokai", line_numbers=False))

    console.print("\n" + "=" * 60)
    console.print(f"[green]✓ LaTeX written to:[/green] [bold]{tex_path}[/bold]")
    console.print(f"[green]✓ Resume JSON saved:[/green] [bold]{output_dir / 'resume.json'}[/bold]")
    console.print(f"[green]✓ Optimized JSON saved:[/green] [bold]{output_dir / 'optimized_resume.json'}[/bold]")

    if not args.skip_compile:
        console.print("\n[cyan]Compiling PDF...[/cyan]")
        compile_pdf(output_dir)
        console.print(f"[green]✓ PDF generated at:[/green] [bold]{output_dir / 'doc.pdf'}[/bold]")

    console.print("\n[green bold]Resume optimization complete![/green bold]\n")


if __name__ == "__main__":
    main()