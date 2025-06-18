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
    run_command(["dnsrecon", "-d", domain])
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


def run_gowitness(subdomains_file: Path, output_dir: Path) -> Path:
    """Capture screenshots of live hosts using ``gowitness``."""

    screenshots = output_dir / "gowitness" / "shots"
    screenshots.mkdir(parents=True, exist_ok=True)
    run_command(["gowitness", "file", "-f", str(subdomains_file), "--destination", str(screenshots)])
    return screenshots


def run_nmap(live_hosts_file: Path, output_dir: Path) -> Path:
    """Perform a light ``nmap`` scan of live hosts."""

    out_file = output_dir / "nmap.txt"
    run_command(["nmap", "-iL", str(live_hosts_file), "-oN", str(out_file)])
    return out_file


def generate_report(domain: str, output_dir: Path, tool_outputs: Dict[str, Path]) -> Path:
    """Create HTML and PDF reports summarizing results from *tool_outputs*."""

    template = Template(
        """
        <html>
        <head><meta charset="utf-8"><title>SubTrace Report</title></head>
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

    html_path = output_dir / f"{domain}_reporte.html"
    pdf_path = output_dir / f"{domain}_reporte.pdf"

    html_content = template.render(domain=domain, outputs=tool_outputs)
    html_path.write_text(html_content, encoding="utf-8")

    try:
        pdfkit.from_file(str(html_path), str(pdf_path))
    except Exception:
        # PDF generation is optional and may fail if wkhtmltopdf is missing
        pdf_path.write_text("PDF generation failed", encoding="utf-8")

    return html_path


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
    parser.add_argument("domain", help="Target domain to enumerate")

    args = parser.parse_args()
    run_all(args.domain)

