from socket import AF_PACKET, SOCK_RAW, socket
from time import time_ns

from pysv.sv import get_sv


def usleep(microseconds: int) -> None:
    end = time_ns() + (microseconds * 1e3)
    while True:
        if time_ns() >= end:
            break


def run() -> None:
    with socket(AF_PACKET, SOCK_RAW, 0xBA88) as nic:
        nic.bind(("lo", 0))

        for header, pdu in get_sv():
            usleep(250)
            nic.sendall(header + pdu)


if __name__ == "__main__":
    run()
