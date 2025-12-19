# Barbería Offline (PySide6 + SQLite)

Aplicación de escritorio 100% offline para gestión de agenda, cobros y reportes de una barbería. Minimalista, en español y preparada para empaquetar a `.exe` con PyInstaller.

## Requisitos
- Python 3.12
- Windows (probado en Windows 10)

## Instalación en desarrollo
```bash
python -m venv .venv
.\\.venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
```

La base de datos se crea en `src/barberia.db` la primera vez que se ejecuta e incluye semillas de barberos y servicios.

## Estructura
- `app.py`: punto de entrada.
- `src/`:
  - `config.py`: constantes, rutas y semillas.
  - `database.py`: conexión SQLite y migraciones.
  - `repositories.py`: acceso a datos.
  - `services/`: lógica de agenda, cobros, reportes y backups.
  - `ui/`: ventanas y tabs (Agenda, Cobros, Reportes, Configuración).
  - `main.py`: arranque de la app Qt.
- `requirements.txt`: dependencias (PySide6, reportlab).

## Funcionalidades clave
- Agenda diaria/semanal con bloqueo por horario (09:30-20:00) y intervalo de 15 minutos.
- Validación de descanso por barbero y prevención de choques de horario.
- Cobros con desglose de servicios, cálculo automático de ganancia de barbero y liquidación a barbería.
- Reportes por rango (hoy/semana/mes/personalizado) y exportación a PDF offline.
- Configuración de barberos, servicios, descansos y backups automáticos en `src/backups` (retiene últimos 30).

## Empaquetado a .exe (PyInstaller)
Desde la raíz del proyecto:
```bash
.\\.venv\\Scripts\\activate
pyinstaller --noconfirm --onefile --windowed app.py
```
El ejecutable quedará en `dist/app.exe`. Copia junto a él el archivo `src/barberia.db` si quieres reutilizar datos; si no existe, la app generará uno nuevo con datos de ejemplo.

## Backups
- Carpeta por defecto: `src/backups`.
- Cada inicio crea `barberia_YYYYMMDD_HHMMSS.db` y se conservan los últimos 30.

## Notas
- Toda la interfaz está en español y las cifras se muestran en COP con separador de miles (`$20.000`).
- La app funciona sin conexión a Internet ni dependencias externas a las incluidas.

