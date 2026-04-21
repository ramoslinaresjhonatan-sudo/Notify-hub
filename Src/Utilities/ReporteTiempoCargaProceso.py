import os
import sys
import traceback
import base64

_current_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir    = os.path.normpath(os.path.join(_current_dir, '..', '..'))
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

from Src.Utilities.Graficas import generar_figuras_b64
from Src.Utilities.Storage  import Storage, limpiar_storage
from Src.Utilities.Picture  import picture

NUM_GRAFICOS = 5

TITULOS_GRAFICOS = [
    "Top 10 Tiempos de Recarga",
    "Distribución por Nodo",
    "Horario de Processing",
    "Top 10 (02:00 - 14:00)",
    "Top 10 (14:00 - 02:00)"
]

def _leer_flags_wa(cfg: dict) -> list:
    return [cfg.get(f"w_grafico{i}", True) for i in range(1, NUM_GRAFICOS + 1)]

def _validar_tarea(cfg: dict, index: int, logs) -> bool:
    faltantes = [c for c in ("subject", "message", "destinatarios") if not cfg.get(c)]
    if faltantes:
        logs.error(f"[Tarea {index}] Campos obligatorios faltantes: {faltantes}")
        return False
    return True

async def _generar_graficos_procesados(grafico_path: str, w_flags: list, index: int, logs):
    limpiar_storage()
    Storage.asegurar()

    try:
        figuras_b64 = generar_figuras_b64(grafico_path)
    except Exception:
        logs.error(f"[Tarea {index}] Error generando gráficos:\n{traceback.format_exc()}")
        return [], []

    pic = picture()
    rutas_todas = []
    rutas_wa    = []

    for i, figura in enumerate(figuras_b64):
        if figura is None:
            continue

        html_img = (
            f'<div style="text-align:center; padding:4px;">'
            f'<img src="data:image/png;base64,{figura["b64"]}"'
            f' style="max-width:100%; border-radius:4px; display:block; margin:auto;"/>'
            f'</div>'
        )

        ruta = await pic.Crear_Picture(
            titulo         = figura["titulo"],
            descripcion    = figura["descripcion"],
            html_contenido = html_img,
            nombre_archivo = f"tarea_{index}_{figura['nombre_archivo']}"
        )

        if ruta and os.path.exists(ruta):
            rutas_todas.append(ruta)
            if i < len(w_flags) and w_flags[i]:
                rutas_wa.append(ruta)

    logs.info(f"[Tarea {index}] {len(rutas_todas)} imagen(es) premium generada(s), "
              f"{len(rutas_wa)} para WhatsApp.")
    return rutas_todas, rutas_wa


async def enviar_whatsapp(wa_service, cfg: dict, rutas_wa: list, archivos_fallback: list, index: int, logs) -> None:
    nombre_chat = cfg.get("nombre_chat")
    if not nombre_chat: return

    archivos_enviar = rutas_wa if rutas_wa else archivos_fallback
    if not archivos_enviar: return

    mensaje_wa = cfg.get("mensaje_wa") or None
    chats = [nombre_chat] if isinstance(nombre_chat, str) else nombre_chat

    for chat in chats:
        try:
            ok = await wa_service.enviar(chat=chat, archivos=archivos_enviar, mensaje=mensaje_wa)
            if ok: logs.info(f"[Tarea {index}] WhatsApp enviado a '{chat}'.")
            else: logs.error(f"[Tarea {index}] Fallo WhatsApp a '{chat}'.")
        except Exception:
            logs.error(f"[Tarea {index}] Excepción WhatsApp a '{chat}':\n{traceback.format_exc()}")

def enviar_correo(correo_service, cfg: dict, adjuntos: list, index: int, logs) -> None:
    destinatarios = cfg.get("destinatarios", [])
    if not destinatarios: return
    
    to_str = ";".join(destinatarios)
    adjuntos_validos = [a for a in adjuntos if a and os.path.exists(a)]

    try:
        ok = correo_service.send_mail(
            to=to_str,
            subject=cfg.get("subject"),
            message=cfg.get("message"),
            attachments=adjuntos_validos if adjuntos_validos else None,
        )
        if ok: logs.info(f"[Tarea {index}] Correo enviado a {len(destinatarios)} persona(s).")
    except OSError as e:
        if 'getaddrinfo' in str(e) or '11001' in str(e):
            logs.error(f"[Tarea {index}] Error de red: no se pudo conectar al servidor de correo. "
                       f"¿Estás conectado a la VPN/red corporativa?")
        else:
            logs.error(f"[Tarea {index}] Error de conexión correo: {e}")
    except Exception:
        logs.error(f"[Tarea {index}] Excepción correo:\n{traceback.format_exc()}")

async def procesar_tarea_carga(correo_service, wa_service, cfg: dict, index: int, logs) -> None:
    logs.info(f"[Tarea {index}] Procesando: {cfg.get('subject')}")

    if not _validar_tarea(cfg, index, logs): return

    ruta_archivo = cfg.get("ruta_archivo", "")
    grafico_path = cfg.get("grafico", "")

    archivos_principales = []
    if ruta_archivo:
        if os.path.exists(ruta_archivo):
            archivos_principales.append(ruta_archivo)
        else:
            logs.warning(f"[Tarea {index}] CSV no encontrado, se omite adjunto: {ruta_archivo}")

    rutas_premium_todas = []
    rutas_premium_wa = []

    if grafico_path:
        if os.path.exists(grafico_path):
            w_flags = _leer_flags_wa(cfg)
            rutas_premium_todas, rutas_premium_wa = await _generar_graficos_procesados(grafico_path, w_flags, index, logs)
            await picture.close()
        else:
            logs.warning(f"[Tarea {index}] CSV de gráficos no encontrado, sin imágenes: {grafico_path}")

    logs.info(f"[Tarea {index}] Iniciando fase de envío por WhatsApp...")
    await enviar_whatsapp(wa_service, cfg, rutas_premium_wa, archivos_principales, index, logs)
    
    todos_adjuntos = archivos_principales + rutas_premium_todas
    enviar_correo(correo_service, cfg, todos_adjuntos, index, logs)

    limpiar_storage()
    logs.info(f"[Tarea {index}] Finalizada.")
