"""Conformer generators using Minima Hopping (ASE) and Confab (OpenBabel)."""

import logging
import os
import tempfile
from pathlib import Path
from typing import Any

from ase import Atoms
from ase.io import read, write

from .utils import BaseConformerGenerator

logger = logging.getLogger(__name__)


class ASEConformerGenerator(BaseConformerGenerator):
    """Conformer generator based on the Minima Hopping method.

    Uses the minimahopping package with ASE calculators to explore
    the potential energy surface and find distinct conformers.
    """

    def generate_and_save(self, atoms: Atoms, config: dict[str, Any]) -> list[str]:
        """Generate conformers using Minima Hopping and save as XYZ files.

        Args:
            atoms: ASE Atoms object with a calculator already attached.
            config: Configuration dict. Relevant keys under "conformers":
                - T0: Initial MD temperature (default 1000).
                - mdmin: MD steps before quench (default 2).
                - fmax: Force convergence for geometry optimization (default 0.05).
                - totalsteps: Number of hopping steps (default from num_conformers).
                - output_n_lowest_minima: How many lowest minima to output (default 20).
                - dt0: Initial MD timestep (default 0.08).
                - energy_threshold: Energy threshold for distinguishing minima (default 0.001).
                - fingerprint_threshold: OMFP distance threshold (default 0.05).

        Returns:
            List of paths to generated XYZ conformer files.
        """
        from minimahopping.minhop import Minimahopping  # noqa: PLC0415

        conformer_config = config.get("conformers", {})
        output_dir = Path(config.get("output_dir", "output"))
        output_dir.mkdir(parents=True, exist_ok=True)

        mh_params = {
            "T0": conformer_config.get("T0", conformer_config.get("T", 1000)),
            "mdmin": conformer_config.get("mdmin", 2),
            "fmax": conformer_config.get("fmax", 0.05),
            "output_n_lowest_minima": conformer_config.get("output_n_lowest_minima", config.get("num_conformers", 100)),
            "dt0": conformer_config.get("dt0", 0.08),
            "energy_threshold": conformer_config.get("energy_threshold", 0.001),
            "fingerprint_threshold": conformer_config.get("fingerprint_threshold", 0.05),
            "fixed_cell_simulation": True,
            "use_MPI": False,
            "collect_md_data": False,
            "write_graph_output": False,
        }

        totalsteps = conformer_config.get("totalsteps", config.get("num_conformers", 100))

        # Minimahopping writes to output/ and minima/ in cwd, so run from a temp dir
        original_cwd = os.getcwd()
        work_dir = tempfile.mkdtemp(prefix="mh_conformers_")

        try:
            os.chdir(work_dir)
            logger.info("Running Minima Hopping in %s with %d steps", work_dir, totalsteps)

            with Minimahopping(atoms, **mh_params) as mh:
                mh(totalsteps=totalsteps)

            # Read unique conformers from the minima hopping output
            results_file = Path(work_dir) / "minima" / "all_minima_no_duplicates.extxyz"
            if not results_file.exists():
                logger.warning("No conformers file found at %s", results_file)
                return []

            conformers = read(str(results_file), index=":")
            logger.info("Found %d unique conformers", len(conformers))

            # Save each conformer as individual XYZ file
            conformer_dir = output_dir / "conformers"
            conformer_dir.mkdir(parents=True, exist_ok=True)

            saved_paths = []
            for i, conformer in enumerate(conformers):
                xyz_path = conformer_dir / f"conformer_{i:04d}.xyz"
                write(str(xyz_path), conformer, format="xyz")
                saved_paths.append(str(xyz_path))

            return saved_paths

        finally:
            os.chdir(original_cwd)


class OpenBabelConformerGenerator(BaseConformerGenerator):
    """Conformer generator based on OpenBabel's Confab method.

    Uses OpenBabel's systematic rotor search to enumerate
    low-energy conformers by rotating around rotatable bonds.
    """

    def generate_and_save(self, atoms: Atoms, config: dict[str, Any]) -> list[str]:
        """Generate conformers using OpenBabel Confab and save as XYZ files.

        Args:
            atoms: ASE Atoms object representing the molecule.
            config: Configuration dict. Relevant keys under "conformers":
                - rmsd_cutoff: RMSD cutoff for confab diversity filter (default 0.5 A).
                - energy_cutoff: Energy cutoff above lowest in kcal/mol (default 50.0).
                - conf_cutoff: Max number of conformers to generate (default from num_conformers).
                - forcefield: Force field for confab (default "mmff94").

        Returns:
            List of paths to generated XYZ conformer files.
        """
        from openbabel import openbabel, pybel  # noqa: PLC0415

        conformer_config = config.get("conformers", {})
        output_dir = Path(config.get("output_dir", "output"))
        conformer_dir = output_dir / "conformers"
        conformer_dir.mkdir(parents=True, exist_ok=True)

        rmsd_cutoff = conformer_config.get("rmsd_cutoff", 0.5)
        energy_cutoff = conformer_config.get("energy_cutoff", 50.0)
        conf_cutoff = conformer_config.get("conf_cutoff", config.get("num_conformers", 100))
        forcefield = conformer_config.get("forcefield", "mmff94")

        # Convert ASE Atoms to OpenBabel molecule via temporary XYZ file
        with tempfile.NamedTemporaryFile(suffix=".xyz", mode="w", delete=False) as tmp:
            tmp_path = tmp.name
            write(tmp_path, atoms, format="xyz")

        try:
            mol = next(pybel.readfile("xyz", tmp_path))
        finally:
            os.unlink(tmp_path)

        # Set up force field and run Confab conformer generation
        ff = openbabel.OBForceField.FindForceField(forcefield)
        if not ff:
            raise RuntimeError(f"Force field '{forcefield}' not available in OpenBabel")

        if not ff.Setup(mol.OBMol):
            raise RuntimeError("Failed to set up force field for molecule")

        ff.DiverseConfGen(rmsd_cutoff, conf_cutoff, energy_cutoff, False)
        ff.GetConformers(mol.OBMol)

        num_conformers = mol.OBMol.NumConformers()
        logger.info("Confab generated %d conformers", num_conformers)

        saved_paths = []
        for i in range(num_conformers):
            mol.OBMol.SetConformer(i)
            xyz_path = conformer_dir / f"conformer_{i:04d}.xyz"
            # Write conformer using pybel
            out_mol = pybel.Molecule(mol.OBMol)
            out_mol.write("xyz", str(xyz_path), overwrite=True)
            saved_paths.append(str(xyz_path))

        return saved_paths
