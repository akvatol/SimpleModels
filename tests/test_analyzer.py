from pathlib import Path

from simplemodels.analyzer import DScribeAnalyzer


def test_analyzer_parses_charge_and_multiplicity_from_xyz_headers():
    """Analyzer must parse charge/spin from XYZ comment line."""
    analyzer = DScribeAnalyzer()
    file_path = Path("tests/test_files/test3.xyz")

    charge, multiplicity, energy = analyzer._parse_xyz_header(file_path)

    assert charge == 0
    assert multiplicity == 3
    assert energy is None


def test_analyzer_clusters_and_selects_representatives():
    """Analyzer clusters similar structures and returns selected conformer dicts."""
    analyzer = DScribeAnalyzer()
    conformer_files = [
        "tests/test_files/test1.xyz",
        "tests/test_files/test2.xyz",
        "tests/test_files/test3.xyz",
    ]
    config = {"analyzer": {"rmsd_threshold": 0.3, "max_selected": 10}, "num_conformers": 10}

    selected = analyzer.cluster_and_select(conformer_files, config)

    assert selected
    assert all("atoms" in conf for conf in selected)
    assert all("cluster_id" in conf for conf in selected)
    assert all("charge" in conf for conf in selected)
    assert all("multiplicity" in conf for conf in selected)
