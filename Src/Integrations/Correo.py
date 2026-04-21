import os
import sys
import smtplib
import logging
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class Correo:

    def __init__(self, server, port, email_address, display_name, error_recipients):
        self.server = server
        self.port = port
        self.email_address = email_address
        self.display_name = display_name
        self.error_recipients = error_recipients

    def _prepare_recipients(self, to):
        if isinstance(to, str):
            return [r.strip() for r in to.replace(";", ",").split(",") if r.strip()]
        return to

    def send_mail(self, to, subject, message, attachments=None, is_html=False):

        try:
            recipients = self._prepare_recipients(to)
            msg = MIMEMultipart('alternative')
            msg['From'] = f'{self.display_name} <{self.email_address}>'
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = subject

            # Tratamiento automático de HTML
            force_html = is_html or message.strip().lower().startswith("<html")
            content_type = 'html' if force_html else 'plain'
            msg.attach(MIMEText(message, content_type))

            # Manejo unificado de adjuntos
            if attachments:
                attachment_list = [attachments] if isinstance(attachments, str) else attachments
                for path in attachment_list:
                    if os.path.exists(path):
                        with open(path, "rb") as file_attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(file_attachment.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(path)}"')
                        msg.attach(part)
                    else:
                        logging.warning(f"No se encontró el archivo adjunto para enviar: {path}")

            with smtplib.SMTP(self.server, self.port) as server_smtp:
                server_smtp.sendmail(self.email_address, recipients, msg.as_string())
            
            logging.info(f"Correo enviado correctamente a: {', '.join(recipients)}")
            return True
        except Exception as e:
            logging.error(f"Error enviando correo genérico a {to}: {e}")
            return False

    def send_styled_report(self, to, subject, content):

        cuerpo_html = content.replace("\n", "<br>")
        color_header = "#667eea" # Azul corporativo por defecto
        
        titulo_lower = subject.lower()
        if "error" in titulo_lower or "fallo" in titulo_lower:
            color_header = "#d63031" # Rojo para errores
        elif "recarga" in titulo_lower or "éxito" in titulo_lower or "exito" in titulo_lower:
            color_header = "#28a745" # Verde para éxitos

        html = f"""
        <html>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; color: #333; line-height: 1.6; background-color: #f4f7f6; padding: 20px;">
            <div style="max-width: 800px; margin: 0 auto; border: 1px solid #eaeaea; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); background-color: #ffffff;">
                <div style="background-color: {color_header}; color: white; padding: 25px; text-align: center;">
                    <h2 style="margin: 0; font-weight: 600; font-size: 24px;">{subject}</h2>
                </div>
                <div style="padding: 35px;">
                    <div style="font-size: 16px; color: #444;">
                        {cuerpo_html}
                    </div>
                </div>
                <div style="background-color: #fafafa; padding: 20px; text-align: center; font-size: 13px; color: #999; border-top: 1px solid #eeeeee;">
                    Generado automáticamente por el Ecosistema BI el <strong>{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</strong><br>
                    <span style="color: #777; font-weight: 600; margin-top: 5px; display: inline-block;">Mamayatech - Business Intelligence</span>
                </div>
            </div>
        </body>
        </html>
        """
        return self.send_mail(to, subject, html, is_html=True)

    def send_error_report(self, process_name, server_name, error_message, to=None):
        if to is None:
            to = self.error_recipients

        table_html = f"""
        <table border="0" width="100%" cellpadding="12" cellspacing="0" style="border-collapse: collapse; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 650px; margin: auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden;">
            <thead style="background-color: #d63031; color: white;">
                <tr>
                    <th colspan="3" style="padding: 20px; font-size: 20px; font-weight: 600; text-transform: uppercase;">⚠️ Alerta de Extracción</th>
                </tr>
                <tr style="background-color: #b32425; font-size: 14px; text-align: left;">
                    <th>Proceso Afectado</th>
                    <th>Fecha Incidencia</th>
                    <th>Servidor</th>
                </tr>
            </thead>
            <tbody style="font-size: 14px; background-color: #ffffff; color: #333;">
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 15px; font-weight: 500;">{process_name}</td>
                    <td style="padding: 15px;">{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</td>
                    <td style="padding: 15px; font-weight: 500;">{server_name}</td>
                </tr>
                <tr>
                    <td colspan="3" style="background-color: #fcfcfc; padding: 15px 15px 5px 15px; font-weight: bold; text-align: left; color: #666;">
                        Detalle Técnico del Error:
                    </td>
                </tr>
                <tr>
                    <td colspan="3" style="padding: 15px; text-align: left;">
                        <div style="background-color: #fff5f5; border-left: 4px solid #d63031; padding: 12px; color: #c0392b; font-family: Consolas, monospace; font-size: 13px; white-space: pre-wrap; word-break: break-all;">
                            {error_message}
                        </div>
                    </td>
                </tr>
            </tbody>
        </table>
        """
        subject = f"Error Crítico: Proceso de Extracción - {process_name}"
        return self.send_mail(to, subject, table_html, is_html=True)

    def send_tasks_summary(self, subject, tasks, state_description, to=None):
        if to is None:
            try:
                actual_dir = os.path.dirname(os.path.abspath(__file__))
                root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(actual_dir))))
                if root_dir not in sys.path:
                    sys.path.insert(0, root_dir)
                from Config.QlikMonitor.constants import RECIPIES_EMAIL
                to = RECIPIES_EMAIL
            except ImportError:
                to = ["smatny.ext@mamayatech.com", "esdrey.vaca@mamayatech.com"]

        if not tasks:
            logging.info(f"No hay tareas con estado '{state_description}'. No se emite correo.")
            return False

        html_content = f"""
        <html>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #2c3e50; padding: 20px; background-color: #f7f9fc;">
            <div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); max-width: 900px; margin: auto;">
                <h2 style="color:#2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; margin-top: 0;">
                    Monitor Qlik Sense: <span style="color: #666; font-weight: normal;">{state_description}</span>
                </h2>
                <p style="font-size: 16px; margin-bottom: 25px;">Se encontraron <strong style="font-size: 18px; color: #e74c3c;">{len(tasks)}</strong> tarea(s) registradas con este estado.</p>
                
                <table cellpadding="12" cellspacing="0" style="border-collapse: collapse; width:100%; font-size: 14px; border: 1px solid #ecf0f1;">
                    <thead style="background-color:#f8f9fa; text-align: left; border-bottom: 2px solid #dde1e5;">
                        <tr style="color: #7f8c8d;">
                            <th>Nombre de la Tarea</th>
                            <th>App Relacionada</th>
                            <th style="text-align: center;">Estado</th>
                            <th>Inicio y Fin</th>
                            <th>Duración</th>
                            <th>Mensaje Reportado</th>
                        </tr>
                    </thead>
                    <tbody>
        """

        for task in tasks:
            op = task.get('operational', {})
            last_result = op.get('lastExecutionResult', {})
            details = last_result.get('details', [])
            last_message = details[-1]['message'] if details else "Sin detalle disponible"
            
            status = last_result.get('status', 'N/A')
            status_style = "background: #f1f2f6; color: #57606f;"
            if status == "FinishedSuccess": 
                status_style = "background: #e5f9e7; color: #2ecc71;"
            elif status in ["FinishedFail", "Failed"]: 
                status_style = "background: #fdeceb; color: #e74c3c;"
            
            start_time = last_result.get('startTime', 'N/A').split('T')[0] if 'T' in str(last_result.get('startTime', '')) else last_result.get('startTime', 'N/A')
            stop_time = last_result.get('stopTime', 'N/A').split('T')[0] if 'T' in str(last_result.get('stopTime', '')) else last_result.get('stopTime', 'N/A')

            html_content += f"""
                        <tr style="border-bottom: 1px solid #ecf0f1; transition: background-color 0.3s;">
                            <td style="font-weight: 600; color: #34495e;">{task.get('name', 'N/A')}</td>
                            <td style="color: #7f8c8d;">{task.get('app', {}).get('name', 'General/N/A')}</td>
                            <td style="text-align:center;">
                                <span style="{status_style} padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; display: inline-block;">
                                    {status}
                                </span>
                            </td>
                            <td style="font-size: 13px; color: #95a5a6;">
                                {start_time}<br>
                                <span style="font-size: 11px;">{stop_time}</span>
                            </td>
                            <td style="font-weight: 500; text-align: right;">{last_result.get('duration', 0)} ms</td>
                            <td style="color: #7f8c8d; font-size: 13px; max-width: 250px; overflow: hidden; text-overflow: ellipsis;">
                                {last_message}
                            </td>
                        </tr>
            """

        html_content += """
                    </tbody>
                </table>
                <div style="margin-top: 30px; font-size: 12px; color:#bdc3c7; text-align: center; border-top: 1px solid #eee; padding-top: 15px;">
                    Notificación Automática | Mamayatech Business Intelligence
                </div>
            </div>
        </body>
        </html>
        """
        return self.send_mail(to, subject, html_content, is_html=True)
