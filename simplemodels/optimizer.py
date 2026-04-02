import copy
from typing import Any

from ase.optimize import BFGS, FIRE, LBFGS

from .utils import BaseOptimizer

OPT_DICT = {
    "BFGS": BFGS,
    "LBFGS": LBFGS,
    "FIRE": FIRE,
}

try:
    from orb_models.forcefield.calculator import ORBCalculator
except ImportError:
    ORBCalculator = None


class DFTConformerOptimizer(BaseOptimizer):
    """Geometry optimizer for selected conformers."""

    def optimize_conformers(
        self,
        selected_conformers: list[dict[str, Any]],
        config: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Optimize conformers while preserving charge/multiplicity metadata."""
        opt_config = config.get("optimizer", {})
        calc_type = opt_config.get("calculator", "orb")
        orb_model_name = opt_config.get("orb_model", "orb-v3")
        optimizer_name = str(opt_config.get("algorithm", "BFGS")).upper()

        optimized_conformers: list[dict[str, Any]] = []

        for conf in selected_conformers:
            new_conf = copy.deepcopy(conf)
            atoms = new_conf.get("atoms")
            if atoms is None:
                continue

            charge = self._resolve_charge(new_conf, config)
            multiplicity = self._resolve_multiplicity(new_conf, config)
            atoms.info["charge"] = charge
            atoms.info["spin"] = multiplicity
            new_conf["charge"] = charge
            new_conf["multiplicity"] = multiplicity

            if calc_type == "orb":
                if ORBCalculator is None:
                    raise ImportError("orb_models is not installed. Install it to run optimization.")
                atoms.calc = self._build_orb_calculator(orb_model_name, charge, multiplicity)
            else:
                raise ValueError(f"Unsupported calculator type: {calc_type}")

            optimizer_cls = OPT_DICT.get(optimizer_name, BFGS)
            optimizer = optimizer_cls(atoms, logfile=None)

            fmax = float(opt_config.get("fmax", 0.01))
            max_steps = int(opt_config.get("max_steps", 500))
            optimizer.run(fmax=fmax, steps=max_steps)

            new_conf["atoms"] = atoms
            new_conf["energy"] = float(atoms.get_potential_energy())
            optimized_conformers.append(new_conf)

        optimized_conformers.sort(key=lambda x: float(x.get("energy", float("inf"))))
        return optimized_conformers

    @staticmethod
    def _build_orb_calculator(model_name: str, charge: int, multiplicity: int):
        """Try passing charge/multiplicity when calculator implementation supports it."""
        try:
            return ORBCalculator(model_name=model_name, charge=charge, multiplicity=multiplicity)
        except TypeError:
            return ORBCalculator(model_name=model_name)

    @staticmethod
    def _resolve_charge(conf: dict[str, Any], config: dict[str, Any]) -> int:
        atoms = conf.get("atoms")
        info_charge = atoms.info.get("charge") if atoms is not None else None
        charge = conf.get("charge", info_charge)
        if charge is None:
            charge = config.get("charge", config.get("optimizer", {}).get("charge", 0))
        return int(charge)

    @staticmethod
    def _resolve_multiplicity(conf: dict[str, Any], config: dict[str, Any]) -> int:
        atoms = conf.get("atoms")
        info_spin = atoms.info.get("spin") if atoms is not None else None
        multiplicity = conf.get("multiplicity", info_spin)
        if multiplicity is None:
            multiplicity = config.get("multiplicity", config.get("optimizer", {}).get("multiplicity", 1))
        return int(multiplicity)
