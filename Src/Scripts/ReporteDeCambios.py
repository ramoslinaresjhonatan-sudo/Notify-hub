import os
import sys
import json
from datetime import datetime
import asyncio

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

CONFIG_FILE = os.path.join(ROOT_DIR, "Config", "DeteccionDeModificaciones.json")

def load_initial_config():
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"No se encontró el archivo de configuración en {CONFIG_FILE}")
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

config_global = load_initial_config()

BASE_PATH = config_global.get("BASE_PATH") or ROOT_DIR
AUDIT_PATH = config_global.get("AUDIT_PATH")
SCHED_PATH = config_global.get("SCHED_PATH")

_wl_path = config_global.get("WHITELIST_PATH", "Config/Const/lista_blanca.csv")
WHITELIST_PATH = os.path.join(BASE_PATH, _wl_path) if not os.path.isabs(_wl_path) else _wl_path

STATE_FILE_REL = config_global.get("STATE_FILE_RELATIVE")
if STATE_FILE_REL:
    STATE_FILE = os.path.join(BASE_PATH, STATE_FILE_REL)
else:
    STATE_FILE = CONFIG_FILE

from Src.Utilities.DetectorQlick import QlikMonitor
from Src.Integrations.WhatsApp import WhatsApp
from Src.Utilities.Picture import picture

try:
    from Src.Integrations.Correo import CorreoSender
except ImportError:
    CorreoSender = None

def formatear_fecha(ts_raw):
    if not ts_raw: return "N/A"
    try:
        patterns = ["%Y%m%dT%H%M%S.%f%z", "%Y%m%dT%H%M%S%z", "%Y%m%dT%H%M%S.%f", "%Y%m%dT%H%M%S"]
        for p in patterns:
            try:
                dt = datetime.strptime(ts_raw.strip(), p)
                return dt.strftime("%d/%m/%Y %H:%M:%S")
            except ValueError: continue
        return ts_raw
    except: return ts_raw

def generar_html_publicaciones(eventos):
    html = "<table><thead><tr><th>Acción</th><th>Aplicativo</th><th>Usuario</th><th>Fecha/Hora</th></tr></thead><tbody>"
    for ev in eventos:
        ts = formatear_fecha(ev.get('timestamp'))
        html += f"<tr><td>{ev.get('command') or 'Desconocida'}</td><td>{ev.get('object') or 'Desconocida'}</td><td>{ev.get('who', 'Desconocido')}</td><td>{ts}</td></tr>"
    return html + "</tbody></table>"

def generar_html_tareas(eventos):
    html = "<table><thead><tr><th>Tipo</th><th>Tarea</th><th>Estado</th><th>Fecha/Hora</th></tr></thead><tbody>"
    for ev in eventos:
        ts = formatear_fecha(ev.get('timestamp'))
        estado = "Inicio de Recarga" if (ev.get('command') or "").lower() == "task execution" else ev.get('command', 'Inicio')
        html += f"<tr><td>Inicio</td><td>{ev.get('object') or 'Desconocida'}</td><td>{estado}</td><td>{ts}</td></tr>"
    return html + "</tbody></table>"

async def main():
    print("--- Iniciando Monitor de Qlik ---")
    
    if not all([AUDIT_PATH, SCHED_PATH, STATE_FILE]):
        print("Error: Faltan rutas críticas en el archivo de configuración JSON.")
        return

    monitor = QlikMonitor(AUDIT_PATH, SCHED_PATH, STATE_FILE, whitelist_csv=WHITELIST_PATH)
    whatsapp_enabled = config_global.get("WhatsApp", False)
    correo_enabled = config_global.get("Correo", False)
    datos_notificacion = config_global.get("Datos", [])

    print(f"Escaneando logs...")
    nuevos_eventos = monitor.process()

    if not nuevos_eventos:
        print("No se detectaron novedades.")
        return

    print(f"Detectados {len(nuevos_eventos)} eventos nuevos.")
    pic = picture()
    ws = WhatsApp() if whatsapp_enabled else None

    if ws:
        if not await ws.conectar():
            print("No se pudo conectar a la ventana de WhatsApp abierta. Abortando envío WhatsApp.")
            ws = None

    try:
        for destino in datos_notificacion:
            stream_filtro = (destino.get("filtro_stream") or "").strip().upper()
            eventos_filtrados = [e for e in nuevos_eventos if (e.get("stream") or "").upper() == stream_filtro]
            
            if not eventos_filtrados: continue

            eventos_pub = [e for e in eventos_filtrados if e["type"] == "PUBLISH"]
            eventos_task = [e for e in eventos_filtrados if e["type"] == "RELOAD_START"]

            archivos_notificar = []
            
            if eventos_pub:
                html = generar_html_publicaciones(eventos_pub)
                ruta = await pic.Crear_Picture(f"Publicaciones ({stream_filtro})", "Cambios detectados en aplicativos", html, f"pub_{stream_filtro}.png")
                archivos_notificar.append((ruta, f"*Publicaciones de Aplicativos:* {stream_filtro}", html, f"Publicaciones ({stream_filtro})"))

            if eventos_task:
                html = generar_html_tareas(eventos_task)
                ruta = await pic.Crear_Picture(f"Recargas ({stream_filtro})", "Tareas de recarga iniciadas", html, f"task_{stream_filtro}.png")
                archivos_notificar.append((ruta, f"*Tareas de Recarga:* {stream_filtro}", html, f"Recargas ({stream_filtro})"))

            if ws and archivos_notificar:
                chat_names = destino.get("nombre_chat", [])
                if isinstance(chat_names, str): chat_names = [chat_names]
                for chat in chat_names:
                    print(f"Enviando a WhatsApp: {chat}")
                    for ruta, msg, _, _ in archivos_notificar:
                        await ws.archivo(chat, ruta, texto=msg)

            if correo_enabled and CorreoSender:
                for email in destino.get("to", []):
                    try:
                        cs = CorreoSender()
                        for _, _, html_raw, titulo in archivos_notificar:
                            cuerpo = pic._insertar_Contenido(titulo, "Reporte automático", html_raw)
                            cs._enviar(destinatario=email, asunto=f"[QLIK] {titulo}", mensaje=cuerpo, is_html=True)
                    except Exception as e: print(f"Error Correo: {e}")

    finally:
        await pic.close()

    print("--- Proceso Finalizado ---")

if __name__ == "__main__":
    asyncio.run(main())


