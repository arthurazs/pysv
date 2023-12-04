import logging
from contextlib import suppress
from itertools import count
from socket import AF_PACKET, SOCK_RAW, socket
from sys import argv
from time import time_ns

from pysv.sv import unpack_sv

logger = logging.getLogger(__name__)


def run(interface: str) -> None:
    with socket(AF_PACKET, SOCK_RAW, 0xBA88) as nic:
        nic.bind((interface, 0))

        logger.info(time_ns())

        for counter in count():
            elapsed = time_ns()
            data = nic.recv(113)
            smp_cnt, i_a, i_b, i_c, i_n, v_a, v_b, v_c, v_n = unpack_sv(data)
            logger.info(
                "%4d/%4d: %13.3f us | ia %6d | ib %6d | ic %6d | in %6d |<>| va %6d | vb %6d | vc %6d | vn %6d",
                counter, smp_cnt, (time_ns() - elapsed) * 1E-3, i_a, i_b, i_c, i_n, v_a, v_b, v_c, v_n,
            )


if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        run(argv[1])
