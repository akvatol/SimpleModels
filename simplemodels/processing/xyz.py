from pathlib import Path

from ase.io import read


def process_xyz(file_path: str) -> list:
    """*.xyz parsing."""
    path = Path(file_path)
    if path.is_file():
        files = [path] if path.suffix.lower() == ".xyz" else []
    elif path.is_dir():
        files = sorted(path.glob("*.xyz"))
    else:
        files = []

    data = []
    names = []
    for molecule_file in files:
        atoms = read(molecule_file, format="xyz")
        with open(molecule_file, "r", encoding="utf-8") as fr:
            xyz = fr.readlines()

        charge, mult = 0, 1
        try:
            if len(xyz) > 1:
                header_parts = xyz[1].split()
                if len(header_parts) >= 2:
                    charge = int(header_parts[0])
                    mult = int(header_parts[1])
        except (TypeError, ValueError):
            charge, mult = 0, 1

        atoms.info["charge"] = charge  # total charge
        atoms.info["spin"] = mult  # spin multiplicity
        data.append(atoms)
        names.append(molecule_file.stem)

    if not data:
        raise FileNotFoundError(f"No XYZ files found at: {file_path}")

    return data, names


if __name__ == "__main__":
    data = process_xyz(r"tests\test_files")
    for i in data:
        print(i)
