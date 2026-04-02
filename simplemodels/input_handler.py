from typing import Any, Dict

from ase import Atoms

from simplemodels.processing.smiles import process_smile
from simplemodels.processing.xyz import process_xyz


class InputHandler:
    """Класс для обработки входных данных.

    Конвертирует химические структуры (SMILES или XYZ) в ASE Atoms объекты.
    """

    def parse_and_convert(self, input_data: str, config: Dict[str, Any]) -> Atoms:
        """Парсит входные данные и конвертирует в ASE Atoms.

        :param input_data: Химическая структура (SMILES или путь к XYZ)
        :param config: Конфигурация (формат ввода, параметры)
        :return: ASE Atoms объект
        """
        input_format = config.get("input_format", "smiles")
        if input_format == "smiles":
            # Заглушка: Использовать process_smile для конвертации SMILES в Atoms
            atoms = process_smile(input_data)
        elif input_format == "xyz":
            # Заглушка: Использовать process_xyz для чтения XYZ
            data, names = process_xyz(input_data)
            atoms = data[0] if data else None  # Предполагаем один файл
        else:
            raise ValueError(f"Неизвестный формат ввода: {input_format}")
        if atoms is None:
            raise ValueError("Не удалось конвертировать входные данные")
        return atoms
