import logging
from itertools import count
from socket import AF_PACKET, SOCK_RAW, socket
from time import time_ns
from typing import TYPE_CHECKING
from statistics import mean
from pysv.sv import unpack_sv

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop


logger = logging.getLogger(__name__)


async def run(loop: "AbstractEventLoop", interface: str) -> None:
    with socket(AF_PACKET, SOCK_RAW, 0xBA88) as nic:
        nic.bind((interface, 0))
        nic.setblocking(False)  # noqa: FBT003

        logger.info(time_ns())

        # means = ()

        for counter in count():
            elapsed = time_ns()
            data = await loop.sock_recv(nic, 113)
            smp_cnt, i_a, i_b, i_c, i_n, v_a, v_b, v_c, v_n = unpack_sv(data)
            # means += ((time_ns() - elapsed) * 1E-3, )
            logger.info(
                "%4d/%4d: %13.3f us | ia %6d | ib %6d | ic %6d | in %6d |<>| va %6d | vb %6d | vc %6d | vn %6d",
                counter, smp_cnt, (time_ns() - elapsed) * 1E-3, i_a, i_b, i_c, i_n, v_a, v_b, v_c, v_n,
            )
            # if counter == 1199:
            #     logger.info(mean(means[1:]))
