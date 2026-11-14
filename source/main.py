import sys
from pathlib import Path

# Добавляем корень проекта в sys.path для корректных импортов при прямом запуске
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from source.application import Application


def main():
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
