from ase import Atoms

import simplemodels.optimizer as optimizer_module
from simplemodels.optimizer import DFTConformerOptimizer


class DummyCalculator:
    """Minimal calculator used to verify constructor kwargs and energy access."""

    def __init__(self, **kwargs):
        """Store constructor kwargs for assertions."""
        self.kwargs = kwargs

    def get_potential_energy(self, atoms=None, force_consistent=False):
        """Return deterministic energy for tests."""
        return -1.23


class DummyOptimizer:
    """No-op optimizer for fast unit tests."""

    def __init__(self, atoms, logfile=None):
        """Capture atoms object passed by optimizer under test."""
        self.atoms = atoms

    def run(self, fmax=0.01, steps=500):
        """No-op run method matching ASE optimizer interface."""
        return None


def test_optimizer_passes_charge_and_multiplicity_to_calculator(monkeypatch):
    """Optimizer should forward charge/multiplicity when calculator supports kwargs."""
    created_kwargs = []

    class TrackingCalculator(DummyCalculator):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            created_kwargs.append(kwargs)

    monkeypatch.setattr(optimizer_module, "ORBCalculator", TrackingCalculator)
    monkeypatch.setitem(optimizer_module.OPT_DICT, "BFGS", DummyOptimizer)

    atoms = Atoms("He", positions=[(0.0, 0.0, 0.0)])
    atoms.info["charge"] = 0
    atoms.info["spin"] = 3

    optimizer = DFTConformerOptimizer()
    selected = [{"atoms": atoms, "source": "x.xyz"}]
    config = {
        "optimizer": {
            "calculator": "orb",
            "orb_model": "orb-v3",
            "algorithm": "BFGS",
            "fmax": 0.02,
            "max_steps": 5,
        }
    }

    out = optimizer.optimize_conformers(selected, config)

    assert out
    assert out[0]["charge"] == 0
    assert out[0]["multiplicity"] == 3
    assert created_kwargs
    assert created_kwargs[0]["charge"] == 0
    assert created_kwargs[0]["multiplicity"] == 3


def test_optimizer_uses_config_charge_and_multiplicity_fallback(monkeypatch):
    """Optimizer should use config values when conformer metadata is absent."""
    monkeypatch.setattr(optimizer_module, "ORBCalculator", DummyCalculator)
    monkeypatch.setitem(optimizer_module.OPT_DICT, "BFGS", DummyOptimizer)

    atoms = Atoms("He", positions=[(0.0, 0.0, 0.0)])
    optimizer = DFTConformerOptimizer()
    selected = [{"atoms": atoms, "source": "x.xyz"}]
    config = {
        "charge": -1,
        "multiplicity": 2,
        "optimizer": {
            "calculator": "orb",
            "orb_model": "orb-v3",
            "algorithm": "BFGS",
        },
    }

    out = optimizer.optimize_conformers(selected, config)

    assert out[0]["charge"] == -1
    assert out[0]["multiplicity"] == 2
