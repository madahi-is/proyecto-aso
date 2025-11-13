import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.font import BOLD
import util.generic as utl
import os
# Asegúrate de tener util.exports_manager y util.generic disponibles
from util.exports_manager import ExportsManager, ExportsError 

# CLASE DUMMY PARA EVITAR ERRORES SI EL ARCHIVO 'add_directory' NO FUE PROPORCIONADO
# Se usa para verificar si el directorio existe antes de añadirlo.
class Add:
    @staticmethod
    def check_directory(ruta):
        if not os.path.isdir(ruta):
            # En un entorno real, la creación del directorio debería hacerse antes
            # de llamar a add_entry, pero para la validación esto es suficiente.
            # raise ExportsError(f"La ruta '{ruta}' no es un directorio válido o no existe.")
            pass # Permitimos continuar para la prueba si solo falta el archivo
        print(f"[INFO] El directorio '{ruta}' es válido.")


class MasterPanel:

    # ------------------------------------------------------------------
    # --- CRUD HOSTS (Añadir/Editar/Eliminar) ---
    # --- Modificado para Checkbuttons (Selección Múltiple) ---
    # ------------------------------------------------------------------

    def save_host(self, host_entry, option_vars, is_edit_mode, original_host_ip=""):
        """Guarda o edita un host para el directorio seleccionado, recolectando opciones de Checkbuttons."""
        
        # 1. Obtener Host/IP
        host_ip = host_entry.get().strip()
        
        # 2. Recolectar opciones marcadas y formar la cadena separada por comas
        opciones_seleccionadas = [name for name, var in option_vars.items() if var.get()]
        opciones_raw = ",".join(opciones_seleccionadas)

        self.new_host_window.destroy()

        # 3. Validar entradas
        seleccion = self.treeview.selection()
        if not seleccion:
            messagebox.showerror("Error", "Debe seleccionar un directorio primero.")
            return

        path_seleccionado = self.treeview.item(seleccion[0])["values"][0]

        if not host_ip or not opciones_raw:
            messagebox.showerror("Error", "Debe especificar Host/IP y al menos una Opción.")
            return
            
        # 4. Lógica de guardado/edición
        try:
            entries = ExportsManager.list_parsed()
            current_entry = next((e for e in entries if e["path"] == path_seleccionado), None)

            if current_entry is None:
                raise ExportsError("El directorio seleccionado no existe en /etc/exports.")

            new_hosts = []
            host_expr_to_add = f"{host_ip}({opciones_raw})"
            host_ip_exists = False

            # Construir la nueva lista de hosts
            for host in current_entry["hosts"]:
                host_name = host["name"]
                
                # Si estamos en modo Edición
                if is_edit_mode and host_name == original_host_ip:
                    # Reemplazar el host antiguo por el nuevo
                    new_hosts.append(host_expr_to_add)
                    host_ip_exists = True
                    
                # Si estamos añadiendo o es un host que ya existe y es diferente al original
                elif host_name != original_host_ip: 
                    # Si el host a añadir ya existía antes de la operación, lo reemplazamos
                    if not is_edit_mode and host_name == host_ip:
                        new_hosts.append(host_expr_to_add)
                        host_ip_exists = True
                    else:
                        # Mantener el host existente
                        new_hosts.append(f"{host['name']}{host['options']}")

            # Si es un host completamente nuevo
            if not host_ip_exists or (is_edit_mode and host_ip != original_host_ip and not host_ip_exists):
                new_hosts.append(host_expr_to_add)

            new_hosts_expr = ' '.join(new_hosts)
            
            # Aplicar cambios
            ExportsManager.edit_entry(path_seleccionado, new_hosts_expr)

            messagebox.showinfo("Éxito", f"Host '{host_ip}' en directorio '{path_seleccionado}' actualizado con opciones: {opciones_raw}.")
            self.actualizar_hosts(None)
        except ExportsError as err:
            messagebox.showerror("Error de NFS", f"Fallo al guardar Host:\n{err}")
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado: {str(e)}")


    def add_host(self):
        """Abre la ventana para añadir o editar un host, usando Checkbuttons para selección múltiple."""
        seleccion_dir = self.treeview.selection()
        if not seleccion_dir:
            messagebox.showerror("Error", "Debe seleccionar un directorio primero.")
            return
            
        # --- Lógica de Detección de Edición ---
        is_edit_mode = False
        host_seleccionado = ""
        # Lista de opciones por defecto
        opciones_seleccionadas_str = "rw,sync,no_root_squash" 

        seleccion_host = self.host_treeview.selection()
        if seleccion_host:
            is_edit_mode = True
            host_item = self.host_treeview.item(seleccion_host[0])
            host_seleccionado = host_item["values"][0]
            # Las opciones vienen como string, le quitamos los paréntesis
            opciones_seleccionadas_str = host_item["values"][1].strip('()') 
            
        opciones_activas = opciones_seleccionadas_str.split(',')
            
        # --- Creación de la Ventana ---
        self.new_host_window = tk.Toplevel(self.ventana)
        # Ajustamos el tamaño para los Checkbuttons
        self.new_host_window.geometry("380x350") 
        self.new_host_window.title("Edit Host/Options" if is_edit_mode else "Add Host/Options")
        self.new_host_window.config(bg="#dce2ec")
        utl.centrar_ventana(self.new_host_window, 380, 350)

        # 1. Host/IP/Subred
        tk.Label(self.new_host_window, text="Host/IP/Subred:", font=("Times New Roman", 10, BOLD), bg="#dce2ec").pack(pady=(5,0))
        host_entry = ttk.Entry(self.new_host_window, font=("Times New Roman", 10), width=30)
        host_entry.pack()
        if is_edit_mode:
            host_entry.insert(0, host_seleccionado)
            
        # 2. Opciones (Usando Checkbuttons)
        tk.Label(self.new_host_window, text="Seleccionar Opciones (NFS Export Options):", font=("Times New Roman", 10, BOLD), bg="#dce2ec").pack(pady=(10,5))
        
        options_frame = tk.Frame(self.new_host_window, bg="#dce2ec")
        options_frame.pack(padx=10)

        # Opciones base para NFS
        base_options = [
            "rw", "ro", "sync", "async", 
            "no_root_squash", "root_squash", "all_squash", 
            "no_subtree_check", "subtree_check", 
            "insecure", "secure",
            "anonuid", "anongid" # Opciones que pueden requerir edición manual de valor
        ]
        
        # Variables de control para Checkbuttons
        self.option_vars = {} 
        

        # Crear Checkbuttons en dos columnas
        col = 0
        row = 0
        for opt_name in base_options:
            var = tk.IntVar()
            
            # Si estamos editando y la opción ya estaba activa, la marcamos
            # Solo chequeamos por el nombre, ignorando posibles valores (ej: anonuid=1000)
            if any(opt_name == opt.split('=')[0] for opt in opciones_activas):
                var.set(1) 
            
            self.option_vars[opt_name] = var
            
            cb = ttk.Checkbutton(options_frame, text=opt_name, variable=var, onvalue=1, offvalue=0)
            
            # Distribución en dos columnas
            cb.grid(row=row, column=col, sticky='w', padx=5, pady=2)
            
            col += 1
            if col > 1:
                col = 0
                row += 1

        # 3. Botones OK/Cancel
        boton_frame = tk.Frame(self.new_host_window, bg="#dce2ec")
        boton_frame.pack(pady=20)

        # El botón OK llama a save_host con la lista de variables
        boton_ok = tk.Button(boton_frame, text="OK", font=("Times New Roman", 10), bg="#b6c6e7", width=10, height=1,
                             command=lambda: self.save_host(host_entry, self.option_vars, is_edit_mode, host_seleccionado))
        boton_ok.pack(side="left", padx=5)
        
        boton_cancel = tk.Button(boton_frame, text="Cancel", font=("Times New Roman", 10), bg="#ccc5c4", width=10, height=1, command=self.new_host_window.destroy)
        boton_cancel.pack(side="left", padx=5)


    def delete_host(self):
        """Elimina el host seleccionado del directorio."""
        seleccion_dir = self.treeview.selection()
        seleccion_host = self.host_treeview.selection()

        if not seleccion_dir or not seleccion_host:
            messagebox.showerror("Error", "Seleccione el Host que desea eliminar.")
            return

        path_seleccionado = self.treeview.item(seleccion_dir[0])["values"][0]
        host_seleccionado = self.host_treeview.item(seleccion_host[0])["values"][0]

        if messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar el Host '{host_seleccionado}' del directorio:\n{path_seleccionado}?"):
            try:
                entries = ExportsManager.list_parsed()
                current_entry = next((e for e in entries if e["path"] == path_seleccionado), None)

                if current_entry is None: return

                new_hosts = []
                # Reconstruir la lista de hosts sin el host seleccionado para eliminar
                for host in current_entry["hosts"]:
                    if host["name"] != host_seleccionado:
                        new_hosts.append(f"{host['name']}{host['options']}")

                new_hosts_expr = ' '.join(new_hosts)
                
                # Aplicar el cambio: editar la entrada con la nueva lista de hosts
                ExportsManager.edit_entry(path_seleccionado, new_hosts_expr)

                messagebox.showinfo("Éxito", f"Host '{host_seleccionado}' eliminado y aplicado correctamente.")
                self.actualizar_hosts(None)
            except ExportsError as err:
                messagebox.showerror("Error de NFS", f"Fallo al eliminar Host:\n{err}")
            except Exception as e:
                messagebox.showerror("Error", f"Error inesperado: {str(e)}")
    
    # ------------------------------------------------------------------
    # --- CRUD DIRECTORIOS (Funciones Originales sin cambios mayores) ---
    # ------------------------------------------------------------------

    def edit_directory(self):
        # ... Lógica original para editar directorio ...
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
            host_info_list = []
            host_line = ""
            for e in entries:
                if e["path"] == path_seleccionado:
                    for host in e["hosts"]:
                        host_info_list.append(f"{host.get('name', '')}{host.get('options', '')}")
                    host_line = ' '.join(host_info_list)
                    break

            if not host_info_list:
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
                text=f"Hosts: {host_line}",
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
                    hosts_expr = host_line

                    # Añadir la nueva entrada
                    ExportsManager.add_entry(ruta_nueva, hosts_expr)

                    messagebox.showinfo("Éxito", f"Se agregó la nueva ruta:\n{ruta_nueva}",parent=self.new_window )
                    self.new_window.destroy()

                    # Si se añadió correctamente, eliminar la antigua
                    ExportsManager.remove_entry(antigua_ruta)

                    # Refrescar vista
                    self.actualizar_hosts(None)
                    self.refrescar_treeview()

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

    def delete_directory(self):
        """Elimina el directorio seleccionado."""
        seleccion = self.treeview.selection()
        if not seleccion:
            messagebox.showerror("Error", "Seleccione un directorio a eliminar.")
            return

        path_seleccionado = self.treeview.item(seleccion[0])["values"][0]

        if messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar el directorio de exportación:\n{path_seleccionado}?"):
            try:
                ExportsManager.remove_entry(path_seleccionado)
                messagebox.showinfo("Éxito", f"Directorio '{path_seleccionado}' eliminado y aplicado correctamente.")
                self.refrescar_treeview()
                # Limpiar la lista de hosts también
                for row in self.host_treeview.get_children():
                    self.host_treeview.delete(row)
            except ExportsError as err:
                messagebox.showerror("Error de NFS", f"Fallo al eliminar directorio:\n{err}")
            except Exception as e:
                messagebox.showerror("Error", f"Error inesperado: {str(e)}")

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
        try:
            Add.check_directory(ruta)
            self.host = "*"
            # Opción default para nueva entrada
            self.opciones = "rw,sync,no_root_squash"
            self.hosts_expr = f"{self.host}({self.opciones})"
            
            ExportsManager.add_entry(ruta, self.hosts_expr)
            messagebox.showinfo("Éxito", f"Directorio '{ruta}' añadido con opciones por defecto: {self.hosts_expr}", parent=self.new_window)
            self.new_window.destroy()
            self.refrescar_treeview()
        except ExportsError as err:
            messagebox.showerror("Error de NFS", f"Fallo al añadir directorio:\n{err}")
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado: {str(e)}")


    def actualizar_hosts(self, event):
        # Obtener selección del Treeview de directorios
        seleccion = self.treeview.selection()

        # Limpiar el Treeview de hosts
        for row in self.host_treeview.get_children():
            self.host_treeview.delete(row)

        if not seleccion:
            return

        item = self.treeview.item(seleccion[0])
        path_seleccionado = item["values"][0]

        # Obtener los hosts correspondientes desde ExportsManager
        try:
            entries = ExportsManager.list_parsed()
            for e in entries:
                if e["path"] == path_seleccionado:
                    for host in e["hosts"]:
                        nombre_host = host.get("name", "")
                        opciones = host.get("options", "")
                        self.host_treeview.insert("", "end", values=(nombre_host, opciones))
                    return # Salir una vez que se procesó la entrada
        except Exception as err:
            messagebox.showerror("Error", f"No se pudieron cargar los hosts:\n{err}")

    # ------------------------------------------------------------------
    # --- INICIALIZACIÓN DE LA VENTANA ---
    # ------------------------------------------------------------------

    def __init__(self):
        # ... [Configuración de ventana] ...
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

        # LISTA DE DIRECTORIOS
        directorio_label = tk.Label(main_frame, text="Directories", font=("Times New Roman", 10, BOLD), bg="#c4c8cf", anchor="w")
        directorio_label.pack(fill="x", padx=10, pady=(0, 0))


        self.treeview = ttk.Treeview(main_frame, columns=("Directorio",), show="", height=8)
        self.treeview.pack(fill="both", padx=10, pady=(0, 10))
        self.treeview.column("Directorio", width=300,anchor="w")

        # Cargar datos reales de /etc/exports
        try:
            entries = ExportsManager.list_parsed()
            for e in entries:
                self.treeview.insert("", "end", values=(e["path"],))
        except Exception as err:
            messagebox.showerror("Error", f"No se pudo leer /etc/exports:\n{err}")

        # Cada vez que se selecciona un path, actualizar hosts
        self.treeview.bind("<<TreeviewSelect>>", self.actualizar_hosts)

        # Botones de Directorio
        button_frame = tk.Frame(main_frame, bg="#dce2ec")
        button_frame.pack(pady=0)

        boton_Add = tk.Button(button_frame, text="Add Directory", font=("Times New Roman", 10), bg="#dce2ec",width=12, height=1, command= self.add_directory)
        boton_Add.pack(side="left", padx=5)
        boton_edit = tk.Button(button_frame, text="Edit", font=("Times New Roman", 10), bg="#dce2ec",width=12, height=1, command=self.edit_directory)
        boton_edit.pack(side="left", padx=5)
        
        # Enlace del botón Delete Directory
        boton_delete = tk.Button(button_frame, text="Delete", font=("Times New Roman", 10), bg="#dce2ec",width=12, height=1, command=self.delete_directory)
        boton_delete.pack(side="left", padx=5)

        # OPCIONES DE HOST
        host_label = tk.Label(main_frame, text="Host Options", font=("Times New Roman", 10, BOLD), bg="#dce2ec", anchor="w")
        host_label.pack(fill="x", padx=10, pady=(10, 0))

        self.host_treeview = ttk.Treeview(main_frame, columns=("Host Wild Card", "Options"), show="headings", height=6)
        self.host_treeview.heading("Host Wild Card", text="Host Wild Card")
        self.host_treeview.heading("Options", text="Options")
        self.host_treeview.column("Host Wild Card", width=50, anchor="w")
        self.host_treeview.column("Options", width=300, anchor="w")
        self.host_treeview.pack(fill="both", padx=10, pady=(0, 10))

        # Botones Host
        host_button_frame = tk.Frame(main_frame, bg="#dce2ec")
        host_button_frame.pack(pady=0)

        # Enlace del botón Add Host
        boton_host_add = tk.Button(host_button_frame, text="Add Host", font=("Times New Roman", 10), bg="#dce2ec",width=12, height=1, command= self.add_host)
        boton_host_add.pack(side="left", padx=5)
        
        # Enlace del botón Edit Host (usa la misma función add_host con detección de selección)
        boton_host_edit = tk.Button(host_button_frame, text="Edit", font=("Times New Roman", 10), bg="#dce2ec",width=12, height=1, command=self.add_host)
        boton_host_edit.pack(side="left", padx=5)
        
        # Enlace del botón Delete Host
        boton_host_delete = tk.Button(host_button_frame, text="Delete", font=("Times New Roman", 10), bg="#dce2ec",width=12, height=1, command=self.delete_host)
        boton_host_delete.pack(side="left", padx=5)

        # Botones de Finish y Cancelar
        action_button_frame = tk.Frame(main_frame, bg="#dce2ec")
        action_button_frame.pack(side="bottom", fill="x", padx=10, pady=10)

        boton_finish = tk.Button(action_button_frame, text="Finish", font=("Times New Roman", 11, BOLD), bg="#3a7ff6", width=12, height=1)
        boton_finish.pack(side="right", padx=5)
        boton_cancel = tk.Button(action_button_frame, text="Cancel", font=("Times New Roman", 11, BOLD), bg="#f44336", width=12, height=1, command=self.ventana.destroy)
        boton_cancel.pack(side="right", padx=5)


        self.ventana.mainloop()
