"""Core pipeline orchestrator for conformer generation."""

from typing import Any

import click

from .analyzer import DScribeAnalyzer
from .config import load_config
from .conformer_generator import ASEConformerGenerator, OpenBabelConformerGenerator
from .input_handler import InputHandler
from .optimizer import DFTConformerOptimizer
from .reporter import Reporter
from .utils import BaseAnalyzer, BaseConformerGenerator, BaseOptimizer


class ConformerPipeline:
    def __init__(self, config: dict[str, Any]):
        """Инициализация пайплайна с конфигурацией и инъекцией зависимостей.

        :param config: Словарь с параметрами (включая 'generator_type', 'analyzer_type', 'enable_optimization')
        """
        self.config = config
        self.input_handler = InputHandler()

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
        
        # Фабрика для легкозаменимых модулей
        self.generator: BaseConformerGenerator = self._create_generator(config.get("generator_type", "ase"))
        self.analyzer: BaseAnalyzer = self._create_analyzer(config.get("analyzer_type", "dscribe"))
        self.optimizer: BaseOptimizer = self._create_optimizer(config.get("optimizer_type", "dft"))
        self.reporter = Reporter()

    def _create_generator(self, gen_type: str) -> BaseConformerGenerator:
        if gen_type == "ase":
            return ASEConformerGenerator()
        elif gen_type == "openbabel":
            return OpenBabelConformerGenerator()
        else:
            raise ValueError(f"Неизвестный тип генератора: {gen_type}")

    def _create_analyzer(self, ana_type: str) -> BaseAnalyzer:
        if ana_type == "dscribe":
            return DScribeAnalyzer()
        else:
            raise ValueError(f"Неизвестный тип анализатора: {ana_type}")

    def _create_optimizer(self, opt_type: str) -> BaseOptimizer:
        if opt_type == "dft":
            return DFTConformerOptimizer()
        else:
            raise ValueError(f"Неизвестный тип оптимизатора: {opt_type}")

    def run(self, input_data: str) -> str:
        """Запуск полного пайплайна.

        :param input_data: Входная химическая структура
        :return: Путь к HTML-отчету
        """
        # Этап 1: Ввод и конвертация
        atoms = self.input_handler.parse_and_convert(input_data, self.config)

        # Этап 2: Генерация конформеров
        conformer_files = self.generator.generate_and_save(atoms, self.config)

        # Этап 3: Анализ
        selected_conformers = self.analyzer.cluster_and_select(conformer_files, self.config)

        # Этап 4: Дооптимизация (опционально)
        if self.config.get("enable_optimization", False):
            selected_conformers = self.optimizer.optimize_conformers(selected_conformers, self.config)

        # Этап 5: Отчет
        report_path = self.reporter.generate_html_report(selected_conformers, self.config)

        return report_path


@click.command()
@click.argument("input_data")  # SMILES строка или путь к файлу/папке
@click.option("--config", default=None, help="Путь к конфигурационному файлу")
@click.option("--output", default=None, help="Папка для выходных файлов")
def main(input_data: str, config: str | None = None, output: str | None = None):
    """Главная функция для запуска пайплайна генерации конформеров.

    :param input_data: Входные данные (SMILES или путь)
    :param config: Путь к конфигу
    :param output: Папка для вывода
    """
    cfg = load_config(config)
    if output:
        cfg["output_dir"] = output

    pipeline = ConformerPipeline(cfg)
    report_path = pipeline.run(input_data)
    print(f"Отчет сгенерирован: {report_path}")


if __name__ == "__main__":
    main()
