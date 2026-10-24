
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path

import customtkinter as ctk

from .core import get_app_info
from .client import ChatClient
from .server import ChatServer


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DEFAULT_PORT = 5050


class NWNCWindow:
    def __init__(self, root):
        self.root = root
        self.app_info = get_app_info()

        self.root.title(f"{self.app_info['name']} - Network Chat")
        self.root.geometry("1080x720")
        self.root.minsize(850, 600)
        self.root.configure(fg_color="#101319")

        self.client = None
        self.server = None
        self.username = "Guest"

        self.connecting = False
        self.server_starting = False
        self.server_stopping = False
        self.closing = False

        self.create_layout()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.log("NWNC started.")

    def create_layout(self):
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(
            self.root,
            width=255,
            corner_radius=0,
            fg_color="#171B23",
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        ctk.CTkLabel(
            self.sidebar,
            text="NWNC",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color="#62AEFF",
        ).pack(anchor="w", padx=22, pady=(25, 0))

        ctk.CTkLabel(
            self.sidebar,
            text="NETWORK CHAT",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#7F899B",
        ).pack(anchor="w", padx=25, pady=(0, 26))

        ctk.CTkLabel(
            self.sidebar,
            text="SERVER",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#8791A3",
        ).pack(anchor="w", padx=20, pady=(0, 8))

        self.server_status = ctk.CTkLabel(
            self.sidebar,
            text="●  Server stopped",
            text_color="#E8B45E",
            font=ctk.CTkFont(size=12),
        )
        self.server_status.pack(anchor="w", padx=20, pady=(0, 10))

        # One button toggles between Start Server and Stop Server.
        self.server_button = ctk.CTkButton(
            self.sidebar,
            text="Start Server",
            height=42,
            corner_radius=9,
            fg_color="#21865A",
            hover_color="#176B46",
            command=self.toggle_server,
        )
        self.server_button.pack(fill="x", padx=20, pady=(0, 24))

        ctk.CTkFrame(
            self.sidebar,
            height=1,
            fg_color="#2B303B",
        ).pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(
            self.sidebar,
            text="CONNECTION",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#8791A3",
        ).pack(anchor="w", padx=20, pady=(0, 8))

        ctk.CTkLabel(
            self.sidebar,
            text="Server IP",
            font=ctk.CTkFont(size=12),
            text_color="#C5CBD6",
        ).pack(anchor="w", padx=20, pady=(3, 5))

        self.server_entry = ctk.CTkEntry(
            self.sidebar,
            height=38,
            corner_radius=8,
            placeholder_text="127.0.0.1",
            fg_color="#202530",
            border_color="#343B49",
        )
        self.server_entry.pack(fill="x", padx=20)
        self.server_entry.insert(0, "127.0.0.1")

        ctk.CTkLabel(
            self.sidebar,
            text="Username",
            font=ctk.CTkFont(size=12),
            text_color="#C5CBD6",
        ).pack(anchor="w", padx=20, pady=(14, 5))

        self.username_entry = ctk.CTkEntry(
            self.sidebar,
            height=38,
            corner_radius=8,
            placeholder_text="Your username",
            fg_color="#202530",
            border_color="#343B49",
        )
        self.username_entry.pack(fill="x", padx=20)
        self.username_entry.insert(0, "Guest")

        self.connect_button = ctk.CTkButton(
            self.sidebar,
            text="Connect to Server",
            height=42,
            corner_radius=9,
            fg_color="#2878D0",
            hover_color="#1F65B3",
            command=self.toggle_connection,
        )
        self.connect_button.pack(fill="x", padx=20, pady=(17, 10))

        self.connection_status = ctk.CTkLabel(
            self.sidebar,
            text="Not connected",
            text_color="#E8B45E",
            font=ctk.CTkFont(size=12),
            wraplength=210,
        )
        self.connection_status.pack(anchor="w", padx=20)

        ctk.CTkLabel(
            self.sidebar,
            text=f"TCP PORT  •  {DEFAULT_PORT}",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#667185",
        ).pack(side="bottom", anchor="w", padx=22, pady=20)

        # Main panel
        self.main = ctk.CTkFrame(
            self.root,
            fg_color="#101319",
            corner_radius=0,
        )
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(
            self.main,
            fg_color="#171B23",
            corner_radius=0,
            height=76,
        )
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_propagate(False)

        ctk.CTkLabel(
            header,
            text="Network Chat",
            font=ctk.CTkFont(size=21, weight="bold"),
            text_color="#F1F4FA",
        ).grid(row=0, column=0, sticky="sw", padx=23, pady=(12, 0))

        ctk.CTkLabel(
            header,
            text="Message users connected to your NWNC server",
            font=ctk.CTkFont(size=11),
            text_color="#8A94A6",
        ).grid(row=1, column=0, sticky="nw", padx=24, pady=(0, 11))

        # Tabs: chat and logs are separate.
        self.tabs = ctk.CTkTabview(
            self.main,
            fg_color="#101319",
            segmented_button_fg_color="#1B202A",
            segmented_button_selected_color="#2878D0",
            segmented_button_selected_hover_color="#1F65B3",
            segmented_button_unselected_color="#1B202A",
            segmented_button_unselected_hover_color="#292F3B",
            text_color="#E5EAF3",
        )
        self.tabs.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=16,
            pady=(12, 6),
        )

        self.tabs.add("Chat")
        self.tabs.add("Server Logs")

        # Chat tab
        chat_tab = self.tabs.tab("Chat")
        chat_tab.grid_columnconfigure(0, weight=1)
        chat_tab.grid_rowconfigure(0, weight=1)

        self.messages = ctk.CTkScrollableFrame(
            chat_tab,
            fg_color="#101319",
            corner_radius=8,
        )
        self.messages.grid(row=0, column=0, sticky="nsew")
        self.messages.grid_columnconfigure(0, weight=1)

        self.add_message(
            "NWNC",
            "Welcome! Start a server or connect to an existing one.",
            incoming=True,
        )

        self.input_area = ctk.CTkFrame(
            chat_tab,
            fg_color="#191E27",
            corner_radius=10,
        )
        self.input_area.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(10, 0),
        )
        self.input_area.grid_columnconfigure(0, weight=1)

        self.message_entry = ctk.CTkEntry(
            self.input_area,
            height=44,
            corner_radius=8,
            placeholder_text="Write a message...",
            fg_color="#222834",
            border_color="#343B49",
        )
        self.message_entry.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(10, 8),
            pady=10,
        )
        self.message_entry.bind("<Return>", self.send_message)

        self.send_button = ctk.CTkButton(
            self.input_area,
            text="Send",
            width=85,
            height=44,
            corner_radius=8,
            command=self.send_message,
        )
        self.send_button.grid(row=0, column=1, padx=(0, 10), pady=10)

        # Server Logs tab
        logs_tab = self.tabs.tab("Server Logs")
        logs_tab.grid_columnconfigure(0, weight=1)
        logs_tab.grid_rowconfigure(1, weight=1)

        log_header = ctk.CTkFrame(
            logs_tab,
            fg_color="transparent",
        )
        log_header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        log_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            log_header,
            text="Server activity",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#EDF1F8",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            log_header,
            text="Clear logs",
            width=85,
            height=30,
            fg_color="#292F3B",
            hover_color="#373F4D",
            command=self.clear_logs,
        ).grid(row=0, column=1, sticky="e")

        self.log_box = ctk.CTkTextbox(
            logs_tab,
            corner_radius=8,
            fg_color="#0D1117",
            text_color="#B9C6D8",
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word",
        )
        self.log_box.grid(row=1, column=0, sticky="nsew")
        self.log_box.configure(state="disabled")

    # ---------------- LOGGING ----------------

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}\n"

        if self.closing:
            return

        try:
            self.root.after(0, lambda value=line: self._append_log(value))
        except (RuntimeError, tk.TclError):
            pass

    def _append_log(self, line):
        if self.closing:
            return

        self.log_box.configure(state="normal")
        self.log_box.insert("end", line)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def clear_logs(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    # ---------------- SERVER ----------------

    def toggle_server(self):
        if self.closing or self.server_starting or self.server_stopping:
            return

        if self.server is not None:
            self.stop_server()
        else:
            self.start_server()

    def start_server(self):
        self.server_starting = True
        self.server_button.configure(
            text="Starting...",
            state="disabled",
            fg_color="#555D6B",
        )
        self.server_status.configure(
            text="●  Starting server...",
            text_color="#E8B45E",
        )
        self.log("Starting server on port 5050...")

        threading.Thread(
            target=self._start_server_worker,
            daemon=True,
        ).start()

    def _start_server_worker(self):
        server = ChatServer(
            host="0.0.0.0",
            port=DEFAULT_PORT,
            on_log=self.log,
        )

        try:
            server.start()
        except OSError as exc:
            try:
                server.stop()
            except Exception:
                pass
            self._safe_after(
                lambda error=str(exc): self._server_start_failed(error)
            )
            return

        self._safe_after(lambda: self._server_started(server))

    def _server_started(self, server):
        if self.closing:
            threading.Thread(target=server.stop, daemon=True).start()
            return

        self.server = server
        self.server_starting = False

        self.server_button.configure(
            text="Stop Server",
            state="normal",
            fg_color="#B83E4B",
            hover_color="#92313B",
        )
        self.server_status.configure(
            text="●  Server running",
            text_color="#4BD49B",
        )
        self.log("Server is ready. Local address: 127.0.0.1:5050")

    def _server_start_failed(self, error):
        if self.closing:
            return

        self.server_starting = False
        self.server_button.configure(
            text="Start Server",
            state="normal",
            fg_color="#21865A",
            hover_color="#176B46",
        )
        self.server_status.configure(
            text="●  Server stopped",
            text_color="#E8B45E",
        )
        self.log(f"[ERROR] Could not start server: {error}")

    def stop_server(self):
        if self.server is None:
            return

        self.server_stopping = True
        self.server_button.configure(
            text="Stopping...",
            state="disabled",
            fg_color="#555D6B",
        )
        self.server_status.configure(
            text="●  Stopping server...",
            text_color="#E8B45E",
        )
        self.log("Stopping server...")

        server = self.server
        self.server = None

        client = self.client
        self.client = None
        self.connecting = False

        if client is not None:
            try:
                client.disconnect()
            except Exception:
                pass

        threading.Thread(
            target=self._stop_server_worker,
            args=(server,),
            daemon=True,
        ).start()

    def _stop_server_worker(self, server):
        try:
            server.stop()
        finally:
            self._safe_after(self._server_stopped)

    def _server_stopped(self):
        if self.closing:
            return

        self.server_stopping = False
        self.server_button.configure(
            text="Start Server",
            state="normal",
            fg_color="#21865A",
            hover_color="#176B46",
        )
        self.server_status.configure(
            text="●  Server stopped",
            text_color="#E8B45E",
        )
        self.connect_button.configure(
            text="Connect to Server",
            state="normal",
        )
        self.set_connection_fields_state(True)
        self.connection_status.configure(
            text="Not connected",
            text_color="#E8B45E",
        )
        self.log("Server stopped.")

    # ---------------- CLIENT CONNECTION ----------------

    def toggle_connection(self):
        if self.closing or self.connecting or self.server_stopping:
            return

        if self.client is not None and self.client.connected:
            client = self.client
            self.client = None

            try:
                client.disconnect()
            except Exception:
                pass

            self.set_connection_fields_state(True)
            self.connect_button.configure(
                text="Connect to Server",
                state="normal",
            )
            self.connection_status.configure(
                text="Not connected",
                text_color="#E8B45E",
            )
            self.log("Disconnected from server.")
            return

        host = self.server_entry.get().strip()
        username = self.username_entry.get().strip() or "Guest"

        if not host:
            self.connection_status.configure(
                text="Enter a server IP",
                text_color="#FF7373",
            )
            return

        self.username = username
        if not self.username_entry.get().strip():
            self.username_entry.delete(0, "end")
            self.username_entry.insert(0, username)

        self.connecting = True
        self.connect_button.configure(
            text="Connecting...",
            state="disabled",
        )
        self.connection_status.configure(
            text="Connecting...",
            text_color="#E8B45E",
        )
        self.log(f"Connecting to {host}:{DEFAULT_PORT} as {username}...")

        client = ChatClient(
            on_message=self.network_message_callback,
            on_status=self.network_status_callback,
        )
        self.client = client

        threading.Thread(
            target=self._connect_worker,
            args=(client, host),
            daemon=True,
        ).start()

    def _connect_worker(self, client, host):
        try:
            client.connect(host)
            self._safe_after(lambda: self._connection_succeeded(client))
        except Exception as exc:
            error = str(exc)
            self._safe_after(
                lambda message=error: self._connection_failed(client, message)
            )

    def _connection_succeeded(self, client):
        if self.closing or client is not self.client:
            return

        self.connecting = False

        if client.connected:
            self.set_connection_fields_state(False)
            self.connect_button.configure(
                text="Disconnect",
                state="normal",
            )
            self.connection_status.configure(
                text="Connected",
                text_color="#4BD49B",
            )
            self.log(f"Connected to server as {self.username}.")
        else:
            self._reset_connection_ui()

    def _connection_failed(self, client, error):
        if self.closing or client is not self.client:
            return

        self.client = None
        self.connecting = False

        try:
            client.disconnect()
        except Exception:
            pass

        self._reset_connection_ui()
        self.connection_status.configure(
            text="Connection failed",
            text_color="#FF7373",
        )
        self.log(f"[ERROR] Connection failed: {error}")

    def _reset_connection_ui(self):
        self.connecting = False
        self.set_connection_fields_state(True)
        self.connect_button.configure(
            text="Connect to Server",
            state="normal",
        )

    def set_connection_fields_state(self, enabled):
        state = "normal" if enabled else "disabled"
        self.server_entry.configure(state=state)
        self.username_entry.configure(state=state)

    # ---------------- MESSAGES ----------------

    def network_message_callback(self, message):
        self._safe_after(lambda value=message: self.handle_network_message(value))

    def handle_network_message(self, message):
        if self.closing or not isinstance(message, dict):
            return

        kind = message.get("type", "message")
        sender = message.get("sender", "Guest")
        text = message.get("text", "")

        if not isinstance(text, str) or not text:
            return

        if kind == "system":
            self.add_message(sender or "NWNC", text, incoming=True)
        elif kind == "message":
            self.add_message(
                sender,
                text,
                incoming=(sender != self.username),
            )
        elif kind == "error":
            self.log(f"[CLIENT ERROR] {text}")

    def network_status_callback(self, status):
        self._safe_after(lambda value=status: self.handle_network_status(value))

    def handle_network_status(self, status):
        if self.closing:
            return

        text = str(status)
        lowered = text.lower()

        if "disconnected" in lowered or "connection closed" in lowered:
            self.client = None
            self._reset_connection_ui()
            self.connection_status.configure(
                text="Not connected",
                text_color="#E8B45E",
            )
            self.log(f"Connection status: {text}")
        elif "error" in lowered or "failed" in lowered:
            self.connection_status.configure(
                text=text,
                text_color="#FF7373",
            )
            self.log(f"[ERROR] {text}")

    def add_message(self, sender, text, incoming=True):
        if self.closing:
            return

        row = ctk.CTkFrame(self.messages, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=6)

        bubble = ctk.CTkFrame(
            row,
            fg_color="#202631" if incoming else "#1C4772",
            corner_radius=12,
        )
        bubble.pack(
            anchor="w" if incoming else "e",
            padx=(0, 40) if incoming else (40, 0),
        )

        ctk.CTkLabel(
            bubble,
            text=str(sender),
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#75B7FF" if incoming else "#B9DCFF",
        ).pack(anchor="w", padx=12, pady=(8, 2))

        ctk.CTkLabel(
            bubble,
            text=str(text),
            font=ctk.CTkFont(size=13),
            text_color="#F1F4FA",
            wraplength=540,
            justify="left",
        ).pack(anchor="w", padx=12, pady=(0, 9))

        try:
            self.messages._parent_canvas.yview_moveto(1.0)
        except (AttributeError, tk.TclError):
            pass

    def send_message(self, event=None):
        if self.closing:
            return "break"

        text = self.message_entry.get().strip()
        if not text:
            return "break"

        client = self.client
        if client is None or not client.connected:
            self.connection_status.configure(
                text="Connect to a server first",
                text_color="#FF7373",
            )
            return "break"

        try:
            client.send_message(text, sender=self.username)
            self.message_entry.delete(0, "end")
        except Exception as exc:
            self.log(f"[ERROR] Could not send message: {exc}")

        return "break"

    # ---------------- HELPERS ----------------

    def _safe_after(self, callback):
        if self.closing:
            return

        try:
            self.root.after(0, callback)
        except (RuntimeError, tk.TclError):
            pass

    def on_close(self):
        if self.closing:
            return

        self.closing = True

        client = self.client
        server = self.server

        self.client = None
        self.server = None

        if client is not None:
            try:
                client.disconnect()
            except Exception:
                pass

        if server is not None:
            threading.Thread(
                target=server.stop,
                daemon=True,
            ).start()

        self.root.destroy()


def main():
    root = ctk.CTk()

    icon_path = Path(__file__).with_name("nwnc.ico")
    if icon_path.exists():
        try:
            root.iconbitmap(default=str(icon_path))
        except Exception:
            pass

    NWNCWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
