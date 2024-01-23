import logging
import sys
from ctypes import CDLL
from pathlib import Path

from pysv.sv import generate_sv_from

logger = logging.getLogger(__name__)
dll_path = Path(__file__).parent
c_pub = CDLL(str(next(dll_path.glob("publisher*.so"))))


def publisher(interface: str, csv_path: "Path") -> None:
    logger.debug("Opening socket...")
    socket_num = c_pub.get_socket()
    if socket_num == -1:
        logger.error("Could not open socket")
        sys.exit(socket_num)
    logger.debug("Socket opened!")

    logger.debug("Finding %s interface...", interface)
    interface_index = c_pub.get_index(socket_num, interface.encode("utf8"))
    if interface_index == -1:
        logger.error("Could not find interface %s", interface)
        sys.exit(interface_index)
    logger.debug("Found at index %d!", interface_index)

    for _time2sleep, header, _pdu in generate_sv_from(csv_path):
        smp_cnt = header[-11:-9]
        logger.debug("smp_cnt len: %d", len(smp_cnt))
        status = c_pub.send_sv(
            socket_num,
            interface_index,
            b"\x01\x0c\xcd\x04\x00\x00"
            b"\x00\xbe\x43\xcc\x53\x68" +
            smp_cnt,
            # pdu[2:],
        )
        if status != 0:
            logger.error("Could not send SV, status %d", status)
            sys.exit(status)

