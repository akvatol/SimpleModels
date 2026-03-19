import ase


def process_smile(smile: str) -> ase.Atoms:  # noqa: D103
    # Принимает строку вида SMILE charge mult и возвращает объект ase.Atoms
    # Должна сгенирирроватиь 3D координаты при помощи RDKit
    pass


def process_smiles(file_path: str) -> list:  # noqa: D103
    data = []
    with open(file_path, "r") as f:  # noqa: PLW1514
        smiles = f.readlines()
    for smile in smiles:
        smile_line = smile.strip()
        process_smile(smile_line)
        data.append(smile_line)
    return data
