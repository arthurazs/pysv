import logging
from itertools import count
from socket import AF_PACKET, SOCK_RAW, socket
from time import time_ns
from typing import TYPE_CHECKING

from pysv.sv import unpack_sv

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop


logger = logging.getLogger(__name__)


async def run(loop: "AbstractEventLoop", interface: str) -> None:
    with socket(AF_PACKET, SOCK_RAW, 0xBA88) as nic:
        logger.info("binding to %s", interface)
        nic.bind((interface, 0))
        nic.setblocking(False)  # noqa: FBT003

        logger.info(time_ns())

        for counter in count():
            elapsed = time_ns()
            # TODO @arthurazs: recv 18 bytes, then while true receiving the rest
            data = await loop.sock_recv(nic, 113)
            smp_cnt, i_a, i_b, i_c, i_n, v_a, v_b, v_c, v_n = unpack_sv(data)
            logger.info(
                "%4d/%4d: %13.3f us | ia %7d | ib %7d | ic %7d | in %7d |<>| va %7d | vb %7d | vc %7d | vn %7d",
                counter, smp_cnt, (time_ns() - elapsed) * 1E-3, i_a, i_b, i_c, i_n, v_a, v_b, v_c, v_n,
            )
