"""SubTrace OSINT DNS tool orchestrator.

This module provides a minimal command line interface that wraps several
commonly used OSINT utilities. The goal is to automate passive DNS and
subdomain reconnaissance and export the results as HTML and PDF reports.

The implementation intentionally keeps the logic lightweight so it can run in
restricted environments. Each external tool is invoked through
``subprocess.run`` and the resulting output is stored in ``<domain>-recon/``.

Tools invoked:

``amass``       -> enumerates subdomains
``dnsrecon``    -> gathers DNS information
``subfinder``   -> additional subdomain discovery
``httpx``       -> verifies which hosts are alive
``gowitness``   -> captures screenshots of reachable hosts
``nmap``        -> performs a basic port scan

The final report is generated in HTML using ``jinja2`` and converted to PDF
with ``pdfkit``. Each step can be executed independently via the helper
functions or together with :func:`run_all`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict, List

try:
    import customtkinter as ctk  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    ctk = None  # type: ignore

try:
    from tkinter import messagebox  # standard library, may be missing on some envs
except Exception:  # pragma: no cover - optional dependency
    messagebox = None  # type: ignore

try:
    from jinja2 import Template
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    Template = None  # type: ignore

try:
    import pdfkit
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    pdfkit = None  # type: ignore


def run_command(command: List[str]) -> str:
    """Execute ``command`` returning ``stdout`` and ``stderr`` combined.

    Parameters
    ----------
    command:
        Sequence of command line arguments.

    Returns
    -------
    str
        Text output produced by the command.
    """

    result = subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return result.stdout


def run_amass(domain: str, output_dir: Path) -> Path:
    """Run ``amass enum`` saving results under *output_dir*."""

    out_file = output_dir / "amass.txt"
    run_command(["amass", "enum", "-d", domain, "-o", str(out_file)])
    return out_file


def run_dnsrecon(domain: str, output_dir: Path) -> Path:
    """Run ``dnsrecon`` on *domain* and store output."""

    out_file = output_dir / "dnsrecon.txt"
    output = run_command(["dnsrecon", "-d", domain])
    out_file.write_text(output, encoding="utf-8")
    return out_file


def run_subfinder(domain: str, output_dir: Path) -> Path:
    """Run ``subfinder`` to discover subdomains."""

    out_file = output_dir / "subfinder.txt"
    run_command(["subfinder", "-d", domain, "-o", str(out_file)])
    return out_file


def combine_subdomains(output_dir: Path) -> Path:
    """Combine discovered subdomains into ``subdominios.txt``."""

    amass = output_dir / "amass.txt"
    subfinder = output_dir / "subfinder.txt"
    out_file = output_dir / "subdominios.txt"

    seen = set()
    with out_file.open("w", encoding="utf-8") as dst:
        for path in (amass, subfinder):
            if not path.exists():
                continue
            for line in path.read_text().splitlines():
                if line not in seen:
                    seen.add(line)
                    dst.write(f"{line}\n")
    return out_file


def run_httpx(subdomains_file: Path, output_dir: Path) -> Path:
    """Run ``httpx`` against a list of subdomains to detect live hosts."""

    out_file = output_dir / "vivos.txt"
    run_command(["httpx", "-l", str(subdomains_file), "-o", str(out_file)])
    return out_file


def run_gowitness(live_hosts_file: Path, output_dir: Path) -> Path:
    """Capture screenshots of live hosts using ``gowitness``.

    Returns a log file describing where the screenshots were stored so the
    report can embed a textual summary instead of attempting to read a
    directory.
    """

    screenshots = output_dir / "gowitness" / "shots"
    screenshots.mkdir(parents=True, exist_ok=True)
    output = run_command(
        [
            "gowitness",
            "file",
            "-f",
            str(live_hosts_file),
            "--destination",
            str(screenshots),
        ]
    )

    log_file = output_dir / "gowitness.txt"
    log_file.write_text(
        (
            "Resultados de gowitness\n\n"
            f"Capturas almacenadas en: {screenshots}\n\n"
            f"Salida de la herramienta:\n{output}"
        ),
        encoding="utf-8",
    )
    return log_file


def run_nmap(live_hosts_file: Path, output_dir: Path) -> Path:
    """Perform a light ``nmap`` scan of live hosts."""

    out_file = output_dir / "nmap.txt"
    run_command(["nmap", "-iL", str(live_hosts_file), "-oN", str(out_file)])
    return out_file


def generate_report(domain: str, output_dir: Path, tool_outputs: Dict[str, Path]) -> Path:
    """Create HTML and PDF reports summarizing results from *tool_outputs*."""

    if Template is not None:
        template = Template(
            """
            <html>
            <head><meta charset=\"utf-8\"><title>SubTrace Report</title></head>
            <body>
            <h1>Reconocimiento para {{ domain }}</h1>
            {% for name, path in outputs.items() %}
            <h2>{{ name }}</h2>
            <pre>{{ path.read_text() }}</pre>
            {% endfor %}
            </body>
            </html>
            """
        )
        html_content = template.render(domain=domain, outputs=tool_outputs)
    else:
        html_content = (
            "<html><head><meta charset=\"utf-8\"><title>SubTrace Report"
            "</title></head><body>"
            f"<h1>Reconocimiento para {domain}</h1>"
            + "".join(f"<h2>{name}</h2><pre>{path.read_text()}</pre>" for name, path in tool_outputs.items())
            + "</body></html>"
        )

    html_path = output_dir / f"{domain}_reporte.html"
    pdf_path = output_dir / f"{domain}_reporte.pdf"

    html_path.write_text(html_content, encoding="utf-8")

    try:
        pdfkit.from_file(str(html_path), str(pdf_path))
    except Exception:
        # PDF generation is optional and may fail if wkhtmltopdf is missing
        pdf_path.write_text("PDF generation failed", encoding="utf-8")

    return html_path


def run_gui() -> None:
    """Launch a very small GUI for running :func:`run_all`.

    The GUI is optional and only available when ``customtkinter`` is installed.
    """

    if ctk is None:
        raise RuntimeError("customtkinter is not installed")

    app = ctk.CTk()
    app.title("SubTrace")
    app.geometry("400x150")

    domain_var = ctk.StringVar()

    def start() -> None:
        domain = domain_var.get().strip()
        if not domain:
            if messagebox:
                messagebox.showwarning("SubTrace", "Debe introducir un dominio")
            return
        run_all(domain)
        if messagebox:
            messagebox.showinfo(
                "SubTrace", f"Resultados guardados en {domain}-recon/"
            )

    entry = ctk.CTkEntry(app, textvariable=domain_var, width=300)
    entry.pack(pady=20)
    button = ctk.CTkButton(app, text="Ejecutar", command=start)
    button.pack(pady=10)

    app.mainloop()


def run_all(domain: str) -> None:
    """Run the full OSINT workflow for ``domain``."""

    output_dir = Path(f"{domain}-recon")
    output_dir.mkdir(exist_ok=True)

    results: Dict[str, Path] = {}
    results["amass"] = run_amass(domain, output_dir)
    results["dnsrecon"] = run_dnsrecon(domain, output_dir)
    results["subfinder"] = run_subfinder(domain, output_dir)
    combined = combine_subdomains(output_dir)
    results["subdominios"] = combined
    results["vivos"] = run_httpx(combined, output_dir)
    results["gowitness"] = run_gowitness(results["vivos"], output_dir)
    results["nmap"] = run_nmap(results["vivos"], output_dir)

    generate_report(domain, output_dir, results)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run SubTrace OSINT workflow")
    parser.add_argument("domain", nargs="?", help="Target domain to enumerate")
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch graphical interface (default if no domain provided)",
    )

    args = parser.parse_args()

    if args.gui or (args.domain is None and ctk is not None):
        run_gui()
    elif args.domain is not None:
        run_all(args.domain)
    else:
        parser.print_help()

