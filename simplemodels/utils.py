from abc import ABC, abstractmethod
from typing import Any, Dict, List

from ase import Atoms


class BaseConformerGenerator(ABC):
    """Абстрактный базовый класс для генераторов конформеров.

    Определяет интерфейс для генерации конформеров из ASE Atoms объекта.
    """

    @abstractmethod
    def generate_and_save(self, atoms: Atoms, config: Dict[str, Any]) -> List[str]:
        """Абстрактный метод для генерации конформеров.

        :param atoms: ASE Atoms объект
        :param config: Конфигурация
        :return: Список путей к XYZ-файлам
        """
        pass


class BaseAnalyzer(ABC):
    """Абстрактный базовый класс для анализаторов конформеров.

    Определяет интерфейс для кластеризации и селекции конформеров.
    """

    @abstractmethod
    def cluster_and_select(self, conformer_files: List[str], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Абстрактный метод для анализа.

        :param conformer_files: Список путей к XYZ-файлам
        :param config: Конфигурация
        :return: Список выбранных конформеров
        """
        pass


class BaseOptimizer(ABC):
    """Абстрактный базовый класс для оптимизаторов конформеров.

    Определяет интерфейс для дооптимизации выбранных конформеров.
    """

    @abstractmethod
    def optimize_conformers(
        self, selected_conformers: List[Dict[str, Any]], config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Абстрактный метод для оптимизации конформеров.

        :param selected_conformers: Список выбранных конформеров
        :param config: Конфигурация (метод оптимизации, точность)
        :return: Оптимизированные конформеры
        """
        pass
