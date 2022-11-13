from socket import AF_PACKET, SOCK_RAW, socket

from pysv.sv import DEFAULT_PATH, generate_sv_from
from pysv.utils import usleep


def run() -> None:
    with socket(AF_PACKET, SOCK_RAW, 0xBA88) as nic:
        nic.bind(("lo", 0))

        for header, pdu in generate_sv_from(DEFAULT_PATH):
            usleep(250)
            nic.sendall(header + pdu)


if __name__ == "__main__":
    run()
