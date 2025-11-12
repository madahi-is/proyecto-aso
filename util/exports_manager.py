# util/exports_manager.py
"""
ExportsManager
--------------
Módulo para listar / añadir / editar / eliminar entradas en /etc/exports
Diseñado para integrarse con una GUI. Usa pkexec para las operaciones que
requieren permisos de root (abrirá el diálogo gráfico en openSUSE).
"""

import os
import tempfile
import shutil
import subprocess
from typing import List, Dict, Optional

EXPORTS_PATH = "/etc/exports"
BACKUP_SUFFIX = ".bak"

class ExportsError(Exception):
    pass

class ExportsManager:
    @staticmethod
    def _run_pkexec(cmd: List[str], timeout: int = 10) -> subprocess.CompletedProcess:
        """Ejecuta un comando usando pkexec (dialogo gráfico de autenticación)."""
        return subprocess.run(["pkexec"] + cmd, capture_output=True, text=True, timeout=timeout)

    @staticmethod
    def _read_file_as_root(path: str) -> str:
        """
        Intenta leer el archivo. Si falla por permisos, usa 'pkexec cat'.
        Retorna el contenido del archivo como string.
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except PermissionError:
            res = ExportsManager._run_pkexec(["cat", path])
            if res.returncode != 0:
                raise ExportsError(f"No se pudo leer {path}: {res.stderr.strip()}")
            return res.stdout

    @staticmethod
    def list_raw() -> List[str]:
        """Devuelve las líneas crudas del /etc/exports (incluye comentarios y líneas vacías)."""
        content = ExportsManager._read_file_as_root(EXPORTS_PATH)
        return content.splitlines()

    @staticmethod
    def list_parsed() -> List[Dict]:
        """
        Parsea /etc/exports y retorna una lista de entradas:
        [
          {
            "path": "/srv/nfs",
            "hosts": [
              {"name": "192.168.1.0/24", "options": "(rw,sync)"},
              {"name": "10.0.0.5", "options": "(ro)"}
            ],
            "raw": "<línea original>",
            "lineno": <número de línea>
          }
        ]
        """
        lines = ExportsManager.list_raw()
        parsed = []

        for i, line in enumerate(lines, start=1):
            s = line.strip()
            if not s or s.startswith("#"):
                continue

            parts = s.split()
            path = parts[0]
            hosts = parts[1:]

            host_entries = []
            for h in hosts:
                # ejemplo: 192.168.1.0/24(rw,sync)
                if "(" in h and ")" in h:
                    name, opts = h.split("(", 1)
                    opts = "(" + opts  # restaurar el paréntesis inicial
                else:
                    name, opts = h, ""
                host_entries.append({
                    "name": name.strip(),
                    "options": opts.strip()
                })

            parsed.append({
                "path": path,
                "hosts": host_entries,
                "raw": line,
                "lineno": i
            })

        return parsed


    @staticmethod
    def backup(backup_path: Optional[str] = None) -> str:
        """
        Crea un backup de /etc/exports. Retorna la ruta del backup.
        Si backup_path no se provee, crea /etc/exports.bak
        """
        if backup_path is None:
            backup_path = EXPORTS_PATH + BACKUP_SUFFIX
        # Intentamos copia directa, si falla por permisos usamos pkexec cp
        try:
            shutil.copyfile(EXPORTS_PATH, backup_path)
        except PermissionError:
            res = ExportsManager._run_pkexec(["cp", EXPORTS_PATH, backup_path])
            if res.returncode != 0:
                raise ExportsError(f"No se pudo crear backup: {res.stderr.strip()}")
        return backup_path

    @staticmethod
    def _write_temp_and_move(new_text: str) -> None:
        """
        Escribe new_text a un archivo temporal y lo mueve atómicamente a /etc/exports
        usando pkexec para el mv (necesita permisos).
        También crea backup automático antes de mover.
        """
        # 1) crear temp file local
        fd, tmp_path = tempfile.mkstemp(prefix="exports_tmp_", text=True)
        os.close(fd)
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(new_text)
            # 2) crear backup
            ExportsManager.backup()
            # 3) mover temp a /etc/exports con pkexec (reemplaza fichero)
            res = ExportsManager._run_pkexec(["mv", tmp_path, EXPORTS_PATH])
            if res.returncode != 0:
                # intentar limpiar temp si mv falló
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
                raise ExportsError(f"No se pudo mover el archivo temporal a {EXPORTS_PATH}: {res.stderr.strip()}")
            # 4) recargar exportfs
            res2 = ExportsManager._run_pkexec(["exportfs", "-ra"])
            if res2.returncode != 0:
                # exportfs falló: restauramos backup y avisamos
                ExportsManager._run_pkexec(["cp", EXPORTS_PATH + BACKUP_SUFFIX, EXPORTS_PATH])
                raise ExportsError(f"exportfs devolvió error: {res2.stderr.strip()}")
        finally:
            # asegurar eliminación del temp en caso de que exista
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    @staticmethod
    def apply_new_content(new_text: str) -> None:
        """
        Reemplaza /etc/exports por new_text de forma atómica (backup + mv + exportfs -ra).
        """
        ExportsManager._write_temp_and_move(new_text)

    @staticmethod
    def add_entry(path: str, hosts_expr: str) -> None:
        """
        Añade una nueva entrada al final de /etc/exports.
        path: ruta del sistema a exportar, ej. /srv/nfs4
        hosts_expr: lo que va después, ej. "192.168.1.0/24(rw,sync,no_subtree_check)"
        """
        if not path or not hosts_expr:
            raise ValueError("path y hosts_expr son requeridos.")
        lines = ExportsManager.list_raw()
        # Comprobar si ya existe una entrada para la misma ruta (startswith)
        for l in lines:
            if l.strip().startswith(path):
                raise ExportsError(f"Ya existe una entrada para la ruta: {path}")
        if not lines or lines[-1].strip() != "":
            lines.append("")  # asegurar nueva línea antes de añadir
        lines.append(f"{path} {hosts_expr}")
        new_text = "\n".join(lines) + "\n"
        ExportsManager.apply_new_content(new_text)

    @staticmethod
    def remove_entry(match_path: str) -> None:
        """
        Elimina todas las líneas que comienzan con match_path.
        match_path: la ruta a buscar al inicio de la línea (ej. '/srv/nfs4').
        """
        lines = ExportsManager.list_raw()
        new_lines = [l for l in lines if not l.strip().startswith(match_path)]
        if len(new_lines) == len(lines):
            raise ExportsError(f"No se encontró ninguna entrada que comience con: {match_path}")
        new_text = "\n".join(new_lines) + "\n"
        ExportsManager.apply_new_content(new_text)

    @staticmethod
    def edit_entry(match_path: str, new_hosts_expr: str) -> None:
        """
        Reemplaza la primera línea que comienza con match_path por 'match_path new_hosts_expr'.
        """
        lines = ExportsManager.list_raw()
        new_lines = []
        replaced = False
        for l in lines:
            if (not replaced) and l.strip().startswith(match_path):
                new_lines.append(f"{match_path} {new_hosts_expr}")
                replaced = True
            else:
                new_lines.append(l)
        if not replaced:
            raise ExportsError(f"No se encontró ninguna entrada que comience con: {match_path}")
        new_text = "\n".join(new_lines) + "\n"
        ExportsManager.apply_new_content(new_text)

    @staticmethod
    def restore_backup(backup_path: Optional[str] = None) -> None:
        """
        Restaura el backup (por defecto /etc/exports.bak) y recarga exportfs.
        """
        backup = backup_path or (EXPORTS_PATH + BACKUP_SUFFIX)
        if not os.path.exists(backup):
            raise ExportsError("No existe backup para restaurar: " + backup)
        res = ExportsManager._run_pkexec(["cp", backup, EXPORTS_PATH])
        if res.returncode != 0:
            raise ExportsError("No se pudo restaurar backup: " + res.stderr.strip())
        res2 = ExportsManager._run_pkexec(["exportfs", "-ra"])
        if res2.returncode != 0:
            raise ExportsError("exportfs devolvió error al restaurar backup: " + res2.stderr.strip())
