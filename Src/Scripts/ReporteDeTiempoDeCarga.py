import os
import sys
import json
import traceback
import asyncio

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir    = os.path.normpath(os.path.join(current_dir, "..", ".."))

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    from Src.Integrations.WhatsApp import WhatsApp
    from Src.Integrations.Correo   import Correo
    from Src.Utilities.ReporteTiempoCargaProceso import procesar_tarea_carga
    from Src.Utilities.Logger      import setup_logger
    from Src.Utilities.Picture     import picture
except ImportError as e:
    print(f"[FATAL] Error de importación: {e}")
    sys.exit(1)

logger = setup_logger("ReporteTiempoCarga", "ReporteTiempoCarga.log")
CONFIG_FILE = os.path.join(root_dir, "Config", "ReporteDeTiempoDeCarga.json")

def load_config(config_path: str) -> list:
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else [data]
    except FileNotFoundError:
        logger.error(f"Archivo de configuración no encontrado: {config_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"JSON inválido en {config_path}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error inesperado cargando config: {e}\n{traceback.format_exc()}")
        return []

async def main() -> None:
    if not os.path.exists(CONFIG_FILE):
        logger.error(f"No se encontró el archivo de configuración: {CONFIG_FILE}")
        return

    tasks = load_config(CONFIG_FILE)
    if not tasks:
        logger.error("No hay tareas que procesar.")
        return

    logger.info(f"Iniciando ReporteDeTiempoDeCarga — {len(tasks)} tarea(s) encontradas.")

    correo_cfg_path = os.path.join(root_dir, "Config", "Correo.json")
    correo_cfg = {}
    if os.path.exists(correo_cfg_path):
        with open(correo_cfg_path, "r", encoding="utf-8") as f:
            correo_cfg = json.load(f)
            
    correo = Correo(
        server=correo_cfg.get("server"),
        port=correo_cfg.get("port"),
        email_address=correo_cfg.get("email_address"),
        display_name=correo_cfg.get("display_name"),
        error_recipients=correo_cfg.get("error_recipients")
    )
    wa = WhatsApp()

    try:
        for index, cfg in enumerate(tasks):
            try:
                await procesar_tarea_carga(correo, wa, cfg, index, logger)
            except Exception:
                logger.error(f"[Tarea {index}] Error no controlado:\n{traceback.format_exc()}")
    finally:
        await wa.cerrar()
        await picture.close()
        logger.info("ReporteDeTiempoDeCarga finalizado.")

if __name__ == "__main__":
    asyncio.run(main())
