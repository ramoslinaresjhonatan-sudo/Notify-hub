import os
import sys
import json
import asyncio
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from Src.Integrations.WhatsApp import WhatsApp

CONFIG_PATH = os.path.join(ROOT_DIR, "Config", "NotifyHub-Automatizacion.json")

def esta_en_horario(intervalo):
    if not intervalo:
        return False
    try:
        partes = intervalo.replace("[", "").replace("]", "").split("-")
        if len(partes) != 2:
            return False
        hora_inicio = datetime.strptime(partes[0].strip(), "%H:%M").time()
        hora_fin = datetime.strptime(partes[1].strip(), "%H:%M").time()
        hora_actual = datetime.now().time()
        if hora_inicio <= hora_fin:
            return hora_inicio <= hora_actual <= hora_fin
        else:
            return hora_actual >= hora_inicio or hora_actual <= hora_fin
    except Exception as e:
        print(f"Error al validar horario '{intervalo}': {e}")
        return False

def obtener_procesos_activos():
    if not os.path.exists(CONFIG_PATH):
        print(f"Error: No se encontró {CONFIG_PATH}")
        return []
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        procesos_activos = [p for p in data.get("procesos", []) if esta_en_horario(p.get("IntervaloDeHorario"))]
        return procesos_activos
    except Exception as e:
        print(f"Error al leer procesos activos: {e}")
        return []

async def main():
    procesos = obtener_procesos_activos()
    
    if not procesos:
        print("No hay procesos activos en este horario.")
        return

    wa = WhatsApp()
    
    if not await wa.conectar():
        print("Error: No se pudo establecer conexión con WhatsApp.")
        return

    try:
        for proceso in procesos:
            nombre_tarea = proceso.get("nombre", "Proceso")
            resumen_file = proceso.get("resumen")
            archivos_adjuntos = proceso.get("rutas", [])
            destinatarios = proceso.get("envio_Whatsapp", [])

            print(f"\nEjecutando: {nombre_tarea}")

            mensaje_final = f"*Notificación de Automatización: {nombre_tarea}*\n\n"
            if resumen_file and os.path.exists(resumen_file):
                with open(resumen_file, "r", encoding="utf-8") as f:
                    mensaje_final += f.read()
            else:
                mensaje_final += "El proceso ha finalizado correctamente."

            for destino in destinatarios:
                print(f"  -> Enviando a grupo: {destino}")
                
                await wa.mensaje(destino, mensaje_final)
                
                for ruta in archivos_adjuntos:
                    if os.path.exists(ruta):
                        print(f"     + Adjuntando: {os.path.basename(ruta)}")
                        await wa.archivo(destino, ruta)
                    else:
                        print(f"     ! Archivo no encontrado: {ruta}")

    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
    finally:
        await wa.cerrar()

if __name__ == "__main__":
    asyncio.run(main())
