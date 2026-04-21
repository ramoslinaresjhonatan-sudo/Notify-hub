import os
import logging
from datetime import datetime


def Logs(nombre: str, log_dir: str = ''):
    if not log_dir:
        log_dir = os.path.normpath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'Logs')
        )

    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(nombre)

    # Evitar añadir handlers duplicados si ya fue configurado
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # Evitar duplicados en el root logger

    fecha = datetime.now().strftime('%Y-%m-%d')
    log_file = os.path.join(log_dir, f'{nombre}-{fecha}.log')

    # Handler de archivo
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.DEBUG)

    # Handler de consola
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    fmt = logging.Formatter('[%(asctime)s] %(levelname)s - %(name)s - %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
    fh.setFormatter(fmt)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger