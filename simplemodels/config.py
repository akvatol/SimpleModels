"""Configuration management for the conformer generation pipeline."""

from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG: dict[str, Any] = {
    "input_format": "smiles",  # 'smiles' or 'xyz'
    "generator_type": "ase",  # 'ase' or 'openbabel'
    "analyzer_type": "dscribe",  # 'dscribe'
    "optimizer_type": "dft",  # 'dft'
    "enable_optimization": False,
    "num_conformers": 100,
    "output_dir": "output",
    "report_path": "report.html",
    "conformers": {},
}


def load_config(config_path: str = None) -> dict[str, Any]:
    """Load configuration from a YAML file or return defaults.

    Args:
        config_path: Path to a YAML configuration file.

    Returns:
        Configuration dictionary with defaults applied for missing keys.
    """
    config = DEFAULT_CONFIG.copy()

    if config_path:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(path) as f:
            user_config = yaml.safe_load(f) or {}

        config.update(user_config)

    return config
