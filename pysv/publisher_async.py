from asyncio import gather, sleep
from contextlib import suppress
from socket import AF_PACKET, SOCK_RAW, socket
from sys import argv
from time import time_ns
from typing import TYPE_CHECKING

from uvloop import new_event_loop

from pysv.sv import get_sv

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop


async def usleep(microseconds: int) -> None:
    end = time_ns() + (microseconds * 1e3)
    while True:
        await sleep(0)
        if time_ns() >= end:
            break


async def run(loop: "AbstractEventLoop", interface: str) -> None:
    with socket(AF_PACKET, SOCK_RAW, 0xBA88) as nic:
        nic.bind((interface, 0))
        nic.setblocking(False)

        for header, pdu in get_sv():
            await gather(usleep(250), loop.sock_sendall(nic, header + pdu))


if __name__ == "__main__":
    loop = new_event_loop()
    with suppress(KeyboardInterrupt):
        loop.run_until_complete(run(loop, argv[1]))
    loop.close()
