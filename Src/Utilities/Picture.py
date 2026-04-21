from datetime import date
import os
from playwright.async_api import async_playwright

_BASE = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
STORAGE_DIR = os.path.join(_BASE, 'Storage')


class picture:
    _p = None
    _browser = None

    def __init__(self):
        os.makedirs(STORAGE_DIR, exist_ok=True)

    async def _get_browser(self):
        if not picture._p:
            picture._p = await async_playwright().start()
        if not picture._browser:
            picture._browser = await picture._p.chromium.launch()
        return picture._browser

    async def _capturar_screenshot(self, html: str, output_path: str = "output.png"):
        browser = await self._get_browser()
        context = await browser.new_context(
            viewport={"width": 820, "height": 800},
            device_scale_factor=2
        )
        page = await context.new_page()
        try:
            await page.set_content(html)
            await page.wait_for_load_state("networkidle")
            # Capturar el cuerpo para evitar espacios vacíos innecesarios
            await page.locator("body").screenshot(path=output_path)
        finally:
            await context.close()

    @classmethod
    async def close(cls):
        if cls._browser:
            await cls._browser.close()
            cls._browser = None
        if cls._p:
            await cls._p.stop()
            cls._p = None

    def _insertar_Contenido(self, titulo, descripcion, html_contenido) -> str:
        plantilla = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>mamaya tech</title>
    <link href="https://fonts.googleapis.com/css2?family=Comfortaa:wght@700&family=Inter:wght@400;600;700;900&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', sans-serif;
            background-color: #f0f0f0;
            display: inline-block;
            padding: 30px;
        }}
        .container {{
            width: 720px;
            border-radius: 14px;
            overflow: hidden;
            box-shadow: 0 8px 32px rgba(0,0,0,0.18);
            background-color: #ffffff;
        }}
        .title-section {{
            background-color: #ffffff;
            padding: 24px 32px 8px 32px;
            border-bottom: 3px solid #F47920;
        }}
        .title-section h1 {{ font-size: 22px; font-weight: 700; color: #1a1a1a; }}
        .title-section p {{ font-size: 13px; color: #777; margin-top: 4px; margin-bottom: 16px; }}
        .content {{ padding: 24px 32px 32px 32px; }}
        .footer {{
            background-color: #1a1a1a;
            padding: 14px 32px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .footer-brand {{ font-family: 'Comfortaa', cursive; font-size: 14px; font-weight: 700; color: #ffffff; }}
        .footer-brand span {{ color: #F47920; }}
        .footer-date {{ font-size: 11px; color: #eeeeee; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
        thead tr {{ background-color: #F47920; }}
        thead th {{ padding: 12px 16px; text-align: left; font-weight: 700; color: #ffffff; text-transform: uppercase; font-size: 12px; }}
        tbody td {{ padding: 12px 16px; border-bottom: 1px solid #f0f0f0; color: #333; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="title-section">
            <h1>{titulo}</h1>
            <p>{descripcion}</p>
        </div>
        <div class="content">
            {contenido}
        </div>
        <div class="footer">
            <span class="footer-brand">mamaya<span> tech</span></span>
            <span class="footer-date">{fecha}</span>
        </div>
    </div>
</body>
</html>"""
        return plantilla.format(
            titulo=titulo,
            descripcion=descripcion,
            contenido=html_contenido,
            fecha=date.today().strftime("%Y-%m-%d")
        )

    async def Crear_Picture(self, titulo, descripcion, html_contenido, nombre_archivo=None):
        os.makedirs(STORAGE_DIR, exist_ok=True)
        nombre = nombre_archivo if nombre_archivo else (titulo + ".png")
        if not nombre.endswith(".png"):
            nombre += ".png"
        html_final = self._insertar_Contenido(titulo, descripcion, html_contenido)
        ruta_final = os.path.join(STORAGE_DIR, nombre)
        await self._capturar_screenshot(html_final, ruta_final)
        return ruta_final