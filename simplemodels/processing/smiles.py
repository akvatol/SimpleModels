from pathlib import Path
from tempfile import NamedTemporaryFile

import ase
from ase.io import read


def _parse_smiles_line(smile_line: str) -> tuple[str, int | None, int | None]:
    """Parse 'SMILES [charge] [multiplicity]' formatted line."""
    parts = smile_line.strip().split()
    if not parts:
        raise ValueError("SMILES строка не может быть пустой")

    smiles = parts[0]
    charge = int(parts[1]) if len(parts) > 1 else None
    multiplicity = int(parts[2]) if len(parts) > 2 else None
    return smiles, charge, multiplicity


def process_smile(smile: str) -> ase.Atoms:  # noqa: D103
    from openbabel import pybel  # noqa: PLC0415

    smiles, charge, multiplicity = _parse_smiles_line(smile)

    mol = pybel.readstring("smi", smiles)
    if charge is not None:
        mol.OBMol.SetTotalCharge(charge)
    if multiplicity is not None:
        mol.OBMol.SetTotalSpinMultiplicity(multiplicity)

    mol.addh()
    mol.make3D()

    with NamedTemporaryFile(suffix=".xyz", mode="w", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        mol.write("xyz", tmp_path, overwrite=True)
        atoms = read(tmp_path, format="xyz")
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return atoms


def smiles_to_xyz(file_path: str, output_dir: str = ".") -> list[str]:
    """Convert SMILES file to numbered XYZ files in output directory."""
    from openbabel import pybel  # noqa: PLC0415

    source = Path(file_path)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    created_files: list[str] = []
    with source.open("r", encoding="utf-8") as f:
        smiles_lines = f.readlines()

    count = 0
    for smile_line in smiles_lines:
        stripped = smile_line.strip()
        if not stripped:
            continue

        count += 1
        smiles, _, _ = _parse_smiles_line(stripped)
        mol = pybel.readstring("smi", smiles)
        mol.addh()
        mol.make3D()

        xyz_path = destination / f"{count}.xyz"
        mol.write("xyz", str(xyz_path), overwrite=True)
        created_files.append(str(xyz_path))

    return created_files


def process_smiles(file_path: str) -> list[str]:  # noqa: D103
    data: list[str] = []
    with open(file_path, "r", encoding="utf-8") as f:  # noqa: PTH123
        smiles = f.readlines()
    for smile in smiles:
        smile_line = smile.strip()
        if not smile_line:
            continue
        process_smile(smile_line)
        data.append(smile_line)
    return data
