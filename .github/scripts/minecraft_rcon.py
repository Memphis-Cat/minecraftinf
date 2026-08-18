#!/usr/bin/env python3
"""Minimal Minecraft RCON client used by the Phase 1 server smoke tests."""

from __future__ import annotations

import argparse
import socket
import struct
import sys
import time
from dataclasses import dataclass


SERVERDATA_RESPONSE_VALUE = 0
SERVERDATA_EXECCOMMAND = 2
SERVERDATA_AUTH_RESPONSE = 2
SERVERDATA_AUTH = 3
MAX_PACKET_LENGTH = 4 * 1024 * 1024


@dataclass(frozen=True)
class Packet:
    request_id: int
    packet_type: int
    body: str


def receive_exactly(connection: socket.socket, byte_count: int) -> bytes:
    chunks: list[bytes] = []
    remaining = byte_count
    while remaining:
        chunk = connection.recv(remaining)
        if not chunk:
            raise ConnectionError("RCON connection closed unexpectedly")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def receive_packet(connection: socket.socket) -> Packet:
    (packet_length,) = struct.unpack("<i", receive_exactly(connection, 4))
    if packet_length < 10 or packet_length > MAX_PACKET_LENGTH:
        raise ValueError(f"Invalid RCON packet length: {packet_length}")

    payload = receive_exactly(connection, packet_length)
    request_id, packet_type = struct.unpack("<ii", payload[:8])
    if payload[-2:] != b"\x00\x00":
        raise ValueError("RCON packet is missing its two null terminators")

    return Packet(request_id, packet_type, payload[8:-2].decode("utf-8", errors="replace"))


def send_packet(connection: socket.socket, request_id: int, packet_type: int, body: str) -> None:
    encoded_body = body.encode("utf-8")
    payload = struct.pack("<ii", request_id, packet_type) + encoded_body + b"\x00\x00"
    connection.sendall(struct.pack("<i", len(payload)) + payload)


def execute_command(host: str, port: int, password: str, command: str, timeout: float) -> str:
    with socket.create_connection((host, port), timeout=timeout) as connection:
        connection.settimeout(timeout)

        auth_request_id = 0x43435542
        send_packet(connection, auth_request_id, SERVERDATA_AUTH, password)
        auth_response = receive_packet(connection)
        if auth_response.packet_type != SERVERDATA_AUTH_RESPONSE or auth_response.request_id == -1:
            raise PermissionError("Minecraft RCON authentication failed")
        if auth_response.request_id != auth_request_id:
            raise ValueError(
                f"Unexpected RCON authentication response ID: {auth_response.request_id}"
            )

        command_request_id = auth_request_id + 1
        send_packet(connection, command_request_id, SERVERDATA_EXECCOMMAND, command)
        response = receive_packet(connection)
        if response.request_id != command_request_id:
            raise ValueError(f"Unexpected RCON command response ID: {response.request_id}")
        if response.packet_type not in (SERVERDATA_RESPONSE_VALUE, SERVERDATA_AUTH_RESPONSE):
            raise ValueError(f"Unexpected RCON command response type: {response.packet_type}")
        return response.body


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", help="Minecraft server command without a leading slash")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=25575)
    parser.add_argument("--password", required=True)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--connect-timeout", type=float, default=60.0)
    parser.add_argument(
        "--allow-disconnect",
        action="store_true",
        help="Treat a disconnect after sending the command as success (useful for stop)",
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    deadline = time.monotonic() + arguments.connect_timeout
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            response = execute_command(
                arguments.host,
                arguments.port,
                arguments.password,
                arguments.command,
                arguments.timeout,
            )
            if response:
                print(response)
            return 0
        except (ConnectionError, ConnectionRefusedError, socket.timeout, OSError) as error:
            last_error = error
            if arguments.allow_disconnect and isinstance(error, ConnectionError):
                return 0
            time.sleep(0.5)
        except (PermissionError, ValueError) as error:
            print(f"RCON protocol error: {error}", file=sys.stderr)
            return 2

    print(f"Unable to execute RCON command before timeout: {last_error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
