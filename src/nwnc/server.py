
import json
import socket
import threading
from typing import Any, Callable


DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 5050
BUFFER_SIZE = 4096


class ChatServer:
    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        on_log: Callable[[str], None] | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.on_log = on_log

        self.server_socket: socket.socket | None = None
        self.clients: dict[socket.socket, tuple[str, int]] = {}
        self.clients_lock = threading.Lock()
        self.running = threading.Event()

    def _log(self, text: str) -> None:
        print(text)
        if self.on_log is not None:
            try:
                self.on_log(text)
            except Exception:
                pass

    def start(self) -> None:
        if self.running.is_set():
            self._log("[INFO] Server is already running.")
            return

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            server.bind((self.host, self.port))
            server.listen()
            server.settimeout(1.0)
        except OSError:
            server.close()
            raise

        self.server_socket = server
        self.running.set()

        self._log("[INFO] NWNC server started.")
        self._log(f"[INFO] Listening on {self.host}:{self.port}")
        self._log("[INFO] Waiting for clients...")

        threading.Thread(
            target=self._accept_clients,
            name="NWNC-Accept",
            daemon=True,
        ).start()

    def _accept_clients(self) -> None:
        while self.running.is_set():
            server = self.server_socket
            if server is None:
                break

            try:
                client_socket, address = server.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            with self.clients_lock:
                self.clients[client_socket] = address

            self._log(f"[CONNECTED] {address[0]}:{address[1]}")

            self._send_to_client(
                client_socket,
                {
                    "type": "system",
                    "text": "Connected to NWNC server.",
                    "sender": "NWNC Server",
                },
            )

            threading.Thread(
                target=self._handle_client,
                args=(client_socket, address),
                name=f"NWNC-Client-{address[0]}",
                daemon=True,
            ).start()

    def _handle_client(
        self,
        client_socket: socket.socket,
        address: tuple[str, int],
    ) -> None:
        buffer = b""

        try:
            while self.running.is_set():
                data = client_socket.recv(BUFFER_SIZE)
                if not data:
                    break

                buffer += data

                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if not line.strip():
                        continue

                    try:
                        message: Any = json.loads(line.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        self._send_to_client(
                            client_socket,
                            {
                                "type": "error",
                                "text": "Invalid message format.",
                            },
                        )
                        continue

                    if not isinstance(message, dict):
                        continue
                    if message.get("type") != "message":
                        continue

                    text = message.get("text")
                    sender = message.get("sender", "Guest")

                    if not isinstance(text, str) or not text.strip():
                        continue
                    if not isinstance(sender, str):
                        sender = "Guest"

                    outgoing = {
                        "type": "message",
                        "sender": sender[:64],
                        "text": text[:4000],
                        "sender_ip": address[0],
                    }

                    self._log(
                        f"[MESSAGE] {sender[:64]} "
                        f"({address[0]}): {text[:200]}"
                    )
                    self._broadcast(outgoing)

        except OSError as exc:
            if self.running.is_set():
                self._log(f"[CLIENT ERROR] {address}: {exc}")
        finally:
            with self.clients_lock:
                was_connected = self.clients.pop(client_socket, None) is not None

            try:
                client_socket.close()
            except OSError:
                pass

            if was_connected:
                self._log(f"[DISCONNECTED] {address[0]}:{address[1]}")

    def _send_to_client(
        self,
        client_socket: socket.socket,
        message: dict[str, Any],
    ) -> bool:
        payload = (
            json.dumps(message, ensure_ascii=False) + "\n"
        ).encode("utf-8")

        try:
            client_socket.sendall(payload)
            return True
        except OSError:
            return False

    def _broadcast(self, message: dict[str, Any]) -> None:
        with self.clients_lock:
            recipients = list(self.clients.keys())

        for client_socket in recipients:
            if not self._send_to_client(client_socket, message):
                with self.clients_lock:
                    address = self.clients.pop(client_socket, None)

                try:
                    client_socket.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass

                try:
                    client_socket.close()
                except OSError:
                    pass

                if address is not None:
                    self._log(
                        f"[WARN] Lost connection to "
                        f"{address[0]}:{address[1]}"
                    )

    def stop(self) -> None:
        if not self.running.is_set() and self.server_socket is None:
            return

        self.running.clear()

        server = self.server_socket
        self.server_socket = None

        if server is not None:
            try:
                server.close()
            except OSError:
                pass

        with self.clients_lock:
            clients = list(self.clients.keys())
            self.clients.clear()

        for client_socket in clients:
            try:
                client_socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                client_socket.close()
            except OSError:
                pass

        self._log("[INFO] NWNC server stopped.")


def main() -> None:
    server = ChatServer()

    try:
        server.start()
        threading.Event().wait()
    except KeyboardInterrupt:
        print("\nStopping NWNC server...")
    except OSError as exc:
        print(f"[SERVER ERROR] Could not start server: {exc}")
    finally:
        server.stop()


if __name__ == "__main__":
    main()
