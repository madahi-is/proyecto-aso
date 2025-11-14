import os
import subprocess
import shutil

class Add:
    @staticmethod
    def _get_privilege_command():
        """
        Detecta qué comando usar para obtener privilegios.
        Retorna 'pkexec' si está disponible, sino 'sudo'.
        """
        if shutil.which("pkexec"):
            return "pkexec"
        elif shutil.which("sudo"):
            return "sudo"
        else:
            raise RuntimeError("No se encontró pkexec ni sudo en el sistema")

    @staticmethod
    def check_directory(path: str):
        """
        Verifica si el directorio existe.
        Si no existe, lo crea con permisos 755 usando pkexec o sudo.
        Si ya existe, solo aplica los permisos 755 nuevamente.
        """
        if not path:
            print("[ERROR] No se especificó una ruta válida.")
            return

        try:
            priv_cmd = Add._get_privilege_command()
            print(f"[INFO] Usando '{priv_cmd}' para operaciones privilegiadas")

            if not os.path.exists(path):
                print(f"[INFO] El directorio '{path}' no existe. Creando con permisos 755...")
                subprocess.run([priv_cmd, "mkdir", "-p", path], check=True)
                subprocess.run([priv_cmd, "chmod", "755", path], check=True)
                print(f"[OK] Directorio '{path}' creado con permisos 755.")
            else:
                print(f"[INFO] El directorio '{path}' ya existe. Aplicando permisos 755...")
                subprocess.run([priv_cmd, "chmod", "755", path], check=True)
                print(f"[OK] Permisos 755 aplicados correctamente al directorio '{path}'.")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] No se pudo crear o modificar el directorio: {e}")
        except RuntimeError as e:
            print(f"[ERROR] {e}")
