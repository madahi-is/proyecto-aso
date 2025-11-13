import os
import stat
import subprocess

class Add:
    def check_directory( path: str):
        """
        Verifica si el directorio existe.
        Si no existe, lo crea con permisos 755 usando pkexec.
        Luego imprime el estado y abre la ventana Add Host.
        """
        if not path:
            print("[Error] Debe ingresar una ruta válida.")
            return

        if not os.path.exists(path):
            print(f"[INFO] El directorio '{path}' no existe. Se procederá a crearlo con permisos 755...")
            try:
                # Crear el directorio con privilegios de root (por seguridad)
                subprocess.run(["pkexec", "mkdir", "-p", path], check=True)
                subprocess.run(["pkexec", "chmod", "755", path], check=True)
                print(f"[OK] Directorio '{path}' creado con permisos 755.")
                self.add_host()
            except subprocess.CalledProcessError as e:
                print(f"[ERROR] No se pudo crear el directorio: {e}")
        else:
            print(f"[OK] El directorio '{path}' ya existe.")
            #self.add_host()
