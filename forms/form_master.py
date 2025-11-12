import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.font import BOLD
import util.generic as utl

class MasterPanel:

    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Master panel")
        w, h = self.ventana.winfo_screenwidth(), self.ventana.winfo_screenheight()
        self.ventana.geometry("%dx%d+0+0" % (w, h))
        self.ventana.config(bg="#fcfcfc")
        self.ventana.resizable(True, True)
        utl.centrar_ventana(self.ventana, 900, 600)
        label = tk.Label(self.ventana, bg="#dce2ec")
        label.place(x=0, y=0, relheight=1,relwidth=1)

                # ======== MARCO PRINCIPAL =========
        main_frame = tk.Frame(self.ventana, bg="#dce2ec", relief="flat")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # ======== TÍTULO SUPERIOR =========
        title_label = tk.Label(
            main_frame,
            text="Directories to Export",
            font=("Times New Roman", 11, BOLD),
            bg="#dce2ec",
            anchor="w"
        )
        title_label.pack(fill="x", padx=10, pady=(5, 10))

        #LISTA DE DIRECTORIOS 
        directorio_label = tk.Label(main_frame, text="Directories", font=("Times New Roman", 10, BOLD), bg="#c4c8cf", anchor="w")
        directorio_label.pack(fill="x", padx=10, pady=(0, 0))
        

        self.treeview = ttk.Treeview(main_frame, columns=("Directorio",), show="", height=8)
        self.treeview.pack(fill="both", padx=10, pady=(0, 10))
        self.treeview.column("Directorio", width=300,anchor="w")

        # Insertar datos de ejemplo
        self.treeview.insert("", "end", values=("/opt/data/",))
        self.treeview.insert("", "end", values=("/srv/nfs/",))

        #Botones 
        button_frame = tk.Frame(main_frame, bg="#dce2ec")
        button_frame.pack(pady=0) 

        boton_Add = tk.Button(button_frame, text="Add Directory", font=("Times New Roman", 10), bg="#dce2ec",width=12, height=1)
        boton_Add.pack(side="left", padx=5)
        boton_edit = tk.Button(button_frame, text="Edit", font=("Times New Roman", 10), bg="#dce2ec",width=12, height=1)
        boton_edit.pack(side="left", padx=5)
        boton_delete = tk.Button(button_frame, text="Delete", font=("Times New Roman", 10), bg="#dce2ec",width=12, height=1)
        boton_delete.pack(side="left", padx=5)
        
        #OPCIONES DE HOST
        host_label = tk.Label(main_frame, text="Host Options", font=("Times New Roman", 10, BOLD), bg="#dce2ec", anchor="w")
        host_label.pack(fill="x", padx=10, pady=(10, 0))

        self.host_treeview = ttk.Treeview(main_frame, columns=("Host Wild Card", "Options"), show="headings", height=6)
        self.host_treeview.heading("Host Wild Card", text="Host Wild Card")
        self.host_treeview.heading("Options", text="Options")
        self.host_treeview.column("Host Wild Card", width=50, anchor="w")
        self.host_treeview.column("Options", width=300, anchor="w")
        self.host_treeview.pack(fill="both", padx=10, pady=(0,  10))
        # Insertar datos de ejemplo
        self.host_treeview.insert("", "end", values=("192.168.0.*", "Allow"))
        self.host_treeview.insert("", "end", values=("10.0.0.*", "Deny"))

        #botones host
        host_button_frame = tk.Frame(main_frame, bg="#dce2ec")
        host_button_frame.pack(pady=0)

        boton_host_add = tk.Button(host_button_frame, text="Add Host", font=("Times New Roman", 10), bg="#dce2ec",width=12, height=1)
        boton_host_add.pack(side="left", padx=5)
        boton_host_edit = tk.Button(host_button_frame, text="Edit", font=("Times New Roman", 10), bg="#dce2ec",width=12, height=1)
        boton_host_edit.pack(side="left", padx=5)
        boton_host_delete = tk.Button(host_button_frame, text="Delete", font=("Times New Roman", 10), bg="#dce2ec",width=12, height=1)
        boton_host_delete.pack(side="left", padx=5)

        # Botones de Finish y Cancelar
        action_button_frame = tk.Frame(main_frame, bg="#dce2ec")
        action_button_frame.pack(side="bottom", fill="x", padx=10, pady=10)

        boton_finish = tk.Button(action_button_frame, text="Finish", font=("Times New Roman", 11, BOLD), bg="#3a7ff6", width=12, height=1)
        boton_finish.pack(side="right", padx=5)      
        boton_cancel = tk.Button(action_button_frame, text="Cancel", font=("Times New Roman", 11, BOLD), bg="#f44336", width=12, height=1, command=self.ventana.destroy)
        boton_cancel.pack(side="right", padx=5)


        self.ventana.mainloop()





