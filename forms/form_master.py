import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.font import BOLD
import util.generic as utl
import os
# Asegúrate de tener util.exports_manager y util.generic disponibles
from util.exports_manager import ExportsManager, ExportsError 

# ====================================================================
# === 1. CLASE ADD CORREGIDA (Crea directorios si no existen) ========
# ====================================================================
class Add:
    """Clase para manejar verificaciones y creación de directorios."""
    @staticmethod
    def check_directory(ruta):
        """Verifica si la ruta existe y la crea si es necesario."""
        # 1. Verificar si la ruta está vacía
        if not ruta.strip():
            raise ExportsError("La ruta del directorio no puede estar vacía.")
            
        # 2. Verificar si el directorio existe
        if not os.path.isdir(ruta):
            print(f"[INFO] El directorio '{ruta}' no existe. Intentando crearlo...")
            try:
                # 3. Crear el directorio si no existe (Requiere permisos de root/sudo)
                os.makedirs(ruta, mode=0o755, exist_ok=True)
                print(f"[INFO] Directorio '{ruta}' creado exitosamente.")
            except OSError as e:
                # Capturar errores de permiso si no se ejecuta como root
                raise ExportsError(f"Fallo al crear el directorio '{ruta}': {e}. ⚠️ Debe ejecutar la aplicación con 'sudo'.")
            
        print(f"[INFO] El directorio '{ruta}' es válido y existe.")

