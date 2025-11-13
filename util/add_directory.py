import os
import subprocess

class Add:
    @staticmethod
    def check_directory(path: str):
        """
        Verifica si el directorio existe.
        Si no existe, lo crea con permisos 755 usando pkexec.
        Si ya existe, solo aplica los permisos 755 nuevamente.
        """
        if not path:
            print("[ERROR] No se especificó una ruta válida.")
            return

        try:
            if not os.path.exists(path):
                print(f"[INFO] El directorio '{path}' no existe. Creando con permisos 755...")
                subprocess.run(["pkexec", "mkdir", "-p", path], check=True)
                subprocess.run(["pkexec", "chmod", "755", path], check=True)
                print(f"[OK] Directorio '{path}' creado con permisos 755.")
            else:
                print(f"[INFO] El directorio '{path}' ya existe. Aplicando permisos 755...")
                subprocess.run(["pkexec", "chmod", "755", path], check=True)
                print(f"[OK] Permisos 755 aplicados correctamente al directorio '{path}'.")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] No se pudo crear o modificar el directorio: {e}")

