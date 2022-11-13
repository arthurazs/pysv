from asyncio import gather
from contextlib import suppress
from socket import AF_PACKET, SOCK_RAW, socket
from sys import argv
from typing import TYPE_CHECKING

from uvloop import new_event_loop

from pysv.sv import DEFAULT_PATH, generate_sv_from
from pysv.utils import async_usleep

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop


async def run(loop: "AbstractEventLoop", interface: str) -> None:
    with socket(AF_PACKET, SOCK_RAW, 0xBA88) as nic:
        nic.bind((interface, 0))
        nic.setblocking(False)

        for header, pdu in generate_sv_from(DEFAULT_PATH):
            await gather(async_usleep(250), loop.sock_sendall(nic, header + pdu))


if __name__ == "__main__":
    loop = new_event_loop()
    with suppress(KeyboardInterrupt):
        loop.run_until_complete(run(loop, argv[1]))
    loop.close()
