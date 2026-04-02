import os
import pytest
from pathlib import Path

# Фикстура-генератор: штампуем xyz-файлы
@pytest.fixture
def create_xyz_file():
    # Создаем папку, если ее нет
    test_dir = Path("tests/test_files")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Название берется из названия файла
    file_path = test_dir / "molecule_test.xyz"
    
    # Содержимое: 8 атомов, заряд 0, мультиплетность 1
    xyz_data = """8
0 1
C         -5.85312        1.22812        0.00000
C         -4.34107        1.22812        0.00000
H         -6.23750        2.00398        0.66883
H         -6.23750        0.26098        0.33750
H         -6.23750        1.41942       -1.00632
H         -3.95670        1.03683        1.00632
H         -3.95670        2.19527       -0.33750
H         -3.95670        0.45227       -0.66883"""

    # Заливаем данные в файл
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(xyz_data)
        
    # Отдаем путь к файлу в тест
    yield str(file_path)
    
    # Убираем за собой мусор после работы (раскомментируй, если надо удалять)
    # os.remove(file_path)