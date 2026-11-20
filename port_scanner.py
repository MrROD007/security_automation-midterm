"""A limited TCP port scanner for authorized assignment testing."""

import argparse
import socket
import time
from datetime import datetime

ALLOWED_TARGETS = {"localhost", "127.0.0.1", "scanme.nmap.org"}
TIMEOUT = 1.0
DELAY = 0.25
MAX_PORTS_PER_RUN = 100


def log(message):
    """Print a message with a local timestamp."""
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    print(f"[{timestamp}] {message}", flush=True)


def parse_ports(text):
    """Accept selected ports or one inclusive port range."""
    try:
        if "-" in text:
            parts = text.split("-")

            if len(parts) != 2:
                raise ValueError

            start, end = (int(part) for part in parts)

            if not 1 <= start <= end <= 65535:
                raise ValueError

            if end - start + 1 > MAX_PORTS_PER_RUN:
                raise argparse.ArgumentTypeError(
                    f"Use no more than {MAX_PORTS_PER_RUN} ports per run."
                )

            ports = list(range(start, end + 1))

        else:
            ports = sorted({int(part) for part in text.split(",")})

            if not ports or any(port < 1 or port > 65535 for port in ports):
                raise ValueError

            if len(ports) > MAX_PORTS_PER_RUN:
                raise argparse.ArgumentTypeError(
                    f"Use no more than {MAX_PORTS_PER_RUN} ports per run."
                )

    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "Use ports 1-65535, such as 21,22,80,443 or 4998-5002."
        ) from error

    return ports


def scan_port(address, port):
    """Try one TCP connection and describe the result."""
    try:
        # Close each probe socket automatically after its attempt.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.settimeout(TIMEOUT)
            probe.connect((address, port))
            return "OPEN"

    except ConnectionRefusedError:
        return "CLOSED (connection refused)"
    except socket.timeout:
        return "NO RESPONSE (timeout; possibly filtered or unreachable)"
    except OSError as error:
        return f"NETWORK ERROR: {error}"


def main():
    """Validate arguments and scan approved targets sequentially."""
    parser = argparse.ArgumentParser(
        description="Scan only localhost, 127.0.0.1, or scanme.nmap.org."
    )
    parser.add_argument(
        "target",
        help="An approved hostname or IP address",
    )
    parser.add_argument(
        "--ports",
        type=parse_ports,
        required=True,
        help="Selected ports or one range, such as 22,80 or 4998-5002",
    )

    args = parser.parse_args()
    target = args.target.strip().lower()

    # Reject unapproved targets before DNS lookup or connection.
    if target not in ALLOWED_TARGETS:
        parser.error(
            "Unauthorized target. Use localhost, 127.0.0.1, "
            "or scanme.nmap.org only."
        )

    try:
        # Use one IPv4 address throughout this scan.
        if target in {"localhost", "127.0.0.1"}:
            address = "127.0.0.1"
        else:
            address = socket.gethostbyname(target)

    except OSError as error:
        log(f"Cannot resolve approved target {target}: {error}")
        return

    log(f"Target: {target} ({address})")
    log(
        f"Ports: {len(args.ports)} | Timeout: {TIMEOUT}s | "
        f"Delay: {DELAY}s"
    )

    started = time.perf_counter()
    open_count = 0
    completed = 0

    try:
        for index, port in enumerate(args.ports):
            result = scan_port(address, port)
            log(f"Port {port}: {result}")

            completed += 1

            if result == "OPEN":
                open_count += 1

            # Pause between attempts rather than scanning aggressively.
            if index < len(args.ports) - 1:
                time.sleep(DELAY)

    except KeyboardInterrupt:
        log("Scan interrupted by user.")

    finally:
        elapsed = time.perf_counter() - started
        log(
            f"Finished: {completed}/{len(args.ports)} ports checked, "
            f"{open_count} open, elapsed {elapsed:.2f} seconds."
        )


if __name__ == "__main__":
    main()