# ====================================================================
# === 2. CLASE MASTERPANEL (Lógica Principal) ========================
# ====================================================================
class MasterPanel:

    # ------------------------------------------------------------------
    # --- CRUD HOSTS (Añadir/Editar/Eliminar) ---
    # ------------------------------------------------------------------

    def save_host(self, host_entry, option_vars, is_edit_mode, original_host_ip="", anonuid_val="", anongid_val=""):
        """Guarda o edita un host, recolectando opciones de Checkbuttons y valores de anonuid/anongid."""
        
        # 1. Obtener Host/IP
        host_ip = host_entry.get().strip()
        
        # 2. Recolectar opciones marcadas y construir la cadena de opciones
        opciones_finales = []
        for name, var in option_vars.items():
            if var.get():
                # Manejar opciones con valor (anonuid/anongid)
                if name == "anonuid":
                    if anonuid_val:
                        if not anonuid_val.isdigit():
                            messagebox.showerror("Error", "anonuid debe ser un valor numérico.", parent=self.new_host_window)
                            return
                        opciones_finales.append(f"anonuid={anonuid_val}")
                elif name == "anongid":
                    if anongid_val:
                        if not anongid_val.isdigit():
                            messagebox.showerror("Error", "anongid debe ser un valor numérico.", parent=self.new_host_window)
                            return
                        opciones_finales.append(f"anongid={anongid_val}")
                elif name != "anonuid" and name != "anongid":
                    # Opciones sin valor
                    opciones_finales.append(name)
        
        opciones_raw = ",".join(opciones_finales)

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
                
                # Modo Edición: Reemplazar el host antiguo
                if is_edit_mode and host_name == original_host_ip:
                    new_hosts.append(host_expr_to_add)
                    host_ip_exists = True
                    
                # Si estamos añadiendo o es un host que ya existe y es diferente al original
                elif host_name != original_host_ip: 
                    if not is_edit_mode and host_name == host_ip:
                        # Si es el host que se está añadiendo/editando (mismo IP), reemplazar
                        new_hosts.append(host_expr_to_add)
                        host_ip_exists = True
                    else:
                        # Mantener el host existente
                        new_hosts.append(f"{host['name']}{host['options']}")

            # Si es un host completamente nuevo (y no existía ya en la lista)
            if not is_edit_mode and not host_ip_exists:
                new_hosts.append(host_expr_to_add)
            elif is_edit_mode and host_ip != original_host_ip and not host_ip_exists:
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
        """Abre la ventana para añadir o editar un host, usando Checkbuttons y campos para valores numéricos."""
        seleccion_dir = self.treeview.selection()
        if not seleccion_dir:
            messagebox.showerror("Error", "Debe seleccionar un directorio primero.")
            return
            
        # --- Lógica de Detección de Edición ---
        is_edit_mode = False
        host_seleccionado = ""
        opciones_seleccionadas_str = "rw,sync,no_root_squash" 
        anonuid_val = ""
        anongid_val = ""

        seleccion_host = self.host_treeview.selection()
        if seleccion_host:
            is_edit_mode = True
            host_item = self.host_treeview.item(seleccion_host[0])
            host_seleccionado = host_item["values"][0]
            opciones_seleccionadas_str = host_item["values"][1].strip('()') 
            
        opciones_activas = opciones_seleccionadas_str.split(',')
            
        # --- Extracción de valores de anonuid/anongid para Edición ---
        if is_edit_mode:
            for opt in opciones_activas:
                if '=' in opt:
                    key, val = opt.split('=', 1)
                    if key == "anonuid":
                        anonuid_val = val
                    elif key == "anongid":
                        anongid_val = val
            
        # --- Creación de la Ventana ---
        self.new_host_window = tk.Toplevel(self.ventana)
        self.new_host_window.geometry("400x400") 
        self.new_host_window.title("Edit Host/Options" if is_edit_mode else "Add Host/Options")
        self.new_host_window.config(bg="#dce2ec")
        utl.centrar_ventana(self.new_host_window, 400, 400)

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

        base_options = [
            "rw", "ro", "sync", "async", 
            "no_root_squash", "root_squash", "all_squash", 
            "no_subtree_check", "subtree_check", 
            "insecure", "secure"
        ]
        
        # Variables de control para Checkbuttons
        self.option_vars = {} 
        
        # Crear Checkbuttons en dos columnas
        col = 0
        row = 0
        for opt_name in base_options:
            var = tk.IntVar()
            
            # Chequear si la opción está activa (ignorando valores)
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

        # 3. Campos para opciones de valor (anonuid/anongid)
        value_options_frame = tk.Frame(self.new_host_window, bg="#dce2ec")
        value_options_frame.pack(pady=10)

        # anonuid
        tk.Label(value_options_frame, text="anonuid:", bg="#dce2ec").grid(row=0, column=0, padx=5, sticky='e')
        self.anonuid_var = tk.StringVar(value=anonuid_val)
        self.anonuid_entry = ttk.Entry(value_options_frame, textvariable=self.anonuid_var, width=15)
        self.anonuid_entry.grid(row=0, column=1, padx=5)
        # Checkbutton para anonuid (se activa si hay un valor, o se marca explícitamente)
        self.option_vars["anonuid"] = tk.IntVar(value=1 if anonuid_val else 0)

        # anongid
        tk.Label(value_options_frame, text="anongid:", bg="#dce2ec").grid(row=1, column=0, padx=5, sticky='e')
        self.anongid_var = tk.StringVar(value=anongid_val)
        self.anongid_entry = ttk.Entry(value_options_frame, textvariable=self.anongid_var, width=15)
        self.anongid_entry.grid(row=1, column=1, padx=5)
        # Checkbutton para anongid
        self.option_vars["anongid"] = tk.IntVar(value=1 if anongid_val else 0)


        # 4. Botones OK/Cancel
        boton_frame = tk.Frame(self.new_host_window, bg="#dce2ec")
        boton_frame.pack(pady=20)

        boton_ok = tk.Button(boton_frame, text="OK", font=("Times New Roman", 10), bg="#b6c6e7", width=10, height=1,
                             command=lambda: self.save_host(
                                 host_entry, 
                                 self.option_vars, 
                                 is_edit_mode, 
                                 host_seleccionado,
                                 anonuid_val=self.anonuid_var.get().strip(),
                                 anongid_val=self.anongid_var.get().strip()
                             ))
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
    # --- CRUD DIRECTORIOS CORREGIDO ---
    # ------------------------------------------------------------------

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

            # 2️⃣ Buscar y recopilar TODAS las expresiones de hosts
            entries = ExportsManager.list_parsed()
            host_info_list = []
            host_line = ""
            current_entry = next((e for e in entries if e["path"] == path_seleccionado), None)

            if current_entry:
                for host in current_entry["hosts"]:
                    host_info_list.append(f"{host.get('name', '')}{host.get('options', '')}")
                host_line = ' '.join(host_info_list)
            
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

                    # 🔑 CORRECCIÓN PRINCIPAL: Verifica y crea el directorio si no existe
                    Add.check_directory(ruta_nueva)

                    # Mantener mismo host y opciones
                    hosts_expr = host_line

                    # 🔑 LÓGICA DE RENOMBRE: Eliminar la antigua, Añadir la nueva
                    
                    # 1. Eliminar la antigua
                    ExportsManager.remove_entry(antigua_ruta)

                    # 2. Añadir la nueva entrada
                    ExportsManager.add_entry(ruta_nueva, hosts_expr)

                    messagebox.showinfo("Éxito", f"Directorio editado:\nDe: {antigua_ruta}\nA: {ruta_nueva}",parent=self.new_window )
                    self.new_window.destroy()

                    # Refrescar vista
                    self.actualizar_hosts(None)
                    self.refrescar_treeview()

                except ExportsError as err:
                    # Captura errores específicos de NFS/filesystem
                    messagebox.showerror("Error de NFS", f"No se pudo editar el directorio:\n{err}")
                except Exception as err:
                    messagebox.showerror("Error", f"No se pudo editar el directorio:\n{err}")
            
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
        """Limpia y recarga el Treeview de directorios con las entradas actuales de /etc/exports."""
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
        label.pack( pady=5 )
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
            # 🔑 Usa la clase Add corregida para crear el directorio
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
