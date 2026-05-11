"""
WhatsApp Integration — Cliente HTTP para la API de WhatsApp.
"""

import os
import logging
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

class WhatsApp:

    def __init__(self, base_url: str = None, api_key: str = None):
        self._base_url = (
            base_url
            or os.getenv("WHATSAPP_API_URL", "http://localhost:8000")
        ).rstrip("/")

        self._api_key = (
            api_key
            or os.getenv("WHATSAPP_API_KEY", "MamayatechJRL2026")
        )

        self._session: aiohttp.ClientSession | None = None
        self._timeout = aiohttp.ClientTimeout(total=320)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=self._timeout,
                headers={
                    "X-API-Key": self._api_key,
                    "Content-Type": "application/json",
                },
            )
        return self._session

    async def conectar(self) -> bool:
        """Verifica que la API esté accesible."""
        try:
            session = await self._get_session()
            async with session.get(
                f"{self._base_url}/docs", timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                reachable = resp.status < 500
                if reachable:
                    logger.info("Conexión con la API de WhatsApp verificada.")
                else:
                    logger.error(f"API respondió con status {resp.status}")
                return reachable
        except Exception as e:
            logger.error(f"No se pudo conectar a la API de WhatsApp ({self._base_url}): {e}")
            return False

    async def enviar(self, chat: str, mensaje: str = None, archivos: list = None) -> bool:
        """Envía un mensaje de texto, archivos o ambos."""
        archivos_abs = None
        if archivos:
            archivos_abs = [os.path.abspath(r) for r in archivos if os.path.exists(r)]
            if not archivos_abs:
                logger.warning("Ninguno de los archivos proporcionados existe.")
                archivos_abs = None

        payload = {
            "chat": chat,
            "message": mensaje or "",
            "files": archivos_abs,
        }

        return await self._post("/send-message", payload, chat)

    async def mensaje(self, chat: str, texto: str) -> bool:
        return await self.enviar(chat, mensaje=texto)

    async def archivo(self, chat: str, ruta: str, texto: str = "") -> bool:
        return await self.enviar(chat, mensaje=texto or None, archivos=[ruta])

    async def varios(self, chat: str, rutas: list, texto: str = "") -> bool:
        return await self.enviar(chat, mensaje=texto or None, archivos=rutas)

    async def enviar_captura(self, chat: str, html: str, caption: str = None) -> bool:
        """Envía contenido HTML como imagen capturada."""
        payload = {
            "chat": chat,
            "message": html,
        }
        return await self._post("/send-message", payload, chat)

    async def _post(self, endpoint: str, payload: dict, chat: str) -> bool:
        url = f"{self._base_url}{endpoint}"
        try:
            session = await self._get_session()
            logger.info(f"Enviando petición a {endpoint} para chat '{chat}'...")

            async with session.post(url, json=payload) as resp:
                body = await resp.json()
                if resp.status == 200 and body.get("status") == "success":
                    logger.info(
                        f"   [✓] Mensaje enviado a '{chat}'. "
                        f"Cola restante: {body.get('cola_restante', '?')}"
                    )
                    return True

                logger.error(f"   [✗] Error API ({resp.status}): {body.get('detail', body)}")
                return False

        except asyncio.TimeoutError:
            logger.error(f"   [✗] Timeout al enviar a '{chat}' vía {endpoint}.")
            return False
        except aiohttp.ClientError as e:
            logger.error(f"   [✗] Error de conexión con la API: {e}")
            return False
        except Exception as e:
            logger.error(f"   [✗] Error inesperado enviando a '{chat}': {e}")
            return False

    async def cerrar(self):
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("Sesión HTTP con la API de WhatsApp cerrada.")
        self._session = None

    async def cerrar_sesion(self):
        await self.cerrar()

    async def close(self):
        await self.cerrar()

WhatsAppSender = WhatsApp
