import logging
import sys
from ctypes import CDLL
from pathlib import Path
from time import perf_counter
from typing import TYPE_CHECKING

from pysv.sv import generate_sv_from

if TYPE_CHECKING:
    from typing import Callable

logger = logging.getLogger(__name__)
dll_path = Path(__file__).parent
c_pub = CDLL(str(next(dll_path.glob("publisher*.so"))))


SendSvFunc = "Callable[[int, int, int, bytes, int], int]"


def _publisher(interface: str) -> tuple[int, int]:
    logger.debug("Opening socket...")
    socket_num = c_pub.get_socket()
    if socket_num == -1:
        msg = "Could not open socket, status -1"
        logger.error(msg)
        raise PermissionError(msg)
    logger.debug("Socket opened!")

    logger.debug("Finding %s interface...", interface)
    interface_index = c_pub.get_index(socket_num, interface.encode("utf8"))
    if interface_index == -1:
        msg = "Could not find interface %s, status -1" % interface
        logger.error(msg)
        raise ValueError(msg)
    logger.debug("Found at index %d!", interface_index)

    return socket_num, interface_index


def _send_sv(
    socket_num: int, interface_index: int, func: SendSvFunc, time2sleep: int, bytestring: bytes, length: int
) -> None:
    # len is necessary bc C's strlen does not work when there's \x00 values inside the SV frame
    status = func(socket_num, interface_index, time2sleep, bytestring, length)
    if status < 0:
        msg = "Could not send SV, status %d" % status
        logger.error(msg)
        raise RuntimeError(msg)


def _publisher_smart(interface: str, csv_path: "Path", func: SendSvFunc) -> None:
    socket_num, interface_index = _publisher(interface)

    previous_slept, previous_time2sleep = 0, 0
    for time2sleep, header, pdu in generate_sv_from(csv_path):
        before = perf_counter()
        diff = int(previous_time2sleep - previous_slept)
        if diff < -250:
            logger.critical(
                "\nprevious2sleep %d\nprevious_slept %d\ndiff %d\ntime2sleep %d\ntime2sleep + diff %d",
                previous_time2sleep, previous_slept, diff, time2sleep, time2sleep + diff,
            )
            diff = 0
        _send_sv(socket_num, interface_index, func, time2sleep + diff, header + pdu, len(header) + len(pdu))
        previous_slept = (perf_counter() - before) * 1e6
        previous_time2sleep = time2sleep

    c_pub.close_socket(socket_num)


def _publisher_dumb(interface: str, csv_path: "Path", func: SendSvFunc) -> None:
    socket_num, interface_index = _publisher(interface)

    for time2sleep, header, pdu in generate_sv_from(csv_path):
        _send_sv(socket_num, interface_index, func, time2sleep, header + pdu, len(header) + len(pdu))

    c_pub.close_socket(socket_num)


def publisher_busy_smart(interface: str, csv_path: "Path") -> None:
    _publisher_smart(interface, csv_path, c_pub.send_sv_busy_wait)


def publisher_busy_dumb(interface: str, csv_path: "Path") -> None:
    _publisher_dumb(interface, csv_path, c_pub.send_sv_busy_wait)


def publisher_rt_smart(interface: str, csv_path: "Path") -> None:
    _publisher_smart(interface, csv_path, c_pub.send_sv_rt)


def publisher_rt_dumb(interface: str, csv_path: "Path") -> None:
    _publisher_dumb(interface, csv_path, c_pub.send_sv_rt)
