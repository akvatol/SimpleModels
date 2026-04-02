from pathlib import Path

from ase import Atoms
from ase.io import write

from simplemodels.main import ConformerPipeline


def _write_xyz_with_header(path: Path, atoms: Atoms, charge: int, multiplicity: int, energy: float) -> None:
    """Write XYZ file and replace comment line with charge/spin/energy metadata."""
    write(str(path), atoms, format="xyz")
    lines = path.read_text(encoding="utf-8").splitlines()
    lines[1] = f"{charge} {multiplicity} energy={energy}"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_pipeline_end_to_end_with_mocked_generator_and_optimizer(tmp_path: Path):
    """Pipeline should run all stages and preserve charge/multiplicity into optimization."""
    input_xyz = tmp_path / "input.xyz"
    input_xyz.write_text(
        """3
0 3
O 0.000000 0.000000 0.000000
H 0.758000 0.000000 0.504000
H -0.758000 0.000000 0.504000
""",
        encoding="utf-8",
    )

    config = {
        "input_format": "xyz",
        "generator_type": "minimahopping",
        "analyzer_type": "dscribe",
        "optimizer_type": "dft",
        "enable_optimization": True,
        "num_conformers": 5,
        "output_dir": str(tmp_path / "output"),
        "report_path": "report.html",
        "analyzer": {"rmsd_threshold": 0.4, "max_selected": 5},
        "optimizer": {"calculator": "orb", "algorithm": "BFGS"},
    }

    pipeline = ConformerPipeline(config)
    state = {"optimizer_called": False}

    def fake_generate_and_save(atoms: Atoms, cfg: dict) -> list[str]:
        """Create synthetic conformer XYZ files with headers for analyzer stage."""
        assert atoms.info.get("charge") == 0
        assert atoms.info.get("spin") == 3

        conformer_dir = Path(cfg["output_dir"]) / "conformers"
        conformer_dir.mkdir(parents=True, exist_ok=True)

        c1 = Atoms("OH2", positions=[(0.0, 0.0, 0.0), (0.758, 0.0, 0.504), (-0.758, 0.0, 0.504)])
        c2 = Atoms("OH2", positions=[(0.0, 0.0, 0.0), (0.760, 0.0, 0.506), (-0.760, 0.0, 0.506)])

        p1 = conformer_dir / "conformer_0000.xyz"
        p2 = conformer_dir / "conformer_0001.xyz"
        _write_xyz_with_header(p1, c1, charge=0, multiplicity=3, energy=-76.1)
        _write_xyz_with_header(p2, c2, charge=0, multiplicity=3, energy=-76.0)

        return [str(p1), str(p2)]

    def fake_optimize_conformers(selected_conformers: list[dict], cfg: dict) -> list[dict]:
        """Validate metadata flow into optimizer and return updated energies."""
        state["optimizer_called"] = True
        for conf in selected_conformers:
            assert conf.get("charge") == 0
            assert conf.get("multiplicity") == 3
            assert conf["atoms"].info.get("charge") == 0
            assert conf["atoms"].info.get("spin") == 3
            conf["energy"] = float(conf.get("energy") or 0.0) - 0.01
        return selected_conformers

    pipeline.generator.generate_and_save = fake_generate_and_save
    pipeline.optimizer.optimize_conformers = fake_optimize_conformers

    report_path = pipeline.run(str(input_xyz))
    report_file = Path(report_path)

    assert state["optimizer_called"] is True
    assert report_file.exists()
    assert report_file.suffix == ".html"
    html = report_file.read_text(encoding="utf-8")
    assert "Conformer Report" in html
    assert "Post-Optimization" in html
