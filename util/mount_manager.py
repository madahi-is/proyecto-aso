"""
MountManager
------------
Módulo para gestionar montajes NFS desde la aplicación
"""

import os
import subprocess
import shutil
from typing import List, Dict, Optional

class MountError(Exception):
    pass

class MountManager:
    """Gestiona montajes NFS en el sistema"""

    @staticmethod
    def _get_privilege_command():
        """Detecta qué comando usar para privilegios"""
        if shutil.which("pkexec"):
            return "pkexec"
        elif shutil.which("sudo"):
            return "sudo"
        else:
            raise MountError("No se encontró pkexec ni sudo")

    @staticmethod
    def _run_privileged(cmd: List[str], timeout: int = 30) -> subprocess.CompletedProcess:
        """Ejecuta comando con privilegios"""
        priv_cmd = MountManager._get_privilege_command()
        return subprocess.run(
            [priv_cmd] + cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=timeout
        )

    @staticmethod
    def get_mounted_nfs() -> List[Dict]:
        """
        Obtiene la lista de sistemas NFS montados actualmente
        Retorna lista de diccionarios con información de cada montaje
        """
        try:
            result = subprocess.run(
                ["mount", "-t", "nfs,nfs4"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=10
            )

            mounted = []
            for line in result.stdout.split('\n'):
                if line.strip() and ':' in line:
                    # Formato: servidor:/path on /punto/montaje type nfs (opciones)
                    parts = line.split()
                    if len(parts) >= 6:
                        server_path = parts[0]  # servidor:/path
                        mount_point = parts[2]  # /punto/montaje
                        mount_type = parts[4]   # nfs o nfs4
                        options = parts[5] if len(parts) > 5 else ""

                        # Separar servidor y path
                        if ':' in server_path:
                            server, remote_path = server_path.split(':', 1)
                        else:
                            server = server_path
                            remote_path = "/"

                        mounted.append({
                            "server": server,
                            "remote_path": remote_path,
                            "mount_point": mount_point,
                            "type": mount_type,
                            "options": options.strip('()')
                        })

            return mounted

        except Exception as e:
            raise MountError(f"Error obteniendo montajes NFS: {e}")

    @staticmethod
    def mount_nfs(server: str, remote_path: str, mount_point: str, options: str = "") -> bool:
        """
        Monta un recurso NFS

        Args:
            server: IP o hostname del servidor NFS
            remote_path: Ruta remota a montar (ej: /srv/nfs/compartido)
            mount_point: Punto de montaje local (ej: /mnt/nfs/compartido)
            options: Opciones de montaje (ej: "rw,sync")

        Returns:
            True si se montó exitosamente
        """
        try:
            print(f"[INFO] Iniciando montaje de {server}:{remote_path} en {mount_point}")

            # Verificar que el punto de montaje existe, si no, crearlo
            if not os.path.exists(mount_point):
                print(f"[INFO] Creando punto de montaje: {mount_point}")
                res = MountManager._run_privileged(["mkdir", "-p", mount_point])
                if res.returncode != 0:
                    raise MountError(f"No se pudo crear punto de montaje: {res.stderr}")
                print(f"[OK] Punto de montaje creado")
            else:
                print(f"[INFO] Punto de montaje ya existe: {mount_point}")

            # Construir comando de montaje
            server_path = f"{server}:{remote_path}"
            cmd = ["mount", "-t", "nfs"]

            # Agregar opciones por defecto si no se especificaron
            if not options:
                options = "rw,sync"

            cmd.extend(["-o", options])
            cmd.extend([server_path, mount_point])

            # Mostrar comando completo
            print(f"[INFO] Comando: {' '.join(cmd)}")

            # Ejecutar montaje
            print(f"[INFO] Ejecutando montaje...")
            res = MountManager._run_privileged(cmd)

            print(f"[DEBUG] mount returncode: {res.returncode}")
            print(f"[DEBUG] mount stdout: {res.stdout}")
            print(f"[DEBUG] mount stderr: {res.stderr}")

            if res.returncode != 0:
                # Proporcionar mensaje de error más claro
                error_msg = res.stderr.strip()
                if "access denied" in error_msg.lower():
                    raise MountError(f"Acceso denegado. Verifique que:\n"
                                   f"1. El servidor permite conexiones desde este cliente\n"
                                   f"2. La ruta {remote_path} está exportada\n"
                                   f"3. Las opciones de permisos son correctas\n\n"
                                   f"Error: {error_msg}")
                elif "no route to host" in error_msg.lower():
                    raise MountError(f"No se puede alcanzar el servidor {server}.\n"
                                   f"Verifique la red y firewall.\n\n"
                                   f"Error: {error_msg}")
                elif "connection timed out" in error_msg.lower():
                    raise MountError(f"Timeout al conectar con {server}.\n"
                                   f"El servidor puede estar apagado o el puerto NFS bloqueado.\n\n"
                                   f"Error: {error_msg}")
                elif "program not registered" in error_msg.lower():
                    raise MountError(f"El servicio NFS no está corriendo en {server}.\n"
                                   f"En el servidor ejecute:\n"
                                   f"  sudo systemctl start nfs-server\n\n"
                                   f"Error: {error_msg}")
                else:
                    raise MountError(f"Error al montar: {error_msg}")

            print(f"[OK] Montaje exitoso!")
            return True

        except MountError:
            raise
        except Exception as e:
            raise MountError(f"No se pudo montar NFS: {e}")

    @staticmethod
    def unmount_nfs(mount_point: str, force: bool = False) -> bool:
        """
        Desmonta un recurso NFS

        Args:
            mount_point: Punto de montaje a desmontar
            force: Si True, fuerza el desmontaje (umount -f)

        Returns:
            True si se desmontó exitosamente
        """
        try:
            cmd = ["umount"]
            if force:
                cmd.append("-f")
            cmd.append(mount_point)

            print(f"[INFO] Desmontando {mount_point}")
            res = MountManager._run_privileged(cmd)

            if res.returncode != 0:
                raise MountError(f"Error al desmontar: {res.stderr}")

            return True

        except Exception as e:
            raise MountError(f"No se pudo desmontar NFS: {e}")

    @staticmethod
    def test_mount(server: str, remote_path: str, timeout: int = 5) -> bool:
        """
        Prueba si un recurso NFS está accesible sin montarlo

        Args:
            server: IP o hostname del servidor
            remote_path: Ruta remota
            timeout: Tiempo máximo de espera en segundos

        Returns:
            True si el recurso está accesible
        """
        try:
            # Usar showmount para verificar
            result = subprocess.run(
                ["showmount", "-e", server],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=timeout
            )

            if result.returncode == 0:
                # Verificar si la ruta específica está en los exports
                for line in result.stdout.split('\n'):
                    """ la linea extraida se vera asi: /srv/nfs/data   (everyone)"""
                    if remote_path in line.split()[0]:
                        return True
                # Si no encontramos la ruta exacta pero showmount funcionó
                return True

            return False

        except subprocess.TimeoutExpired:
            return False
        except Exception:

            return False

    @staticmethod
    def get_mount_options_presets() -> Dict[str, str]:
        """
        Retorna presets comunes de opciones de montaje
        """
        return {
            "Default": "rw,sync",
            "Read-Only": "ro,sync",
            "High Performance": "rw,async,noatime",
            "Soft Mount": "rw,soft,timeo=10",
            "Hard Mount": "rw,hard,intr",
            "NFSv4": "rw,sync,vers=4",
            "NFSv3": "rw,sync,vers=3"
        }

    @staticmethod
    def add_to_fstab(server: str, remote_path: str, mount_point: str,
                     options: str = "defaults,_netdev", backup: bool = True) -> bool:
        """
        Añade una entrada a /etc/fstab para montaje automático al inicio

        Args:
            server: IP o hostname del servidor
            remote_path: Ruta remota
            mount_point: Punto de montaje local
            options: Opciones de montaje
            backup: Si True, crea backup de fstab antes de modificar

        Returns:
            True si se añadió exitosamente
        """
        try:
            fstab_path = "/etc/fstab"

            # Crear backup si se solicita
            if backup:
                res = MountManager._run_privileged(["cp", fstab_path, f"{fstab_path}.bak"])
                if res.returncode != 0:
                    print("[WARNING] No se pudo crear backup de fstab")

            # Leer fstab actual
            try:
                with open(fstab_path, 'r') as f:
                    content = f.read()
            except PermissionError:
                res = MountManager._run_privileged(["cat", fstab_path])
                if res.returncode != 0:
                    raise MountError("No se pudo leer /etc/fstab")
                content = res.stdout

            # Verificar si ya existe una entrada para este mount_point
            for line in content.split('\n'):
                if line.strip() and not line.strip().startswith('#'):
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == mount_point:
                        raise MountError(f"Ya existe una entrada en fstab para {mount_point}")

            # Construir nueva entrada
            server_path = f"{server}:{remote_path}"
            new_entry = f"{server_path}\t{mount_point}\tnfs\t{options}\t0 0\n"

            # Crear archivo temporal con el nuevo contenido
            import tempfile
            fd, tmp_path = tempfile.mkstemp(text=True)
            os.close(fd)

            with open(tmp_path, 'w') as f:
                f.write(content)
                if not content.endswith('\n'):
                    f.write('\n')
                f.write(new_entry)

            # Mover el archivo temporal a fstab
            res = MountManager._run_privileged(["mv", tmp_path, fstab_path])
            if res.returncode != 0:
                os.remove(tmp_path)
                raise MountError(f"No se pudo actualizar fstab: {res.stderr}")

            return True

        except Exception as e:
            raise MountError(f"Error añadiendo entrada a fstab: {e}")

    @staticmethod
    def remove_from_fstab(mount_point: str, backup: bool = True) -> bool:
        """
        Elimina una entrada de /etc/fstab

        Args:
            mount_point: Punto de montaje a eliminar
            backup: Si True, crea backup antes de modificar

        Returns:
            True si se eliminó exitosamente
        """
        try:
            fstab_path = "/etc/fstab"

            # Crear backup
            if backup:
                res = MountManager._run_privileged(["cp", fstab_path, f"{fstab_path}.bak"])
                if res.returncode != 0:
                    print("[WARNING] No se pudo crear backup de fstab")

            # Leer fstab actual
            try:
                with open(fstab_path, 'r') as f:
                    lines = f.readlines()
            except PermissionError:
                res = MountManager._run_privileged(["cat", fstab_path])
                if res.returncode != 0:
                    raise MountError("No se pudo leer /etc/fstab")
                lines = res.stdout.split('\n')

            # Filtrar la línea del mount_point
            new_lines = []
            found = False
            for line in lines:
                if line.strip() and not line.strip().startswith('#'):
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == mount_point:
                        found = True
                        continue
                new_lines.append(line if isinstance(line, str) else line)

            if not found:
                raise MountError(f"No se encontró entrada en fstab para {mount_point}")

            # Crear archivo temporal
            import tempfile
            fd, tmp_path = tempfile.mkstemp(text=True)
            os.close(fd)

            with open(tmp_path, 'w') as f:
                f.writelines(new_lines)

            # Mover a fstab
            res = MountManager._run_privileged(["mv", tmp_path, fstab_path])
            if res.returncode != 0:
                os.remove(tmp_path)
                raise MountError(f"No se pudo actualizar fstab: {res.stderr}")

            return True

        except Exception as e:
            raise MountError(f"Error eliminando entrada de fstab: {e}")
