import os
import glob

_BASE = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
DIR_STORAGE = os.path.join(_BASE, 'Storage')


class Storage:
    DIR_STORAGE = DIR_STORAGE

    @staticmethod
    def asegurar():
        os.makedirs(DIR_STORAGE, exist_ok=True)

    @staticmethod
    def listar(extension="*.png"):
        Storage.asegurar()
        return glob.glob(os.path.join(DIR_STORAGE, extension))


def limpiar_storage():
    if not os.path.exists(DIR_STORAGE):
        return
    for ext in ("*.png", "*.html"):
        for f in glob.glob(os.path.join(DIR_STORAGE, ext)):
            try:
                os.remove(f)
            except Exception:
                pass