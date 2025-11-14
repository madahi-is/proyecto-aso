import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from tkinter.font import BOLD
import util.generic as utl
from util.service_manager import ServiceManager, ServiceError
from util.backup_manager import BackupManager, BackupError
from util.mount_manager import MountManager, MountError

class ClientManagerPanel:
    """Panel de gestión de clientes NFS y servicios"""

    def __init__(self, parent=None):
        if parent:
            self.ventana = tk.Toplevel(parent)
        else:
            self.ventana = tk.Tk()

        self.ventana.title("NFS Client & Service Manager")
        self.ventana.geometry("1000x800")
        self.ventana.config(bg="#fcfcfc")
        self.ventana.resizable(True, True)
        utl.centrar_ventana(self.ventana, 1000, 800)

        # Frame principal
        self.setup_ui()

        # Cargar datos iniciales
        self.refresh_all()

        if not parent:
            self.ventana.mainloop()

    def setup_ui(self):
        """Configura la interfaz de usuario CON SCROLL"""
        # Fondo
        bg_label = tk.Label(self.ventana, bg="#dce2ec")
        bg_label.place(x=0, y=0, relheight=1, relwidth=1)

        # ======== CREAR CANVAS Y SCROLLBAR ========
        # Canvas principal que contendrá todo
        canvas = tk.Canvas(self.ventana, bg="#dce2ec", highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=20)

        # Scrollbar vertical
        scrollbar = ttk.Scrollbar(self.ventana, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y", padx=(0, 20), pady=20)

        # Configurar canvas para usar scrollbar
        canvas.configure(yscrollcommand=scrollbar.set)

        # Frame que contendrá todo el contenido (dentro del canvas)
        main_frame = tk.Frame(canvas, bg="#dce2ec")

        # Crear ventana en el canvas
        canvas_window = canvas.create_window((0, 0), window=main_frame, anchor="nw")

        # Función para actualizar el scroll region cuando cambie el tamaño
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Ajustar el ancho del frame al ancho del canvas
            canvas_width = event.width
            canvas.itemconfig(canvas_window, width=canvas_width)

        main_frame.bind("<Configure>", configure_scroll_region)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))

        # Habilitar scroll con la rueda del ratón
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        # Bind para diferentes sistemas operativos
        canvas.bind_all("<MouseWheel>", _on_mousewheel)  # Windows y MacOS
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux scroll up
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))   # Linux scroll down

        # ======== SECCIONES ========
        # ======== SECCIÓN 1: ESTADO DEL SERVICIO ========
        self.setup_service_section(main_frame)

        # ======== SECCIÓN 2: EXPORTACIONES ACTIVAS ========
        self.setup_exports_section(main_frame)

        # ======== SECCIÓN 3: CLIENTES CONECTADOS ========
        self.setup_clients_section(main_frame)

        # ======== SECCIÓN 4: MONTAJES NFS ========
        self.setup_mounts_section(main_frame)

        # ======== SECCIÓN 5: BACKUPS ========
        self.setup_backup_section(main_frame)

        # ======== BOTONES INFERIORES ========
        self.setup_bottom_buttons(main_frame)

        # Actualizar scroll region inicial
        main_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    def setup_service_section(self, parent):
        """Sección de control del servicio"""
        # Título
        title = tk.Label(
            parent,
            text="NFS Service Control",
            font=("Times New Roman", 12, BOLD),
            bg="#dce2ec",
            anchor="w"
        )
        title.pack(fill="x", padx=10, pady=(5, 5))

        # Frame de contenido
        service_frame = tk.Frame(parent, bg="#ffffff", relief="raised", bd=1)
        service_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Estado del servicio
        status_frame = tk.Frame(service_frame, bg="#ffffff")
        status_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(status_frame, text="Status:", font=("Times New Roman", 10, BOLD),
                bg="#ffffff").pack(side="left", padx=5)
        self.status_label = tk.Label(status_frame, text="Unknown",
                                     font=("Times New Roman", 10), bg="#ffffff")
        self.status_label.pack(side="left", padx=5)

        tk.Label(status_frame, text="Enabled:", font=("Times New Roman", 10, BOLD),
                bg="#ffffff").pack(side="left", padx=15)
        self.enabled_label = tk.Label(status_frame, text="Unknown",
                                      font=("Times New Roman", 10), bg="#ffffff")
        self.enabled_label.pack(side="left", padx=5)

        # Botones de control
        buttons_frame = tk.Frame(service_frame, bg="#ffffff")
        buttons_frame.pack(fill="x", padx=10, pady=(0, 10))

        btn_width = 10
        tk.Button(buttons_frame, text="Start", font=("Times New Roman", 9),
                 bg="#4CAF50", fg="white", width=btn_width,
                 command=self.service_start).pack(side="left", padx=3)

        tk.Button(buttons_frame, text="Stop", font=("Times New Roman", 9),
                 bg="#f44336", fg="white", width=btn_width,
                 command=self.service_stop).pack(side="left", padx=3)

        tk.Button(buttons_frame, text="Restart", font=("Times New Roman", 9),
                 bg="#2196F3", fg="white", width=btn_width,
                 command=self.service_restart).pack(side="left", padx=3)

        tk.Button(buttons_frame, text="Enable", font=("Times New Roman", 9),
                 bg="#FF9800", fg="white", width=btn_width,
                 command=self.service_enable).pack(side="left", padx=3)

        tk.Button(buttons_frame, text="Disable", font=("Times New Roman", 9),
                 bg="#9E9E9E", fg="white", width=btn_width,
                 command=self.service_disable).pack(side="left", padx=3)

        tk.Button(buttons_frame, text="Refresh", font=("Times New Roman", 9),
                 bg="#607D8B", fg="white", width=btn_width,
                 command=self.refresh_service_status).pack(side="left", padx=3)

    def setup_exports_section(self, parent):
        """Sección de exportaciones activas"""
        title = tk.Label(
            parent,
            text="Active Exports",
            font=("Times New Roman", 11, BOLD),
            bg="#dce2ec",
            anchor="w"
        )
        title.pack(fill="x", padx=10, pady=(10, 5))

        # Treeview
        self.exports_tree = ttk.Treeview(
            parent,
            columns=("Path", "Client", "Options"),
            show="headings",
            height=6
        )
        self.exports_tree.heading("Path", text="Export Path")
        self.exports_tree.heading("Client", text="Client")
        self.exports_tree.heading("Options", text="Options")
        self.exports_tree.column("Path", width=300)
        self.exports_tree.column("Client", width=150)
        self.exports_tree.column("Options", width=300)
        self.exports_tree.pack(fill="x", padx=10, pady=(0, 10))

    def setup_clients_section(self, parent):
        """Sección de clientes conectados"""
        title = tk.Label(
            parent,
            text="Connected Clients",
            font=("Times New Roman", 11, BOLD),
            bg="#dce2ec",
            anchor="w"
        )
        title.pack(fill="x", padx=10, pady=(10, 5))

        # Treeview
        self.clients_tree = ttk.Treeview(
            parent,
            columns=("Hostname", "Mount Path"),
            show="headings",
            height=5
        )
        self.clients_tree.heading("Hostname", text="Client Hostname")
        self.clients_tree.heading("Mount Path", text="Mounted Path")
        self.clients_tree.column("Hostname", width=200)
        self.clients_tree.column("Mount Path", width=400)
        self.clients_tree.pack(fill="x", padx=10, pady=(0, 10))

    def setup_mounts_section(self, parent):
        """Sección de montajes NFS"""
        title = tk.Label(
            parent,
            text="NFS Mounts (Client Mode)",
            font=("Times New Roman", 11, BOLD),
            bg="#dce2ec",
            anchor="w"
        )
        title.pack(fill="x", padx=10, pady=(10, 5))

        # Frame de contenido
        mount_frame = tk.Frame(parent, bg="#ffffff", relief="raised", bd=1)
        mount_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Botones de montaje
        buttons_frame = tk.Frame(mount_frame, bg="#ffffff")
        buttons_frame.pack(fill="x", padx=10, pady=10)

        tk.Button(buttons_frame, text="Mount NFS", font=("Times New Roman", 9),
                 bg="#4CAF50", fg="white", width=12,
                 command=self.mount_nfs_dialog).pack(side="left", padx=5)

        tk.Button(buttons_frame, text="Unmount", font=("Times New Roman", 9),
                 bg="#f44336", fg="white", width=12,
                 command=self.unmount_nfs).pack(side="left", padx=5)

        tk.Button(buttons_frame, text="Add to fstab", font=("Times New Roman", 9),
                 bg="#FF9800", fg="white", width=12,
                 command=self.add_to_fstab).pack(side="left", padx=5)

        tk.Button(buttons_frame, text="Refresh", font=("Times New Roman", 9),
                 bg="#2196F3", fg="white", width=12,
                 command=self.refresh_mounts).pack(side="left", padx=5)

        # Treeview de montajes
        self.mounts_tree = ttk.Treeview(
            mount_frame,
            columns=("Server", "Remote Path", "Mount Point", "Type", "Options"),
            show="headings",
            height=5
        )
        self.mounts_tree.heading("Server", text="Server")
        self.mounts_tree.heading("Remote Path", text="Remote Path")
        self.mounts_tree.heading("Mount Point", text="Mount Point")
        self.mounts_tree.heading("Type", text="Type")
        self.mounts_tree.heading("Options", text="Options")
        self.mounts_tree.column("Server", width=120)
        self.mounts_tree.column("Remote Path", width=150)
        self.mounts_tree.column("Mount Point", width=150)
        self.mounts_tree.column("Type", width=60)
        self.mounts_tree.column("Options", width=200)
        self.mounts_tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def setup_backup_section(self, parent):
        """Sección de backups"""
        title = tk.Label(
            parent,
            text="Backup Management",
            font=("Times New Roman", 11, BOLD),
            bg="#dce2ec",
            anchor="w"
        )
        title.pack(fill="x", padx=10, pady=(10, 5))

        # Frame de contenido
        backup_frame = tk.Frame(parent, bg="#ffffff", relief="raised", bd=1)
        backup_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Botones de backup
        buttons_frame = tk.Frame(backup_frame, bg="#ffffff")
        buttons_frame.pack(fill="x", padx=10, pady=10)

        tk.Button(buttons_frame, text="Create Backup", font=("Times New Roman", 9),
                 bg="#4CAF50", fg="white", width=15,
                 command=self.create_backup).pack(side="left", padx=5)

        tk.Button(buttons_frame, text="Restore Backup", font=("Times New Roman", 9),
                 bg="#FF9800", fg="white", width=15,
                 command=self.restore_backup).pack(side="left", padx=5)

        tk.Button(buttons_frame, text="Delete Backup", font=("Times New Roman", 9),
                 bg="#f44336", fg="white", width=15,
                 command=self.delete_backup).pack(side="left", padx=5)

        tk.Button(buttons_frame, text="Refresh List", font=("Times New Roman", 9),
                 bg="#2196F3", fg="white", width=15,
                 command=self.refresh_backups).pack(side="left", padx=5)

        # Treeview de backups
        self.backups_tree = ttk.Treeview(
            backup_frame,
            columns=("Filename", "Timestamp", "Size", "Description"),
            show="headings",
            height=5
        )
        self.backups_tree.heading("Filename", text="Backup File")
        self.backups_tree.heading("Timestamp", text="Timestamp")
        self.backups_tree.heading("Size", text="Size")
        self.backups_tree.heading("Description", text="Description")
        self.backups_tree.column("Filename", width=250)
        self.backups_tree.column("Timestamp", width=150)
        self.backups_tree.column("Size", width=80)
        self.backups_tree.column("Description", width=250)
        self.backups_tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def setup_bottom_buttons(self, parent):
        """Botones inferiores"""
        button_frame = tk.Frame(parent, bg="#dce2ec")
        button_frame.pack(side="bottom", fill="x", pady=10)

        tk.Button(button_frame, text="Refresh All", font=("Times New Roman", 11, BOLD),
                 bg="#3a7ff6", fg="white", width=15, height=1,
                 command=self.refresh_all).pack(side="right", padx=5)

        tk.Button(button_frame, text="Close", font=("Times New Roman", 11, BOLD),
                 bg="#f44336", fg="white", width=15, height=1,
                 command=self.ventana.destroy).pack(side="right", padx=5)

    # ========== MÉTODOS DE SERVICIO ==========

    def service_start(self):
        """Inicia el servicio NFS"""
        try:
            ServiceManager.start()
            messagebox.showinfo("Éxito", "Servicio NFS iniciado correctamente")
            self.refresh_service_status()
        except ServiceError as e:
            messagebox.showerror("Error", f"No se pudo iniciar el servicio:\n{e}")

    def service_stop(self):
        """Detiene el servicio NFS"""
        try:
            confirm = messagebox.askyesno("Confirmar",
                                         "¿Está seguro de detener el servicio NFS?\n"
                                         "Esto desconectará a todos los clientes.")
            if confirm:
                ServiceManager.stop()
                messagebox.showinfo("Éxito", "Servicio NFS detenido correctamente")
                self.refresh_service_status()
        except ServiceError as e:
            messagebox.showerror("Error", f"No se pudo detener el servicio:\n{e}")

    def service_restart(self):
        """Reinicia el servicio NFS"""
        try:
            ServiceManager.restart()
            messagebox.showinfo("Éxito", "Servicio NFS reiniciado correctamente")
            self.refresh_service_status()
        except ServiceError as e:
            messagebox.showerror("Error", f"No se pudo reiniciar el servicio:\n{e}")

    def service_enable(self):
        """Habilita el servicio NFS al inicio"""
        try:
            ServiceManager.enable()
            messagebox.showinfo("Éxito", "Servicio NFS habilitado para inicio automático")
            self.refresh_service_status()
        except ServiceError as e:
            messagebox.showerror("Error", f"No se pudo habilitar el servicio:\n{e}")

    def service_disable(self):
        """Deshabilita el servicio NFS del inicio"""
        try:
            ServiceManager.disable()
            messagebox.showinfo("Éxito", "Servicio NFS deshabilitado del inicio automático")
            self.refresh_service_status()
        except ServiceError as e:
            messagebox.showerror("Error", f"No se pudo deshabilitar el servicio:\n{e}")

    def refresh_service_status(self):
        """Actualiza el estado del servicio"""
        try:
            status = ServiceManager.status()

            # Actualizar etiquetas
            if status["running"]:
                self.status_label.config(text="Running", fg="green")
            else:
                self.status_label.config(text="Stopped", fg="red")

            enabled_text = status["enabled"]
            if enabled_text == "enabled":
                self.enabled_label.config(text="Yes", fg="green")
            else:
                self.enabled_label.config(text="No", fg="red")

        except Exception as e:
            self.status_label.config(text="Error", fg="red")
            self.enabled_label.config(text="Error", fg="red")
            print(f"[ERROR] refresh_service_status: {e}")

    # ========== MÉTODOS DE EXPORTACIONES ==========

    def refresh_exports(self):
        """Actualiza la lista de exportaciones activas"""
        try:
            # Limpiar treeview
            for item in self.exports_tree.get_children():
                self.exports_tree.delete(item)

            # Obtener exportaciones
            exports = ServiceManager.get_exports_active()

            # Llenar treeview
            for export in exports:
                self.exports_tree.insert("", "end", values=(
                    export.get("path", ""),
                    export.get("client", ""),
                    export.get("options", "")
                ))

            if not exports:
                self.exports_tree.insert("", "end", values=(
                    "No hay exportaciones activas", "", ""
                ))

        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar las exportaciones:\n{e}")

    # ========== MÉTODOS DE CLIENTES ==========

    def refresh_clients(self):
        """Actualiza la lista de clientes conectados"""
        try:
            # Limpiar treeview
            for item in self.clients_tree.get_children():
                self.clients_tree.delete(item)

            # Obtener clientes
            clients = ServiceManager.get_connected_clients()

            # Llenar treeview
            for client in clients:
                self.clients_tree.insert("", "end", values=(
                    client.get("hostname", ""),
                    client.get("mount_path", "")
                ))

            if not clients:
                self.clients_tree.insert("", "end", values=(
                    "No hay clientes conectados", ""
                ))

        except Exception as e:
            print(f"[ERROR] refresh_clients: {e}")

    # ========== MÉTODOS DE MONTAJE ==========

    def mount_nfs_dialog(self):
        """Diálogo para montar un recurso NFS"""
        dialog = tk.Toplevel(self.ventana)
        dialog.title("Mount NFS Resource")
        dialog.geometry("500x350")
        dialog.config(bg="#dce2ec")
        utl.centrar_ventana(dialog, 500, 350)

        # Campos del formulario
        fields_frame = tk.Frame(dialog, bg="#dce2ec")
        fields_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Server
        tk.Label(fields_frame, text="NFS Server (IP or hostname):",
                font=("Times New Roman", 10), bg="#dce2ec").grid(row=0, column=0, sticky="w", pady=5)
        server_entry = ttk.Entry(fields_frame, font=("Times New Roman", 10), width=35)
        server_entry.grid(row=0, column=1, pady=5, padx=5)
        server_entry.insert(0, "192.168.1.1")  # Valor por defecto

        # Remote Path
        tk.Label(fields_frame, text="Remote Path:",
                font=("Times New Roman", 10), bg="#dce2ec").grid(row=1, column=0, sticky="w", pady=5)
        remote_entry = ttk.Entry(fields_frame, font=("Times New Roman", 10), width=35)
        remote_entry.grid(row=1, column=1, pady=5, padx=5)
        remote_entry.insert(0, "/srv/nfs/compartido")  # Valor por defecto

        # Mount Point
        tk.Label(fields_frame, text="Local Mount Point:",
                font=("Times New Roman", 10), bg="#dce2ec").grid(row=2, column=0, sticky="w", pady=5)
        mount_entry = ttk.Entry(fields_frame, font=("Times New Roman", 10), width=35)
        mount_entry.grid(row=2, column=1, pady=5, padx=5)
        mount_entry.insert(0, "/mnt/nfs/compartido")  # Valor por defecto

        # Options preset
        tk.Label(fields_frame, text="Mount Options Preset:",
                font=("Times New Roman", 10), bg="#dce2ec").grid(row=3, column=0, sticky="w", pady=5)

        options_var = tk.StringVar()
        presets = MountManager.get_mount_options_presets()
        options_combo = ttk.Combobox(fields_frame, textvariable=options_var,
                                     font=("Times New Roman", 10), width=32, state="readonly")
        options_combo['values'] = list(presets.keys())
        options_combo.current(0)  # Default
        options_combo.grid(row=3, column=1, pady=5, padx=5)

        # Custom options
        tk.Label(fields_frame, text="Custom Options (optional):",
                font=("Times New Roman", 10), bg="#dce2ec").grid(row=4, column=0, sticky="w", pady=5)
        custom_entry = ttk.Entry(fields_frame, font=("Times New Roman", 10), width=35)
        custom_entry.grid(row=4, column=1, pady=5, padx=5)

        # Test button
        def test_connection():
            server = server_entry.get().strip()
            remote = remote_entry.get().strip()
            if not server or not remote:
                messagebox.showwarning("Advertencia", "Ingrese servidor y ruta remota", parent=dialog)
                return

            messagebox.showinfo("Probando", f"Probando conexión a {server}...", parent=dialog)
            if MountManager.test_mount(server, remote):
                messagebox.showinfo("Éxito", "Recurso NFS accesible", parent=dialog)
            else:
                messagebox.showerror("Error", "No se puede acceder al recurso NFS", parent=dialog)

        tk.Button(fields_frame, text="Test Connection", font=("Times New Roman", 9),
                 bg="#9C27B0", fg="white", width=20,
                 command=test_connection).grid(row=5, column=0, columnspan=2, pady=10)

        # Botones de acción
        def do_mount():
            try:
                server = server_entry.get().strip()
                remote = remote_entry.get().strip()
                mount_point = mount_entry.get().strip()

                if not server or not remote or not mount_point:
                    messagebox.showwarning("Advertencia", "Complete todos los campos requeridos", parent=dialog)
                    return

                # Obtener opciones
                custom_opts = custom_entry.get().strip()
                if custom_opts:
                    options = custom_opts
                else:
                    preset_name = options_var.get()
                    options = presets.get(preset_name, "rw,sync")

                # Montar
                MountManager.mount_nfs(server, remote, mount_point, options)
                dialog.destroy()
                messagebox.showinfo("Éxito", f"Montado exitosamente en:\n{mount_point}")
                self.refresh_mounts()

            except MountError as e:
                messagebox.showerror("Error", f"No se pudo montar:\n{e}", parent=dialog)

        button_frame = tk.Frame(dialog, bg="#dce2ec")
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Mount", font=("Times New Roman", 10),
                 bg="#4CAF50", fg="white", width=12,
                 command=do_mount).pack(side="left", padx=5)

        tk.Button(button_frame, text="Cancel", font=("Times New Roman", 10),
                 bg="#f44336", fg="white", width=12,
                 command=dialog.destroy).pack(side="left", padx=5)

    def unmount_nfs(self):
        """Desmonta un recurso NFS seleccionado"""
        selection = self.mounts_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un montaje para desmontar")
            return

        item = self.mounts_tree.item(selection[0])
        mount_point = item["values"][2]

        confirm = messagebox.askyesno("Confirmar",
                                     f"¿Desmontar {mount_point}?")
        if confirm:
            try:
                MountManager.unmount_nfs(mount_point)
                messagebox.showinfo("Éxito", "Desmontado correctamente")
                self.refresh_mounts()
            except MountError as e:
                # Intentar forzar desmontaje
                retry = messagebox.askyesno("Error",
                                           f"No se pudo desmontar:\n{e}\n\n"
                                           f"¿Intentar forzar desmontaje?")
                if retry:
                    try:
                        MountManager.unmount_nfs(mount_point, force=True)
                        messagebox.showinfo("Éxito", "Desmontado forzosamente")
                        self.refresh_mounts()
                    except MountError as e2:
                        messagebox.showerror("Error", f"No se pudo desmontar:\n{e2}")

    def add_to_fstab(self):
        """Añade un montaje seleccionado a /etc/fstab"""
        selection = self.mounts_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un montaje para añadir a fstab")
            return

        item = self.mounts_tree.item(selection[0])
        server = item["values"][0]
        remote_path = item["values"][1]
        mount_point = item["values"][2]
        options = item["values"][4]

        # Diálogo de confirmación con opciones
        dialog = tk.Toplevel(self.ventana)
        dialog.title("Add to fstab")
        dialog.geometry("450x200")
        dialog.config(bg="#dce2ec")
        utl.centrar_ventana(dialog, 450, 200)

        tk.Label(dialog, text="Se añadirá la siguiente entrada a /etc/fstab:",
                font=("Times New Roman", 10, BOLD), bg="#dce2ec").pack(pady=10)

        info_text = f"{server}:{remote_path}\n{mount_point}\nnfs\n{options},_netdev 0 0"
        tk.Label(dialog, text=info_text, font=("Times New Roman", 9),
                bg="#ffffff", justify="left", relief="sunken", padx=10, pady=10).pack(padx=20)

        tk.Label(dialog, text="Se creará un backup de fstab automáticamente",
                font=("Times New Roman", 9), bg="#dce2ec", fg="green").pack(pady=5)

        def do_add():
            try:
                opts = f"{options},_netdev" if options else "defaults,_netdev"
                MountManager.add_to_fstab(server, remote_path, mount_point, opts)
                dialog.destroy()
                messagebox.showinfo("Éxito", "Añadido a /etc/fstab correctamente")
            except MountError as e:
                messagebox.showerror("Error", f"No se pudo añadir a fstab:\n{e}", parent=dialog)

        button_frame = tk.Frame(dialog, bg="#dce2ec")
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Add", font=("Times New Roman", 10),
                 bg="#4CAF50", fg="white", width=12,
                 command=do_add).pack(side="left", padx=5)

        tk.Button(button_frame, text="Cancel", font=("Times New Roman", 10),
                 bg="#f44336", fg="white", width=12,
                 command=dialog.destroy).pack(side="left", padx=5)

    def refresh_mounts(self):
        """Actualiza la lista de montajes NFS"""
        try:
            # Limpiar treeview
            for item in self.mounts_tree.get_children():
                self.mounts_tree.delete(item)

            # Obtener montajes
            mounts = MountManager.get_mounted_nfs()

            # Llenar treeview
            for mount in mounts:
                self.mounts_tree.insert("", "end", values=(
                    mount.get("server", ""),
                    mount.get("remote_path", ""),
                    mount.get("mount_point", ""),
                    mount.get("type", ""),
                    mount.get("options", "")
                ))

            if not mounts:
                self.mounts_tree.insert("", "end", values=(
                    "No hay montajes NFS activos", "", "", "", ""
                ))

        except Exception as e:
            print(f"[ERROR] refresh_mounts: {e}")

    # ========== MÉTODOS DE BACKUP ==========

    def create_backup(self):
        """Crea un nuevo backup"""
        # Ventana para descripción
        dialog = tk.Toplevel(self.ventana)
        dialog.title("Create Backup")
        dialog.geometry("400x150")
        dialog.config(bg="#dce2ec")
        utl.centrar_ventana(dialog, 400, 150)

        tk.Label(dialog, text="Backup Description (optional):",
                font=("Times New Roman", 10), bg="#dce2ec").pack(pady=10)

        desc_entry = ttk.Entry(dialog, font=("Times New Roman", 10), width=40)
        desc_entry.pack(pady=5)

        def do_backup():
            try:
                description = desc_entry.get().strip()
                filename = BackupManager.create_backup(description)
                dialog.destroy()
                messagebox.showinfo("Éxito", f"Backup creado:\n{filename}")
                self.refresh_backups()
            except BackupError as e:
                messagebox.showerror("Error", f"No se pudo crear el backup:\n{e}")

        button_frame = tk.Frame(dialog, bg="#dce2ec")
        button_frame.pack(pady=15)

        tk.Button(button_frame, text="Create", font=("Times New Roman", 10),
                 bg="#4CAF50", fg="white", width=10,
                 command=do_backup).pack(side="left", padx=5)

        tk.Button(button_frame, text="Cancel", font=("Times New Roman", 10),
                 bg="#f44336", fg="white", width=10,
                 command=dialog.destroy).pack(side="left", padx=5)

    def restore_backup(self):
        """Restaura un backup seleccionado"""
        selection = self.backups_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un backup para restaurar")
            return

        item = self.backups_tree.item(selection[0])
        filename = item["values"][0]

        confirm = messagebox.askyesno("Confirmar Restauración",
                                     f"¿Está seguro de restaurar el backup?\n\n"
                                     f"Archivo: {filename}\n\n"
                                     f"Se creará un backup automático del estado actual.")
        if confirm:
            try:
                BackupManager.restore_backup(filename)
                messagebox.showinfo("Éxito", "Backup restaurado correctamente")
                self.refresh_all()
            except BackupError as e:
                messagebox.showerror("Error", f"No se pudo restaurar el backup:\n{e}")

    def delete_backup(self):
        """Elimina un backup seleccionado"""
        selection = self.backups_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un backup para eliminar")
            return

        item = self.backups_tree.item(selection[0])
        filename = item["values"][0]

        confirm = messagebox.askyesno("Confirmar Eliminación",
                                     f"¿Está seguro de eliminar el backup?\n\n{filename}")
        if confirm:
            try:
                BackupManager.delete_backup(filename)
                messagebox.showinfo("Éxito", "Backup eliminado correctamente")
                self.refresh_backups()
            except BackupError as e:
                messagebox.showerror("Error", f"No se pudo eliminar el backup:\n{e}")

    def refresh_backups(self):
        """Actualiza la lista de backups"""
        try:
            # Limpiar treeview
            for item in self.backups_tree.get_children():
                self.backups_tree.delete(item)

            # Obtener backups
            backups = BackupManager.list_backups()

            # Llenar treeview
            for backup in backups:
                self.backups_tree.insert("", "end", values=(
                    backup.get("filename", ""),
                    backup.get("timestamp", ""),
                    backup.get("size", ""),
                    backup.get("description", "")
                ))

            if not backups:
                self.backups_tree.insert("", "end", values=(
                    "No hay backups disponibles", "", "", ""
                ))

        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los backups:\n{e}")

    # ========== MÉTODO GENERAL ==========

    def refresh_all(self):
        """Actualiza toda la información"""
        self.refresh_service_status()
        self.refresh_exports()
        self.refresh_clients()
        self.refresh_mounts()  # NUEVA
        self.refresh_backups()


# Para pruebas independientes
if __name__ == "__main__":
    ClientManagerPanel()
