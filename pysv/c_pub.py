import logging
import sys
from ctypes import CDLL
from pathlib import Path
from pysv.sv import DEFAULT_PATH, generate_sv_from

logger = logging.getLogger(__name__)

c_pub = CDLL(str(Path.cwd() / "pysv" / "c_package" / "publisher.so"))


def run(interface: str, csv_path: "Path") -> None:
    socket_num = c_pub.open_socket()
    if socket_num == -1:
        logger.error("Could not open socket")
        sys.exit(socket_num)

    for time2sleep, header, pdu in generate_sv_from(csv_path):
        smp_cnt = header[-11:-9]
        # return
        status = c_pub.send_sv(
            socket_num,
            b"\x01\x0c\xcd\x04\x00\x00", b"\x00\xbe\x43\xcc\x53\x68",
            smp_cnt,
            pdu[2:]
        )
        if status != 0:
            logger.error(status)
