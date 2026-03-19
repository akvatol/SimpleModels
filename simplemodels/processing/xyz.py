from pathlib import Path

from ase.io import read


def process_xyz(file_path: str) -> list:
    """*.xyz parsing."""
    path = Path(file_path)
    files = path.glob("*.xyz")
    data = []
    names = []
    for molecule_file in files:
        atoms = read(molecule_file, format="xyz")
        with open(molecule_file, "r", encoding="utf-8") as fr:
            xyz = fr.readlines()
        try:
            charge, mult = int(xyz[1].split()[0]), int(xyz[1].split()[1])
        # TODO: add proper error handling
        except:  # noqa: E722
            charge, mult = 0, 1
        finally:
            atoms.info["charge"] = charge  # total charge
            atoms.info["spin"] = mult  # spin multiplicity
        data.append(atoms)
        names.append(molecule_file.stem)
    return data, names


if __name__ == "__main__":
    data = process_xyz(r"tests\test_files")
    for i in data:
        print(i)
