
import json
import socket
import threading
from typing import Any, Callable


DEFAULT_PORT = 5050
BUFFER_SIZE = 4096
MAX_MESSAGE_LENGTH = 4000


class ChatClient:
    def __init__(
        self,
        on_message: Callable[[dict[str, Any]], None] | None = None,
        on_status: Callable[[str], None] | None = None,
    ) -> None:
        self.on_message = on_message
        self.on_status = on_status

        self._socket: socket.socket | None = None
        self._send_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._connected = False
        self._receiver_thread: threading.Thread | None = None

    @property
    def connected(self) -> bool:
        with self._state_lock:
            return self._connected

    def _notify_status(self, status: str) -> None:
        if self.on_status is not None:
            try:
                self.on_status(status)
            except Exception as exc:
                print(f"[NWNC status callback error] {exc}")

    def _notify_message(self, message: dict[str, Any]) -> None:
        if self.on_message is not None:
            try:
                self.on_message(message)
            except Exception as exc:
                print(f"[NWNC message callback error] {exc}")

    def connect(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        timeout: float = 5.0,
    ) -> None:
        if self.connected:
            raise RuntimeError("Client is already connected.")

        host = host.strip()

        if not host:
            raise ValueError("Server IP address cannot be empty.")

        if not 1 <= port <= 65535:
            raise ValueError("Port must be between 1 and 65535.")

        client_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        )
        client_socket.settimeout(timeout)

        try:
            client_socket.connect((host, port))
            client_socket.settimeout(None)
        except OSError:
            client_socket.close()
            raise

        with self._state_lock:
            if self._connected:
                client_socket.close()
                raise RuntimeError("Client is already connected.")

            self._socket = client_socket
            self._connected = True

        self._notify_status(f"Connected to {host}:{port}")

        self._receiver_thread = threading.Thread(
            target=self._receive_loop,
            name="NWNC-Receiver",
            daemon=True,
        )
        self._receiver_thread.start()

    def send_message(self, text: str, sender: str = "Guest") -> None:
        text = text.strip()

        if not text:
            raise ValueError("Message cannot be empty.")

        if len(text) > MAX_MESSAGE_LENGTH:
            raise ValueError(
                f"Message cannot exceed {MAX_MESSAGE_LENGTH} characters."
            )

        if not isinstance(sender, str):
            sender = "Guest"

        message = {
            "type": "message",
            "sender": sender.strip()[:64] or "Guest",
            "text": text,
        }

        payload = (
            json.dumps(message, ensure_ascii=False) + "\n"
        ).encode("utf-8")

        with self._send_lock:
            with self._state_lock:
                client_socket = self._socket
                is_connected = self._connected

            if not is_connected or client_socket is None:
                raise ConnectionError("Not connected to the server.")

            try:
                client_socket.sendall(payload)
            except OSError as exc:
                self._mark_disconnected()
                raise ConnectionError(
                    f"Failed to send message: {exc}"
                ) from exc

    def _receive_loop(self) -> None:
        buffer = b""

        while True:
            with self._state_lock:
                client_socket = self._socket
                is_connected = self._connected

            if not is_connected or client_socket is None:
                break

            try:
                data = client_socket.recv(BUFFER_SIZE)
            except OSError as exc:
                if self.connected:
                    self._notify_status(f"Connection error: {exc}")
                break

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
                    self._notify_status("Received an invalid server message.")
                    continue

                if isinstance(message, dict):
                    self._notify_message(message)

        was_connected = self.connected
        self._mark_disconnected()

        if was_connected:
            self._notify_status("Disconnected from server.")

    def _mark_disconnected(self) -> None:
        with self._state_lock:
            self._connected = False
            client_socket = self._socket
            self._socket = None

        if client_socket is not None:
            try:
                client_socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

            try:
                client_socket.close()
            except OSError:
                pass

    def disconnect(self) -> None:
        was_connected = self.connected
        self._mark_disconnected()

        if was_connected:
            self._notify_status("Disconnected from server.")

    def __enter__(self) -> "ChatClient":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.disconnect()


def main() -> None:
    server_ip = input("Enter server IP address: ").strip()
    username = input("Enter your username: ").strip() or "Guest"

    client = ChatClient(
        on_message=lambda msg: print(
            f"\n[{msg.get('sender', 'System')}] "
            f"{msg.get('text', '')}"
        ),
        on_status=print,
    )

    try:
        client.connect(server_ip)
        print("Connected. Type a message; use /quit to exit.")

        while client.connected:
            try:
                text = input("> ")
            except EOFError:
                break

            if text.strip().lower() == "/quit":
                break

            if not text.strip():
                continue

            try:
                client.send_message(text, username)
            except (ConnectionError, ValueError) as exc:
                print(f"Send failed: {exc}")

    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Could not connect: {exc}")
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
