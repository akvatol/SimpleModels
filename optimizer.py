import copy
from typing import Dict, List

from ase.optimize import BFGS

# Пытаемся прикрутить ORB, как просили в плане
try:
    from orb_models.forcefield.calculator import ORBCalculator
except ImportError:
    ORBCalculator = None


class DFTConformerOptimizer:
    @staticmethod
    def optimize_conformers(selected_conformers: List[Dict], config: Dict) -> List[Dict]:
        """Optimize selected conformers using ORB calculator and BFGS."""
        # читает config
        opt_config = config.get("optimizer", {})
        calc_type = opt_config.get("calculator", "orb")
        fmax = opt_config.get("fmax", 0.01)
        max_steps = opt_config.get("max_steps", 500)
        orb_model_name = opt_config.get("orb_model", "orb-v3")

        optimized_conformers = []

        for conf in selected_conformers:
            # Берем копию файла, чтобы не сломать оригинал, если что-то пойдет не так
            new_conf = copy.deepcopy(conf)
            atoms = new_conf.get("atoms")

            if atoms is None:
                continue  # Если файла нет, пропускаем

            # Ставим счетчик давления (калькулятор)
            if calc_type == "orb":
                if ORBCalculator is None:
                    raise ImportError("Библиотека orb_models не установлена! Ставь давай, иначе работать не будет.")
                # Навешиваем калькулятор
                calc = ORBCalculator(model_name=orb_model_name)
                atoms.calc = calc
            else:
                # Если подсунули какую-то дичь вместо нормального инструмента
                raise ValueError(f"Какой нахуй {calc_type}? Валера работает только с 'orb'.")

            # Берем BFGS и начинаем оптимизировать геометрию
            # logfile=None
            opt = BFGS(atoms, logfile=None)
            opt.run(fmax=fmax, steps=max_steps)

            # Парсит новую геометрию и энергию, сохраняет в новый конфиг
            new_conf["atoms"] = atoms
            new_conf["energy"] = atoms.get_potential_energy()

            optimized_conformers.append(new_conf)

        # Сортируем от лучшей к худшей (по энергии)
        optimized_conformers.sort(key=lambda x: x.get("energy", float("inf")))

        return optimized_conformers
