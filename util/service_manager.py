"""
ServiceManager
--------------
Módulo para gestionar el servicio NFS (start, stop, restart, status, enable, disable)
"""

import subprocess
import shutil
from typing import Dict, List, Optional


class ServiceError(Exception):
    pass


class ServiceManager:
    """Gestiona el servicio NFS del sistema"""

    _privilege_cmd = None

    @staticmethod
    def _get_privilege_command():
        """Detecta qué comando usar para privilegios (pkexec o sudo)"""
        if ServiceManager._privilege_cmd is None:
            if shutil.which("pkexec"):
                ServiceManager._privilege_cmd = "pkexec"
            elif shutil.which("sudo"):
                ServiceManager._privilege_cmd = "sudo"
            else:
                raise ServiceError("No se encontró pkexec ni sudo en el sistema")
        return ServiceManager._privilege_cmd

    @staticmethod
    def _run_privileged(cmd: List[str], timeout: int = 10) -> subprocess.CompletedProcess:
        """Ejecuta un comando con privilegios"""
        priv_cmd = ServiceManager._get_privilege_command()
        return subprocess.run(
            [priv_cmd] + cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=timeout
        )

    @staticmethod
    def start() -> bool:
        """Inicia el servicio NFS"""
        try:
            res = ServiceManager._run_privileged(["systemctl", "start", "nfs-server"])
            if res.returncode != 0:
                raise ServiceError(f"Error al iniciar servicio: {res.stderr}")
            return True
        except Exception as e:
            raise ServiceError(f"No se pudo iniciar el servicio: {e}")

    @staticmethod
    def stop() -> bool:
        """Detiene el servicio NFS"""
        try:
            res = ServiceManager._run_privileged(["systemctl", "stop", "nfs-server"])
            if res.returncode != 0:
                raise ServiceError(f"Error al detener servicio: {res.stderr}")
            return True
        except Exception as e:
            raise ServiceError(f"No se pudo detener el servicio: {e}")

    @staticmethod
    def restart() -> bool:
        """Reinicia el servicio NFS"""
        try:
            res = ServiceManager._run_privileged(["systemctl", "restart", "nfs-server"])
            if res.returncode != 0:
                raise ServiceError(f"Error al reiniciar servicio: {res.stderr}")
            return True
        except Exception as e:
            raise ServiceError(f"No se pudo reiniciar el servicio: {e}")

    @staticmethod
    def enable() -> bool:
        """Habilita el servicio NFS para inicio automático"""
        try:
            res = ServiceManager._run_privileged(["systemctl", "enable", "nfs-server"])
            if res.returncode != 0:
                raise ServiceError(f"Error al habilitar servicio: {res.stderr}")
            return True
        except Exception as e:
            raise ServiceError(f"No se pudo habilitar el servicio: {e}")

    @staticmethod
    def disable() -> bool:
        """Deshabilita el servicio NFS del inicio automático"""
        try:
            res = ServiceManager._run_privileged(["systemctl", "disable", "nfs-server"])
            if res.returncode != 0:
                raise ServiceError(f"Error al deshabilitar servicio: {res.stderr}")
            return True
        except Exception as e:
            raise ServiceError(f"No se pudo deshabilitar el servicio: {e}")

    @staticmethod
    def status() -> Dict[str, str]:
        """Obtiene el estado detallado del servicio NFS"""
        try:
            # Estado activo/inactivo
            res_active = ServiceManager._run_privileged(["systemctl", "is-active", "nfs-server"])
            active_status = res_active.stdout.strip()

            # Estado de habilitado/deshabilitado
            res_enabled = ServiceManager._run_privileged(["systemctl", "is-enabled", "nfs-server"])
            enabled_status = res_enabled.stdout.strip()

            # Información detallada
            res_status = ServiceManager._run_privileged(["systemctl", "status", "nfs-server"])

            return {
                "active": active_status,
                "enabled": enabled_status,
                "status_output": res_status.stdout,
                "running": active_status == "active"
            }
        except Exception as e:
            return {
                "active": "unknown",
                "enabled": "unknown",
                "status_output": str(e),
                "running": False
            }

    @staticmethod
    def get_exports_active() -> List[Dict]:
        """Obtiene las exportaciones activas del sistema"""
        try:
            res = ServiceManager._run_privileged(["exportfs", "-v"])
            exports = []

            for line in res.stdout.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split()
                    if len(parts) >= 2:
                        export = {
                            "path": parts[0],
                            "client": parts[1] if len(parts) > 1 else "*",
                            "options": " ".join(parts[2:]) if len(parts) > 2 else ""
                        }
                        exports.append(export)

            return exports
        except Exception as e:
            raise ServiceError(f"No se pudieron obtener las exportaciones: {e}")

    @staticmethod
    def get_connected_clients() -> List[Dict]:
        """Obtiene la lista de clientes conectados actualmente"""
        try:
            res = ServiceManager._run_privileged(["showmount", "-a"])
            clients = []

            for line in res.stdout.split('\n'):
                line = line.strip()
                if line and ':' in line:
                    # Formato: hostname:/ruta
                    parts = line.split(':')
                    if len(parts) == 2:
                        client = {
                            "hostname": parts[0],
                            "mount_path": parts[1]
                        }
                        clients.append(client)

            return clients
        except Exception as e:
            # Si no hay clientes conectados, showmount puede fallar
            return []

