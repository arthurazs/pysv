import logging
from asyncio import gather
from socket import AF_PACKET, SOCK_RAW, socket
from typing import TYPE_CHECKING

from pysv.sv import SVConfig, generate_sv_from
from pysv.utils import async_usleep

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop
    from pathlib import Path

logger = logging.getLogger(__name__)


async def run(loop: "AbstractEventLoop", interface: str, csv_path: "Path", sv_config: "SVConfig") -> None:
    with socket(AF_PACKET, SOCK_RAW, 0xBA88) as nic:
        logger.info("binding to %s", interface)
        nic.bind((interface, 0))
        nic.setblocking(False)  # noqa: FBT003

        # TODO(arthurazs): check using chrt --rr
        # TODO(arthurazs): check running async_usleep(250) instead of async_usleep(time2sleep)
        # TODO(arthurazs): check sleeping 2_500 between each 10 SVs, instead of 250 each SV
        for time2sleep, _smp_cnt, sv in generate_sv_from(csv_path, sv_config):
            await gather(async_usleep(time2sleep), loop.sock_sendall(nic, sv))
