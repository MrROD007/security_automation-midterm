"""A local TCP server for the networking midterm."""

import socket
from datetime import datetime

HOST = "127.0.0.1"
PORT = 5000
MAX_MESSAGE_BYTES = 4096


def log(message):
    """Display a message with a timestamp."""
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    print(f"[{timestamp}] {message}", flush=True)


def receive_message(connection):
    """Read a message until its ending newline."""
    data = bytearray()

    while True:
        chunk = connection.recv(1)

        # An empty result means the client closed its connection.
        if not chunk:
            if data:
                raise ConnectionError("Connection ended during a message.")
            return None

        if chunk == b"\n":
            return data.decode("utf-8")

        data.extend(chunk)

        if len(data) > MAX_MESSAGE_BYTES:
            raise ValueError("Message exceeded the size limit.")


def handle_client(connection, address):
    """Receive client messages and send responses."""
    log(f"Client connected: {address}")

    # Close this client socket automatically
    with connection:
        connection.settimeout(120)

        try:
            while True:
                message = receive_message(connection)

                if message is None:
                    log("Client disconnected.")
                    break

                log(f"Received from client: {message}")

                if message.lower() == "quit":
                    connection.sendall(b"Goodbye!\n")
                    log("Sent Goodbye! Closing client connection cleanly.")
                    break

                response = f"Server received: {message}\n"
                connection.sendall(response.encode("utf-8"))
                log(f"Sent response: {response.strip()}")

        except socket.timeout:
            log("Client timed out; closing its connection.")
        except (OSError, ValueError, UnicodeError) as error:
            log(f"Client communication error: {error}")

    log("Client socket closed; ready for another connection.")


def main():
    """Create the server socket and wait for connections."""
    try:
        # AF_INET means IPv4. SOCK_STREAM means TCP.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind((HOST, PORT))
            server.listen(5)

            log(f"Listening on {HOST}:{PORT}. Press Ctrl+C to stop.")

            while True:
                connection, address = server.accept()
                handle_client(connection, address)

    except KeyboardInterrupt:
        log("Server stopped by user; sockets closed.")
    except OSError as error:
        log(f"Server error: {error}")


if __name__ == "__main__":
    main()
