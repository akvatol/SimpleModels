from pathlib import Path
from typing import Any, Dict, List

import numpy as np
from ase.io import read

from .utils import BaseAnalyzer


class DScribeAnalyzer(BaseAnalyzer):
    """Анализатор конформеров на основе DScribe.

    Выполняет кластеризацию с DScribe, селекцию с qc-selector и отпечатки с scikit-fingerprints.
    """

    def cluster_and_select(self, conformer_files: List[str], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Cluster conformers by geometry and select representatives.

        Uses a lightweight RMSD-threshold clustering fallback to keep the
        full pipeline functional without mandatory external descriptor stack.
        """
        if not conformer_files:
            return []

        analyzer_cfg = config.get("analyzer", {})
        rmsd_threshold = float(analyzer_cfg.get("rmsd_threshold", 0.5))
        max_selected = int(analyzer_cfg.get("max_selected", config.get("num_conformers", 100)))

        conformers: list[dict[str, Any]] = []
        for path_str in conformer_files:
            path = Path(path_str)
            atoms = read(str(path), format="xyz")
            charge, multiplicity, energy = self._parse_xyz_header(path)

            atoms.info["charge"] = charge
            atoms.info["spin"] = multiplicity

            conformers.append(
                {
                    "atoms": atoms,
                    "file": str(path),
                    "source": path.name,
                    "charge": charge,
                    "multiplicity": multiplicity,
                    "energy": energy,
                }
            )

        clusters: list[list[int]] = []
        representatives: list[Any] = []

        for idx, conf in enumerate(conformers):
            atoms = conf["atoms"]
            assigned = False

            for c_idx, rep in enumerate(representatives):
                if self._rmsd(atoms, rep) <= rmsd_threshold:
                    clusters[c_idx].append(idx)
                    assigned = True
                    break

            if not assigned:
                representatives.append(atoms)
                clusters.append([idx])

        selected: list[dict[str, Any]] = []
        for cluster_id, member_ids in enumerate(clusters):
            members = [conformers[i] for i in member_ids]
            members.sort(key=lambda c: float("inf") if c.get("energy") is None else float(c["energy"]))
            chosen = members[0]
            chosen["cluster_id"] = cluster_id
            selected.append(chosen)

        selected.sort(key=lambda c: float("inf") if c.get("energy") is None else float(c["energy"]))
        return selected[:max_selected]

    @staticmethod
    def _rmsd(atoms_a: Any, atoms_b: Any) -> float:
        if len(atoms_a) != len(atoms_b):
            return float("inf")
        if atoms_a.get_chemical_symbols() != atoms_b.get_chemical_symbols():
            return float("inf")

        pos_a = atoms_a.get_positions() - atoms_a.get_positions().mean(axis=0)
        pos_b = atoms_b.get_positions() - atoms_b.get_positions().mean(axis=0)
        return float(np.sqrt(np.mean((pos_a - pos_b) ** 2)))

    @staticmethod
    def _parse_xyz_header(path: Path) -> tuple[int, int, float | None]:
        charge, multiplicity = 0, 1
        energy: float | None = None

        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if len(lines) < 2:
            return charge, multiplicity, energy

        tokens = lines[1].split()

        if len(tokens) >= 2:
            try:
                charge = int(tokens[0])
                multiplicity = int(tokens[1])
            except ValueError:
                pass

        for token in tokens:
            if token.startswith("energy="):
                _, value = token.split("=", 1)
                try:
                    energy = float(value)
                except ValueError:
                    pass
                break

        return charge, multiplicity, energy
