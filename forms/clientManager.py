import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from tkinter.font import BOLD
import util.generic as utl
from util.service_manager import ServiceManager, ServiceError
from util.backup_manager import BackupManager, BackupError

class ClientManagerPanel:
    """Panel de gestión de clientes NFS y servicios"""

    def __init__(self, parent=None):
        if parent:
            self.ventana = tk.Toplevel(parent)
        else:
            self.ventana = tk.Tk()

        self.ventana.title("NFS Client & Service Manager")
        self.ventana.geometry("1000x700")
        self.ventana.config(bg="#fcfcfc")
        self.ventana.resizable(True, True)
        utl.centrar_ventana(self.ventana, 1000, 700)

        # Frame principal
        self.setup_ui()

        # Cargar datos iniciales
        self.refresh_all()

        if not parent:
            self.ventana.mainloop()

    def setup_ui(self):
        """Configura la interfaz de usuario"""
        # Fondo
        bg_label = tk.Label(self.ventana, bg="#dce2ec")
        bg_label.place(x=0, y=0, relheight=1, relwidth=1)

        # Frame principal con scroll
        main_frame = tk.Frame(self.ventana, bg="#dce2ec")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # ======== SECCIÓN 1: ESTADO DEL SERVICIO ========
        self.setup_service_section(main_frame)

        # ======== SECCIÓN 2: EXPORTACIONES ACTIVAS ========
        self.setup_exports_section(main_frame)

        # ======== SECCIÓN 3: CLIENTES CONECTADOS ========
        self.setup_clients_section(main_frame)

        # ======== SECCIÓN 4: BACKUPS ========
        self.setup_backup_section(main_frame)

        # ======== BOTONES INFERIORES ========
        self.setup_bottom_buttons(main_frame)

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
        self.refresh_backups()


# Para pruebas independientes
if __name__ == "__main__":
    ClientManagerPanel()

