import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.font import BOLD
import util.generic as utl
from forms.form_master import MasterPanel
import getpass
import subprocess

class App:
    def validar_login(self):
        usuario = self.usuario.get()
        contrasena = self.contrasena.get()

        # Login normal demo
        if usuario == "admin" and contrasena == "1234":
            print("[INFO] Login demo exitoso")
            self.root_user = None  # No se usarán credenciales de root
            self.root_pass = None
            self.ventana.destroy()
            MasterPanel()
            return
        # Login superusuario real
        try:
            cmd = ["sudo", "-S", "id"]
            proc = subprocess.run(
                cmd,
                input=contrasena + "\n",
                universal_newlines=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            if proc.returncode == 0:
                print(f"[OK] Usuario root válido: {usuario}")
                self.root_user = usuario
                self.root_pass = contrasena
                self.ventana.destroy()
                #MasterPanel(root_user=usuario, root_pass=contrasena)
                MasterPanel()
            else:
                print("[ERROR] Credenciales root incorrectas")
                tk.messagebox.showerror("Error de login", "Usuario o contraseña root incorrectos.")
        except Exception as e:
            tk.messagebox.showerror("Error de login", f"No se pudo verificar root:\n{e}")

    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Login")
        self.ventana.geometry("800x500")
        self.ventana.config(bg="#fcfcfc")
        self.ventana.resizable(width=0, height=0)
        utl.centrar_ventana(self.ventana, 800, 500)

        logo = utl.leer_imagen("imagenes/nfs.png", (200, 200))

        # Frame_logo
        frame_logo = tk.Frame(self.ventana, bd=0, width=300, relief=tk.SOLID, padx=10, pady=10, bg="#7babfd")
        frame_logo.pack(side="left", expand=tk.YES, fill=tk.BOTH)
        label = tk.Label(frame_logo, image=logo, bg="#7babfd")
        label.place(x=0, y=0, relheight=1,relwidth=1)

        # Frame_login
        frame_form = tk.Frame(self.ventana, bd=0, width=500, relief=tk.SOLID, bg="#fcfcfc")
        frame_form.pack(side="right", expand=tk.YES, fill=tk.BOTH)

        frame_form_top = tk.Frame(frame_form, height=50, bd=0 , relief=tk.SOLID, bg="#130b0b")
        frame_form_top.pack(side="top", fill=tk.X)
        title = tk.Label(frame_form_top, text="Iniciar sesión", font=("Times New Roman", 30), fg="#666a88", bg="#fcfcfc", pady=30)
        title.pack(expand=tk.YES, fill=tk.BOTH)
        description = tk.Label(frame_form_top, text="Las acciones a continuacion necesita privilegios de root.\nPor favor, introdusca a continuación el usuario y contraseña del usuario root.", font=("Times New Roman", 10), fg="#666a88", bg="#fcfcfc", justify="left", wraplength=360)
        description.pack(expand=tk.YES, fill=tk.BOTH)
        

        # frame_form_fill
        frame_form_fill = tk.Frame(frame_form, height=50, bd=0 , relief=tk.SOLID, bg="#fcfcfc")
        frame_form_fill.pack(side="bottom", fill=tk.BOTH, expand=tk.YES)

        etiqueta_usuario = tk.Label(frame_form_fill, text="Usuario:", font=("Times New Roman", 14), fg="#666a88", bg="#fcfcfc",anchor="w")
        etiqueta_usuario.pack(fill=tk.X, padx=20, pady=5)
        self.usuario = ttk.Entry(frame_form_fill, font=("Times New Roman", 14))
        self.usuario.pack(fill=tk.X, padx=20, pady=10)

        etiqueta_contrasena = tk.Label(frame_form_fill, text="Contraseña:", font=("Times New Roman", 14), fg="#666a88", bg="#fcfcfc",anchor="w")
        etiqueta_contrasena.pack(fill=tk.X, padx=20, pady=5)
        self.contrasena = ttk.Entry(frame_form_fill, font=("Times New Roman", 14))
        self.contrasena.pack(fill=tk.X, padx=20, pady=10)
        self.contrasena.config(show="*")

        boton_login = tk.Button(frame_form_fill, text="Iniciar sesión", font=("Times New Roman", 15,BOLD),bg="#649af8", command=self.validar_login)
        boton_login.pack(fill=tk.X, padx=20, pady=20)
        boton_login.bind("<Return>", lambda event: self.validar_login())

        self.ventana.mainloop()

if __name__ == "__main__":
    App()
