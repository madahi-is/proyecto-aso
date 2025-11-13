"""
BackupManager
-------------
Módulo para gestionar backups de la configuración de NFS
"""

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

EXPORTS_PATH = "/etc/exports"
BACKUP_DIR = "/var/backups/nfs-manager"

class BackupError(Exception):
    pass

class BackupManager:
    """Gestiona backups de la configuración NFS"""

    @staticmethod
    def _get_privilege_command():
        """Detecta qué comando usar para privilegios"""
        if shutil.which("pkexec"):
            return "pkexec"
        elif shutil.which("sudo"):
            return "sudo"
        else:
            raise BackupError("No se encontró pkexec ni sudo")

    @staticmethod
    def _run_privileged(cmd: List[str]) -> subprocess.CompletedProcess:
        """Ejecuta comando con privilegios"""
        priv_cmd = BackupManager._get_privilege_command()
        return subprocess.run(
            [priv_cmd] + cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=10
        )

    @staticmethod
    def create_backup(description: str = "") -> str:
        """
        Crea un backup del archivo /etc/exports
        Retorna el nombre del archivo de backup creado
        """
        try:
            # Crear directorio de backups si no existe
            res = BackupManager._run_privileged(["mkdir", "-p", BACKUP_DIR])
            if res.returncode != 0:
                raise BackupError(f"No se pudo crear directorio de backups: {res.stderr}")

            # Generar nombre del backup con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"exports_backup_{timestamp}.bak"
            backup_path = os.path.join(BACKUP_DIR, backup_filename)

            # Copiar archivo exports
            res = BackupManager._run_privileged(["cp", EXPORTS_PATH, backup_path])
            if res.returncode != 0:
                raise BackupError(f"No se pudo crear backup: {res.stderr}")

            # Guardar descripción si se proporcionó
            if description:
                info_path = backup_path + ".info"
                info_content = f"Timestamp: {timestamp}\nDescription: {description}\n"

                # Crear archivo temporal con la info
                import tempfile
                fd, tmp_path = tempfile.mkstemp(text=True)
                os.close(fd)
                with open(tmp_path, 'w') as f:
                    f.write(info_content)

                # Mover a ubicación final
                res = BackupManager._run_privileged(["mv", tmp_path, info_path])
                if res.returncode != 0:
                    os.remove(tmp_path)

            return backup_filename

        except Exception as e:
            raise BackupError(f"Error creando backup: {e}")

    @staticmethod
    def list_backups() -> List[Dict]:
        """
        Lista todos los backups disponibles
        Retorna lista de diccionarios con información de cada backup
        """
        try:
            # Verificar si el directorio existe
            res = BackupManager._run_privileged(["test", "-d", BACKUP_DIR])
            if res.returncode != 0:
                return []

            # Listar archivos de backup
            res = BackupManager._run_privileged(["ls", "-lt", BACKUP_DIR])
            if res.returncode != 0:
                return []

            backups = []
            for line in res.stdout.split('\n'):
                if '.bak' in line:
                    parts = line.split()
                    if len(parts) >= 9:
                        filename = parts[-1]
                        size = parts[4]
                        date = " ".join(parts[5:8])

                        # Extraer timestamp del nombre
                        try:
                            timestamp = filename.split('_')[2] + "_" + filename.split('_')[3].replace('.bak', '')
                        except:
                            timestamp = "unknown"

                        # Leer descripción si existe
                        description = ""
                        info_file = os.path.join(BACKUP_DIR, filename + ".info")
                        res_info = BackupManager._run_privileged(["cat", info_file])
                        if res_info.returncode == 0:
                            for info_line in res_info.stdout.split('\n'):
                                if info_line.startswith("Description:"):
                                    description = info_line.replace("Description:", "").strip()

                        backup = {
                            "filename": filename,
                            "timestamp": timestamp,
                            "size": size,
                            "date": date,
                            "description": description,
                            "full_path": os.path.join(BACKUP_DIR, filename)
                        }
                        backups.append(backup)

            return backups

        except Exception as e:
            raise BackupError(f"Error listando backups: {e}")

    @staticmethod
    def restore_backup(backup_filename: str) -> bool:
        """
        Restaura un backup específico
        """
        try:
            backup_path = os.path.join(BACKUP_DIR, backup_filename)

            # Verificar que el backup existe
            res = BackupManager._run_privileged(["test", "-f", backup_path])
            if res.returncode != 0:
                raise BackupError(f"El backup no existe: {backup_filename}")

            # Crear backup del estado actual antes de restaurar
            BackupManager.create_backup("Auto-backup antes de restaurar")

            # Restaurar el backup
            res = BackupManager._run_privileged(["cp", backup_path, EXPORTS_PATH])
            if res.returncode != 0:
                raise BackupError(f"No se pudo restaurar backup: {res.stderr}")

            # Recargar exportfs
            res = BackupManager._run_privileged(["exportfs", "-ra"])
            if res.returncode != 0:
                raise BackupError(f"Backup restaurado pero error al recargar exportfs: {res.stderr}")

            return True

        except Exception as e:
            raise BackupError(f"Error restaurando backup: {e}")

    @staticmethod
    def delete_backup(backup_filename: str) -> bool:
        """Elimina un backup específico"""
        try:
            backup_path = os.path.join(BACKUP_DIR, backup_filename)
            info_path = backup_path + ".info"

            # Eliminar archivo de backup
            res = BackupManager._run_privileged(["rm", "-f", backup_path])
            if res.returncode != 0:
                raise BackupError(f"No se pudo eliminar backup: {res.stderr}")

            # Eliminar archivo de info si existe
            BackupManager._run_privileged(["rm", "-f", info_path])

            return True

        except Exception as e:
            raise BackupError(f"Error eliminando backup: {e}")

    @staticmethod
    def get_backup_info(backup_filename: str) -> Optional[Dict]:
        """Obtiene información detallada de un backup"""
        try:
            backup_path = os.path.join(BACKUP_DIR, backup_filename)

            # Verificar que existe
            res = BackupManager._run_privileged(["test", "-f", backup_path])
            if res.returncode != 0:
                return None

            # Obtener información del archivo
            res = BackupManager._run_privileged(["stat", backup_path])
            if res.returncode != 0:
                return None

            # Leer contenido del backup
            res_content = BackupManager._run_privileged(["cat", backup_path])
            content = res_content.stdout if res_content.returncode == 0 else ""

            # Contar líneas de exportación
            export_count = 0
            for line in content.split('\n'):
                if line.strip() and not line.strip().startswith('#'):
                    export_count += 1

            return {
                "filename": backup_filename,
                "full_path": backup_path,
                "exports_count": export_count,
                "content": content
            }

        except Exception as e:
            raise BackupError(f"Error obteniendo información del backup: {e}")
