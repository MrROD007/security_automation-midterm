"""A local TCP client for the networking midterm."""

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
    """Read a response until its ending newline."""
    data = bytearray()

    while True:
        chunk = connection.recv(1)

        # An empty result means the server closed the connection.
        if not chunk:
            if data:
                raise ConnectionError("Connection ended during a response.")
            return None

        if chunk == b"\n":
            return data.decode("utf-8")

        data.extend(chunk)

        if len(data) > MAX_MESSAGE_BYTES:
            raise ValueError("Response exceeded the size limit.")


def main():
    """Connect to the server and exchange messages."""
    try:
        # Create an IPv4 TCP socket and close it when finished.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.settimeout(5)

            log(f"Connecting to {HOST}:{PORT}...")
            client.connect((HOST, PORT))
            log("Connected. Type a message, or type quit to disconnect.")

            while True:
                try:
                    message = input("You: ")
                except EOFError:
                    message = "quit"

                if not message:
                    log("Please enter a message.")
                    continue

                encoded = message.encode("utf-8")

                if len(encoded) > MAX_MESSAGE_BYTES:
                    log(f"Message must be {MAX_MESSAGE_BYTES} bytes or fewer.")
                    continue

                # A newline marks the end of each message.
                client.sendall(encoded + b"\n")
                response = receive_message(client)

                if response is None:
                    log("Server closed the connection.")
                    break

                log(f"Received from server: {response}")

                if message.lower() == "quit":
                    log("Clean disconnection completed.")
                    break

    except ConnectionRefusedError:
        log("Connection refused. Start server.py, then try again.")
    except socket.timeout:
        log("Connection or response timed out.")
    except KeyboardInterrupt:
        log("Client stopped by user.")
    except (OSError, ValueError, UnicodeError) as error:
        log(f"Client error: {error}")
    finally:
        log("Client finished; socket closed if it was created.")


if __name__ == "__main__":
    main()
