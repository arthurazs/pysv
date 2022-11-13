from contextlib import suppress
from itertools import count
from socket import AF_PACKET, SOCK_RAW, socket
from sys import argv
from time import time_ns
from typing import TYPE_CHECKING

import uvloop

from pysv.sv import unpack_sv

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop


async def run(loop: "AbstractEventLoop", interface: str) -> None:
    with socket(AF_PACKET, SOCK_RAW, 0xBA88) as nic:
        nic.bind((interface, 0))
        nic.setblocking(False)

        for counter in count():
            elapsed = time_ns()
            data = await loop.sock_recv(nic, 113)
            smp_cnt, i_a, i_b, i_c, i_n, v_a, v_b, v_c, v_n = unpack_sv(data)
            print(
                f"{counter:4}/{smp_cnt:4}: {(time_ns() - elapsed) * 1E-3:13.3f} us |"
                f" ia {i_a:6} | ib {i_b:6} | ic {i_c:6} | in {i_n:6} |<>|"
                f" va {v_a:6} | vb {v_b:6} | vc {v_c:6} | vn {v_n:6}"
            )


if __name__ == "__main__":
    loop = uvloop.new_event_loop()
    with suppress(KeyboardInterrupt):
        loop.run_until_complete(run(loop, argv[1]))
    loop.close()
