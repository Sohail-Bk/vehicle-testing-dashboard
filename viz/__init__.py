from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from data.generate_sample_data import generate_all_data


DATA_PATH = ROOT_DIR / 'data' / 'sample_vehicle_data.csv'


# This file intentionally exists to keep the package importable when the app is run from the viz/ folder.
