# Notify Hub

**Notify Hub** es el centro de monitoreo principal y de analítica enfocado en la infraestructura de Qlik Sense. Este componente rastrea tareas fallidas, elabora informes visuales del rendimiento de las recargas, y audita cualquier cambio realizado en los aplicativos. Todo se comunica mediante Correo Electrónico y WhatsApp.
## ✅WhatsApp 

para al terminar de enviar WhatsApp, se tiene que ejecutar "reducir_memoria_proceso" que esta en la clase WhatsApp, esto hace que el


## 📂 Estructura del Proyecto

```text
notify-hub/
├── Config/               # Configuraciones JSON (QlikMonitor, ReporteDeTiempoDeCarga, DeteccionDeModificaciones)
│   └── Const/            # Archivos constantes del core (constants.py con las claves para Qlik QRS)
├── Logs/                 # Registros de eventos operativos y errores localizados
├── requirement.txt       # Requisitos específicos para el análisis y conexión Qlik
├── Src/
│   ├── Integrations/     # Conectores externos (API de Qlik, Cliente SMTP, Automatización de WhatsApp)
│   ├── Scripts/          # Scripts principales del servicio
│   └── Utilities/        # Herramientas de manejo de gráficas (Matplotlib) y rastreadores de archivos (DetectorQlik)
└── Storage/              # Archivos y almacenamiento donde se analizan los ficheros en bruto (Audit Repository)
```

## ⚙️ Principales Scripts (`Src/Scripts/`)

# (Removed scripts related to QlikMonitor/ReporteDeCambios)

### 3. `ReporteDeTiempoDeCarga.py`
Genera inteligencia y analítica rápida sobre qué tareas (orientadas a extracción y modelo DWH / Stage QVD) toman más tiempo. 
- Lee el listado en formato `.csv`, grafica usando `matplotlib`, y adjunta directamente la visualización o las fotos a Correo y WhatsApp.

Instalación y Requisitos

1. Asegúrate de estar en la carpeta raíz `notify-hub`.
2. Instala los requerimientos:
   ```bash
   pip install -r requirement.txt
   ```
3. Si vas a permitir a Notify Hub usar la integración local para enviar informes gráficos a WhatsApp, necesitas Playwright:
   ```bash
   playwright install chromium
   ```


Asegúrate de haber introducido correctamente los certificados (`.pem`) del servidor de Qlik y configurado `Config/Const/constants.py` para que el script pueda interactuar de modo API. Luego prueba de forma independiente cada servicio:

```bash
python Src/Scripts/QlikMonitor.py
python Src/Scripts/ReporteDeCambios.py
python Src/Scripts/ReporteDeTiempoDeCarga.py
```

**Este texto sestá en negrita**

**texto en negrita**
***texto importante***
```python
print("Hola mundo")
```

usa `pip install`