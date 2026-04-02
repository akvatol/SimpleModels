from pathlib import Path

from ase import Atoms

from simplemodels.reporter import Reporter


def test_generate_html_report_creates_nested_output_path(tmp_path: Path):
    """Reporter creates report file in nested subdirectory under output dir."""
    reporter = Reporter()
    conformers = [
        {
            "atoms": Atoms("H2", positions=[(0.0, 0.0, 0.0), (0.74, 0.0, 0.0)]),
            "energy": -1.0,
            "source": "input.xyz",
        }
    ]
    config = {
        "output_dir": str(tmp_path),
        "report_path": "reports/report.html",
        "generator_type": "minimahopping",
        "enable_optimization": False,
    }

    report_path = reporter.generate_html_report(conformers, config)
    report_file = Path(report_path)

    assert report_file.exists()
    assert report_file.name == "report.html"
    assert report_file.parent.name == "reports"


def test_generate_html_report_handles_empty_conformers(tmp_path: Path):
    """Reporter renders valid HTML even when conformer list is empty."""
    reporter = Reporter()
    config = {
        "output_dir": str(tmp_path),
        "report_path": "report.html",
        "generator_type": "openbabel",
        "enable_optimization": True,
    }

    report_path = reporter.generate_html_report([], config)
    html = Path(report_path).read_text(encoding="utf-8")

    assert "Conformer Report" in html
    assert "selected" in html
    assert "N/A" in html


def test_generate_html_report_escapes_source_html(tmp_path: Path):
    """Reporter escapes HTML-sensitive source values in table output."""
    reporter = Reporter()
    conformers = [
        {
            "atoms": Atoms("He", positions=[(0.0, 0.0, 0.0)]),
            "energy": 0.0,
            "source": "<script>alert('x')</script>",
        }
    ]
    config = {
        "output_dir": str(tmp_path),
        "report_path": "report.html",
        "generator_type": "openbabel",
        "enable_optimization": False,
    }

    report_path = reporter.generate_html_report(conformers, config)
    html = Path(report_path).read_text(encoding="utf-8")

    assert "<script>alert('x')</script>" not in html
    assert "&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;" in html


def test_generate_html_report_contains_offline_fallback_logic(tmp_path: Path):
    """Reporter embeds fallback messages for unavailable CDN JS libraries."""
    reporter = Reporter()
    conformers = [{"atoms": Atoms("He", positions=[(0.0, 0.0, 0.0)]), "energy": 0.0}]
    config = {
        "output_dir": str(tmp_path),
        "report_path": "report.html",
        "generator_type": "openbabel",
        "enable_optimization": False,
    }

    report_path = reporter.generate_html_report(conformers, config)
    html = Path(report_path).read_text(encoding="utf-8")

    assert "typeof $3Dmol === 'undefined'" in html
    assert "typeof Chart === 'undefined'" in html
    assert "3D viewer unavailable" in html
    assert "Energy chart unavailable" in html
