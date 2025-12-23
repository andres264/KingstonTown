import shutil
from datetime import datetime
from pathlib import Path

from .. import config


def perform_backup(db_path: Path = config.DB_PATH, backup_dir: Path = config.BACKUP_DIR, keep: int = 30) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = backup_dir / f"barberia_{ts}.db"
    shutil.copy(db_path, target)
    _trim_backups(backup_dir, keep)
    return target


def _trim_backups(backup_dir: Path, keep: int) -> None:
    files = sorted(backup_dir.glob("barberia_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in files[keep:]:
        try:
            old.unlink()
        except Exception:
            pass






