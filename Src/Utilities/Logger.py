import os
import logging
from logging.handlers import TimedRotatingFileHandler
import re
from datetime import datetime

class DailyRotatingFileHandler(TimedRotatingFileHandler):
    def rotation_filename(self, default_name):
        base_dir, base_name = os.path.split(default_name)
        if ".log." in base_name:
            partes = base_name.split(".log.")
            if len(partes) == 2:
                nombre_base, date_part = partes
                try:
                    dt = datetime.strptime(date_part, "%Y-%m-%d")
                    fecha_formateada = dt.strftime("%d-%m-%Y")
                    nuevo_nombre = f"{fecha_formateada}-{nombre_base}.log"
                    return os.path.join(base_dir, nuevo_nombre)
                except ValueError:
                    return default_name
        return default_name

    def getFilesToDelete(self):
        dirName, baseName = os.path.split(self.baseFilename)
        fileNames = os.listdir(dirName)
        result = []
        nombre_sin_ext = baseName.replace('.log', '')
        pattern_new = re.compile(r"^\d{2}-\d{2}-\d{4}-" + re.escape(nombre_sin_ext) + r"\.log$")
        pattern_old1 = re.compile(re.escape(nombre_sin_ext) + r"-\d{4}-\d{2}-\d{2}\.log$")
        pattern_old2 = re.compile(re.escape(nombre_sin_ext) + r"_\d{2}-\d{2}-\d{4}\.log$")
        for fileName in fileNames:
            if pattern_new.match(fileName) or pattern_old1.match(fileName) or pattern_old2.match(fileName):
                result.append(os.path.join(dirName, fileName))
        result.sort(key=lambda x: os.path.getmtime(x))
        if len(result) < self.backupCount:
            result = []
        else:
            result = result[:len(result) - self.backupCount]
        return result

def setup_logger(name: str, log_file: str, level=logging.INFO):
    if not os.path.isabs(log_file):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        log_file = os.path.join(base_dir, "Logs", log_file)
    log_dir = os.path.dirname(log_file)
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if logger.hasHandlers():
        logger.handlers.clear()
    file_handler = DailyRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)-8s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False
    return logger
