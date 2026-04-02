import ase
import click

from simplemodels.processing import process_smiles, process_xyz


# TODO 1
def validate_input(file_path: str) -> str:
    """Выбрасывает исклюбие, если файл задан неверно.

    Returns:
        str: Тип SMILES или папка с xyz

    """
    import os
    # ПРОВЕРКА НА НАЛИЧИЕ ТОГО filepath который нам нужен
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Такого пути не существует, проверьте возможно он задан неверно: {file_path}")
    
    # ПРОВЕРКА НА ТО, ЧТО ЭТО ИМЕННО ФАЙЛ ТИПА SMILES, ЧТОБЫ СЛУЧАЙНО НЕ ЦЕПАНУТЬ ЛИШНЕГО
    if os.path.isfile(file_path):
        if file_path.endswith(('.smi', '.txt', '.smiles')): # ТУТ ДОБАВЛЯЕМ ПРОВЕРКУ НА txt и smi СООТВЕТСТВЕННО, ТАК КАК ЭТИ ФОРМАТЫ В ЦЕЛОМ РОДСТВЕННЫЕ, НО ЭТО МОЖНО УБРАТЬ ПОТОМ
            return print("Данный файл относится к SMILES")
        else:
            raise ValueError(f"Файл с неподдерживаемым расширением, ожидалось расширение типа: .smi, .txt или .smiles: {file_path}")
    # ПРОВЕРКА НА СУЩЕСТВОВАНИЕ ДИРЕКТОРИИ 
    elif os.path.isdir(file_path):
        # ПРОВЕРИМ ЕСТЬ ЛИ В ДАННОЙ ДИРЕКТОРИИ xyz-файлы
        list_of_xyz_files = [f for f in os.listdir(file_path) if f.endswith('.xyz')] # ЭТОТ ГЕНЕРАТОР СПИСКА БУДЕТ ЦЕПЛЯТЬ XYZ-ФАЙЛЫ ИЗ ДИРЕКТОРИИ И ДОБАВЛЯТЬ ИХ В СПИСОК
        if list_of_xyz_files:
            return "xyz_folder"
        else:
            raise ValueError(f"Данная директория не содержит каких-либо фалов типа .xyz: {file_path}")
    
    # В СЛУЧАЕ ЕСЛИ ОТСУТСТВУЕТ И ФАЙЛ И ДИРЕКТОРИЯ
    else:
         raise ValueError(f"Не обнаружено ни подобной директории, ни файлов: {file_path}")
        


# XXX
def calculate_molecule(molecule: ase.Atoms, output: str, name: str):  # noqa: D103
    from ase.optimize import BFGS  # noqa: PLC0415
    from orb_models.forcefield import pretrained  # noqa: PLC0415
    from orb_models.forcefield.inference.calculator import ORBCalculator  # noqa: PLC0415

    device = "cpu"  # or device="cuda"
    orbff, atoms_adapter = pretrained.orb_v3_conservative_inf_omat(
        device=device,
        precision="float32-high",  # or "float32-highest" / "float64
    )

    calc = ORBCalculator(orbff, atoms_adapter=atoms_adapter, device=device)
    molecule.calc = calc

    dyn = BFGS(molecule)
    dyn.run(fmax=0.01)
    print("Optimized Energy:", molecule.get_potential_energy())
    ase.io.write(f"{name}_optimized.xyz", molecule, format="xyz")


@click.command()
@click.argument("file_path")  # txt file или папка с xyz
@click.option("--config", default=None)  # конфигурационный файл
@click.option("--output", default=None)  # папка для выходных файлов
def main(file_path: str, config: str | None = None, output: str | None = None):  # noqa: D103
    mol_type = validate_input(file_path)

    mol_type = "xyz"

    if mol_type == "SMILES":
        molecules, names = process_smiles(file_path)  # Наша задача получить список с ase.Atoms
    elif mol_type == "xyz":
        molecules, names = process_xyz(file_path)

    # TODO 2
    if output is None:
        # Получить путь для выходных данных
        pass

    for molecule, name in zip(molecules, names):
        calculate_molecule(molecule, output, name)


if __name__ == "__main__":
    main()
