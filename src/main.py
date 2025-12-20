import sys

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon

from . import config
from .database import db
from .services.backup_service import perform_backup
from .ui.main_window import MainWindow


def main():
    try:
        config.ensure_directories()
        db.init_db()
        if config.DB_PATH.exists():
            perform_backup()
    except Exception as exc:
        QMessageBox.critical(None, "Error inicializando", str(exc))
        raise

    app = QApplication(sys.argv)
    if config.LOGO_PATH.exists():
        app.setWindowIcon(QIcon(str(config.LOGO_PATH)))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


