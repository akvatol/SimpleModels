import copy
from typing import Any, Dict, List  # Добавил Any, чтобы не текло

from ase.optimize import BFGS, LBFGS, FIRE
from .utils import BaseOptimizer

# Наш ящик с ключами: если просят "LBFGS", выдаем соответствующий инструмент
OPT_DICT = {
    "BFGS": BFGS,
    "LBFGS": LBFGS,
    "FIRE": FIRE
}

# Пытаемся прикрутить ORB (Вот этот кусок трубы ты потерял!)
try:
    from orb_models.forcefield.calculator import ORBCalculator
except ImportError:
    ORBCalculator = None

# Нормально наследуемся от BaseOptimizer
class DFTConformerOptimizer(BaseOptimizer):
    
    # Никаких @staticmethod! Нормальный вентиль с self и новым параметром
    def optimize_conformers(
        self, selected_conformers: List[Dict[str, Any]], config: Dict[str, Any], optimizer: str = "BFGS"
    ) -> List[Dict[str, Any]]:
        
        # читает config
        opt_config = config.get("optimizer", {})
        calc_type = opt_config.get("calculator", "orb")
        orb_model_name = opt_config.get("orb_model", "orb-v3")

        optimized_conformers = []

        for conf in selected_conformers:
            # Берем копию файла, чтобы не сломать оригинал
            new_conf = copy.deepcopy(conf)
            atoms = new_conf.get("atoms")
            
            if atoms is None:
                continue # Если файла нет, пропускаем (засор)

            # Ставим калькулятор
            if calc_type == "orb":
                if ORBCalculator is None:
                    raise ImportError("Библиотека orb_models не установлена! Ставь давай, иначе работать не будет.")
                # Навешиваем калькулятор
                calc = ORBCalculator(model_name=orb_model_name)
                atoms.calc = calc
            else:
                raise ValueError(f"Не тот тип {calc_type}! Валера работает только с 'orb'.")

            # Берем указанный оптимизатор из ящика
            alg_opt = OPT_DICT.get(optimizer, BFGS)
            logfile = None  # чтобы не затопило консоль лишней водой
            opt = alg_opt(atoms, logfile=logfile)

            # Пускаем давление
            fmax = opt_config.get("fmax", 0.01)
            max_steps = opt_config.cdget("max_steps", 500)
            opt.run(fmax=fmax, steps=max_steps)

            # Парсит новую геометрию и энергию
            new_conf["atoms"] = atoms
            new_conf["energy"] = atoms.get_potential_energy()
            
            optimized_conformers.append(new_conf)

        # Сортируем от лучшей к худшей
        optimized_conformers.sort(key=lambda x: x.get("energy", float('inf')))
        
        return optimized_conformers