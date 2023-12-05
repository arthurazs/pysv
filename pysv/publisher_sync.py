from socket import AF_PACKET, SOCK_RAW, socket
from sys import argv

from pysv.sv import DEFAULT_PATH, generate_sv_from
from pysv.utils import usleep


def run(interface: str) -> None:
    with socket(AF_PACKET, SOCK_RAW, 0xBA88) as nic:
        nic.bind((interface, 0))

        for time2sleep, header, pdu in generate_sv_from(DEFAULT_PATH):
            usleep(time2sleep)
            nic.sendall(header + pdu)


if __name__ == "__main__":
    run(argv[1])
