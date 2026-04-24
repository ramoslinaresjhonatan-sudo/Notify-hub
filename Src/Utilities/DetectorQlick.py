import os
import json
import re
import csv
from glob import glob
from datetime import datetime

class QlikMonitor:

    IDX = {
        "Timestamp": 2,
        "Description": 5,
        "UserDirectory": 9,
        "UserId": 10,
        "ObjectName": 12,
        "Command": 16,
        "Message": 18,
    }

    def __init__(self, audit_path, sched_path, state_file, whitelist_csv=None):
        self.audit_path = audit_path
        self.sched_path = sched_path
        self.state_file = state_file
        self.whitelist_csv = whitelist_csv
        
        self.app_allow = set()
        self.task_allow = set()
        self.name_to_stream = {}
        self._load_whitelist()

    def _load_whitelist(self):
        if not self.whitelist_csv or not os.path.exists(self.whitelist_csv):
            print(f"Aviso: No se encontró la lista blanca en {self.whitelist_csv}. Se procesarán TODOS.")
            return

        try:
            with open(self.whitelist_csv, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    tipo = (row.get("tipo") or "").strip().upper()
                    nombre = (row.get("nombre") or "").strip()
                    stream = (row.get("stream") or "").strip().upper()
                    if not nombre: continue
                    
                    nombre_cf = nombre.casefold()
                    if tipo == "APP":
                        self.app_allow.add(nombre_cf)
                    elif tipo == "TASK":
                        self.task_allow.add(nombre_cf)
                    
                    self.name_to_stream[nombre_cf] = stream
            print(f"Cargadas {len(self.app_allow)} Apps y {len(self.task_allow)} Tareas permitidas.")
        except Exception as e:
            print(f"Error cargando lista blanca: {e}")

    def _is_allowed(self, name, allow_set):
        if not allow_set: return True
        return name.strip().casefold() in allow_set

    def _get_stream(self, name):
        return self.name_to_stream.get(name.strip().casefold(), "GENERAL")

    def load_state(self):
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except:
            return {"files": {}}

    def save_state(self, state):
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                final_data = json.load(f)
        except:
            final_data = {}
            
        final_data.update(state)
        
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(final_data, f, indent=2)

    def load_config(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def tail_file(self, path, offset):
        if not os.path.exists(path):
            return offset or 0, []

        size = os.path.getsize(path)
        if offset is None:
            offset = max(0, size - 8192)
        if offset > size:
            offset = 0

        with open(path, "rb") as f:
            f.seek(offset)
            data = f.read()
            new_offset = f.tell()

        lines = data.decode("utf-8", errors="ignore").splitlines()
        return new_offset, lines

    def _get_col(self, cols, name):
        idx = self.IDX.get(name)
        if idx is not None and idx < len(cols):
            return cols[idx].strip()
        return ""

    def scan_audit_logs(self, lines):
        events = []
        keywords = ["publish app", "replace app", "unpublish app"]
        
        for ln in lines:
            if not ln or ln.startswith("Sequence#"): continue
            
            low_ln = ln.lower()
            if any(k in low_ln for k in keywords):
                cols = ln.split("\t")
                app_name = self._get_col(cols, "ObjectName")
                
                if not self._is_allowed(app_name, self.app_allow):
                    continue

                ud = self._get_col(cols, "UserDirectory")
                usr = self._get_col(cols, "UserId")
                who = f"{ud}\\{usr}" if ud and usr else usr or ud or "Desconocido"

                events.append({
                    "type": "PUBLISH",
                    "timestamp": self._get_col(cols, "Timestamp"),
                    "object": app_name,
                    "command": self._get_col(cols, "Command") or "Publicación",
                    "who": who,
                    "stream": self._get_stream(app_name)
                })
        return events

    def scan_scheduler_logs(self, lines):
        events_dedup = {}
        
        for ln in lines:
            if not ln or ln.startswith("Sequence#"): continue
            
            low_ln = ln.lower()
            if "task execution" in low_ln and "to started" in low_ln:
                cols = ln.split("\t")
                task_name = self._get_col(cols, "ObjectName")
                
                if "|" in task_name:
                    task_name = task_name.split("|")[0].strip()

                if not self._is_allowed(task_name, self.task_allow):
                    continue

                ts = self._get_col(cols, "Timestamp")
                ts_sec = ts.split(".")[0] if ts else ts
                key = (task_name, ts_sec)

                if key not in events_dedup:
                    events_dedup[key] = {
                        "type": "RELOAD_START",
                        "timestamp": ts,
                        "object": task_name,
                        "command": "Inicio de Recarga",
                        "who": "System / Scheduler",
                        "stream": self._get_stream(task_name)
                    }
        
        return list(events_dedup.values())

    def process(self):
        state = self.load_state()
        
        es_embebido = "LINE_AUDIT" in state or "LINE_SHED" in state
        files_state = state.get("files", {})
        all_events = []

        for file in glob(self.audit_path):
            offset = state.get("LINE_AUDIT") if es_embebido else files_state.get(file, {}).get("off")
            new_offset, lines = self.tail_file(file, offset)
            
            if es_embebido: state["LINE_AUDIT"] = new_offset
            else: files_state[file] = {"off": new_offset}
            
            all_events.extend(self.scan_audit_logs(lines))

        for file in glob(self.sched_path):
            offset = state.get("LINE_SHED") if es_embebido else files_state.get(file, {}).get("off")
            new_offset, lines = self.tail_file(file, offset)
            
            if es_embebido: state["LINE_SHED"] = new_offset
            else: files_state[file] = {"off": new_offset}
            
            all_events.extend(self.scan_scheduler_logs(lines))

        if not es_embebido:
            state["files"] = files_state
        
        self.save_state(state)
        return all_events