import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.font import BOLD
import util.generic as utl
from util.exports_manager import ExportsManager
from util.add_directory import Add

class MasterPanel:
    def edit_directory(self):
        try:
            # 1️⃣ Verificar selección
            seleccion = self.treeview.selection()
            if not seleccion:
                messagebox.showwarning("Advertencia", "Por favor, seleccione un directorio primero.")
                return

            item_id = seleccion[0]
            item = self.treeview.item(item_id)
            path_seleccionado = item["values"][0]
            antigua_ruta = path_seleccionado
            print(f"[INFO] Editando directorio: {antigua_ruta}")

            # 2️⃣ Buscar host y opciones actuales
            entries = ExportsManager.list_parsed()
            nombre_host, opciones = "", ""
            for e in entries:
                if e["path"] == path_seleccionado:
                    if e["hosts"]:
                        nombre_host = e["hosts"][0].get("name", "")
                        opciones = e["hosts"][0].get("options", "")
                    break

            if not nombre_host:
                messagebox.showerror("Error", "No se encontraron hosts para el directorio seleccionado.")
                return

            # 3️⃣ Crear ventana de edición
            self.new_window = tk.Toplevel(self.ventana)
            self.new_window.geometry("350x150")
            self.new_window.title("Edit Directory")
            self.new_window.config(bg="#dce2ec")
            utl.centrar_ventana(self.new_window, 350, 150)

            top_frame = tk.Frame(self.new_window, bg="#dce2ec")
            top_frame.pack(pady=5)

            label = tk.Label(top_frame, text="Directory to Export:", font=("Times New Roman", 10), bg="#dce2ec")
            label.pack(pady=5)

            # 4️⃣ Campo editable con valor antiguo
            self.var_directorio = tk.StringVar(value=antigua_ruta)
            entry_directorio = ttk.Entry(top_frame, font=("Times New Roman", 10), textvariable=self.var_directorio, width=40)
            entry_directorio.pack()

            # Mostrar host y opciones (solo informativos)
            info_label = tk.Label(
                top_frame,
                text=f"Host: {nombre_host}\nOptions: {opciones}",
                font=("Times New Roman", 9),
                bg="#dce2ec",
                justify="left"
            )
            info_label.pack(pady=5)

            # 5️⃣ Botones
            boton_frame = tk.Frame(self.new_window, bg="#dce2ec")
            boton_frame.pack(pady=10)

            def confirmar_edicion():
                try:
                    ruta_nueva = self.var_directorio.get().strip()
                    if not ruta_nueva:
                        messagebox.showwarning("Advertencia", "Debe ingresar una ruta válida.")
                        return

                    # Verificar o crear directorio
                    Add.check_directory(ruta_nueva)

                    # Mantener mismo host y opciones
                    hosts_expr = f"{nombre_host}{opciones}"

                    # Añadir la nueva entrada
                    ExportsManager.add_entry(ruta_nueva, hosts_expr)

                    messagebox.showinfo("Éxito", f"Se agregó la nueva ruta:\n{ruta_nueva}")
                    self.new_window.destroy()

                    # Refrescar vista
                    self.refrescar_treeview()
                    self.add_host()

                except Exception as err:
                    messagebox.showerror("Error", f"No se pudo agregar la nueva ruta:\n{err}")

            boton_ok = tk.Button(
                boton_frame,
                text="OK",
                font=("Times New Roman", 10),
                bg="#b6c6e7",
                width=10, height=1,
                command=confirmar_edicion
            )
            boton_ok.pack(side="left", padx=5)

            boton_cancel = tk.Button(
                boton_frame,
                text="Cancel",
                font=("Times New Roman", 10),
                bg="#ccc5c4",
                width=10, height=1,
                command=self.new_window.destroy
            )
            boton_cancel.pack(side="left", padx=5)

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo editar el directorio:\n{e}")


    def refrescar_treeview(self):
        """
        Limpia y recarga el Treeview de directorios con las entradas actuales de /etc/exports.
        """
        try:
            # Limpiar Treeview
            for item in self.treeview.get_children():
                self.treeview.delete(item)

            # Cargar entradas actualizadas
            entries = ExportsManager.list_parsed()
            for e in entries:
                self.treeview.insert("", "end", values=(e["path"],))
        except Exception as err:
            print(f"[ERROR] No se pudo leer /etc/exports: {err}")

    def delete_directory(self, ruta):
        ExportsManager.remove_entry(ruta)
        self.refrescar_treeview() 

    def add_directory(self):
        self.new_window = tk.Toplevel(self.ventana)
        self.new_window.geometry("300x100")
        self.new_window.title("Add Directory")
        self.new_window.config(bg="#dce2ec")
        utl.centrar_ventana(self.new_window, 300, 100)
        
        top_frame = tk.Frame(self.new_window, bg="#dce2ec")
        top_frame.pack(pady=5)
        
        label = tk.Label(top_frame, text="Directory to Export", font=("Times New Roman", 10), bg="#dce2ec", anchor="e")
        label.pack( pady=5  )
        new_directory_entry = ttk.Entry(top_frame, font=("Times New Roman", 10))
        new_directory_entry.pack()

        boton_frame = tk.Frame(self.new_window, bg="#dce2ec")
        boton_frame.pack(pady=10)

        boton_ok = tk.Button(boton_frame, text="OK", font=("Times New Roman", 10), bg="#b6c6e7", width=10, height=1,command=lambda: self.directorio_leido(new_directory_entry.get()))
        boton_ok.pack(side="left", padx=5)
        boton_cancel = tk.Button(boton_frame, text="Cancel", font=("Times New Roman", 10), bg="#ccc5c4", width=10, height=1, command=self.new_window.destroy)
        boton_cancel.pack(side="left", padx=5)

    def directorio_leido(self, ruta):
        Add.check_directory(ruta)
        self.host = "*"
        self.opciones = "rw,sync,no_subtree_check"
        self.hosts_expr = f"{self.host}({self.opciones})"
        ExportsManager.add_entry(ruta, self.hosts_expr)
        self.new_window.destroy()
        # Refrescar Treeview
        self.refrescar_treeview()    
        self.add_host()


    def add_host(self):
        seleccion = tk.StringVar()
        self.new_host_window = tk.Toplevel(self.ventana)
        self.new_host_window.geometry("300x150")
        self.new_host_window.title("Add Host")
        self.new_host_window.config(bg="#dce2ec")
        utl.centrar_ventana(self.new_host_window, 200, 150)
        label = tk.Label(self.new_host_window, text="Host Wild Card", font=("Times New Roman", 10), bg="#dce2ec")
        label.pack( pady=5  )
        host_entry = ttk.Entry(self.new_host_window, font=("Times New Roman", 10))
        host_entry.pack()

        label_options = tk.Label(self.new_host_window, text="Options", font=("Times New Roman", 10), bg="#dce2ec")
        label_options.pack( pady=5  )

        combo = ttk.Combobox(self.new_host_window, textvariable=seleccion , font=("Times New Roman", 10))
        combo['values'] = ( "rw", "ro", "sync", "async", "no_root_squash", "root_squash",
        "all_squash", "no_subtree_check", "subtree_check", "insecure",
        "secure", "anonuid", "anongid")
        combo.pack()

        boton_frame = tk.Frame(self.new_host_window, bg="#dce2ec")
        boton_frame.pack(pady=10)

        boton_ok = tk.Button(boton_frame, text="OK", font=("Times New Roman", 10), bg="#b6c6e7", width=10, height=1)
        boton_ok.pack(side="left", padx=5)
        boton_cancel = tk.Button(boton_frame, text="Cancel", font=("Times New Roman", 10), bg="#ccc5c4", width=10, height=1, command=self.new_host_window.destroy)
        boton_cancel.pack(side="left", padx=5)   

    def actualizar_hosts(self, event):
        # Obtener selección del Treeview de directorios
        seleccion = self.treeview.selection()
        if not seleccion:
            return

        item = self.treeview.item(seleccion[0])
        path_seleccionado = item["values"][0]

        # Limpiar el Treeview de hosts
        for row in self.host_treeview.get_children():
            self.host_treeview.delete(row)

        # Obtener los hosts correspondientes desde ExportsManager
        try:
            entries = ExportsManager.list_parsed()
            for e in entries:
                if e["path"] == path_seleccionado:
                    for host in e["hosts"]:
                        nombre_host = host.get("name", "")
                        opciones = host.get("options", "")
                        self.host_treeview.insert("", "end", values=(nombre_host, opciones))
        except Exception as err:
            messagebox.showerror("Error", f"No se pudieron cargar los hosts:\n{err}")



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
	
	#Cargar datos reales de /etc/exports
        try:
            entries = ExportsManager.list_parsed()
            for e in entries:
                self.treeview.insert("", "end", values=(e["path"],))
        except Exception as err:
            messagebox.showerror("Error", f"No se pudo leer /etc/exports:\n{err}")
        
        # Cada vez que se selecciona un path, actualizar hosts
        self.treeview.bind("<<TreeviewSelect>>", self.actualizar_hosts)	

        #Botones 
        button_frame = tk.Frame(main_frame, bg="#dce2ec")
        button_frame.pack(pady=0) 

        boton_Add = tk.Button(button_frame, text="Add Directory", font=("Times New Roman", 10), bg="#dce2ec",width=12, height=1, command= self.add_directory)
        boton_Add.pack(side="left", padx=5)
        boton_edit = tk.Button(button_frame, text="Edit", font=("Times New Roman", 10), bg="#dce2ec",width=12, height=1, command=self.edit_directory)
        boton_edit.pack(side="left", padx=5)
        #boton_delete = tk.Button(button_frame, text="Delete", font=("Times New Roman", 10), bg="#dce2ec",width=12, height=1)
        boton_delete = tk.Button(button_frame, text="Delete", font=("Times New Roman", 10), bg="#dce2ec",width=12, height=1, command=lambda: self.delete_directory(self.treeview.item(self.treeview.selection())["values"][0]) )
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
        #self.host_treeview.insert("", "end", values=("192.168.0.*", "Allow"))
        #self.host_treeview.insert("", "end", values=("10.0.0.*", "Deny"))

        #botones host
        host_button_frame = tk.Frame(main_frame, bg="#dce2ec")
        host_button_frame.pack(pady=0)

        boton_host_add = tk.Button(host_button_frame, text="Add Host", font=("Times New Roman", 10), bg="#dce2ec",width=12, height=1, command= self.add_host)
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





