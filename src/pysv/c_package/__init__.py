import logging
import sys
from ctypes import CDLL
from pathlib import Path
from time import perf_counter
import decimal as dec

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

    previous_slept = 0
    previous_time2sleep = 0
    for time2sleep, header, pdu in generate_sv_from(csv_path):
        before = perf_counter()
        # diff = max(0, int(previous_time2sleep - previous_slept))
        diff = int(previous_time2sleep - previous_slept)
        if diff < -250:
            logger.critical("\nprevious2sleep %d\nprevious_slept %d\ndiff %d\ntime2sleep %d\ntime2sleep + diff %d", previous_time2sleep, previous_slept, diff, time2sleep, time2sleep + diff)
            diff = 0
        status = c_pub.send_sv_busy_wait(
            socket_num,
            interface_index,
            time2sleep + diff,
            header + pdu,
            # len is necessary bc C's strlen does not work when there's \x00 values inside the SV frame
            len(header) + len(pdu),
            )
        if status < 0:
            logger.error("Could not send SV, status %d", status)
            sys.exit(status)
        previous_slept = (perf_counter() - before) * 1e6
        previous_time2sleep = time2sleep


def publisher_dumb(interface: str, csv_path: "Path") -> None:
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

    for time2sleep, header, pdu in generate_sv_from(csv_path):
        status = c_pub.send_sv_busy_wait(
            socket_num,
            interface_index,
            time2sleep,
            header + pdu,
            # len is necessary bc C's strlen does not work when there's \x00 values inside the SV frame
            len(header) + len(pdu),
            )
        if status < 0:
            logger.error("Could not send SV, status %d", status)
            sys.exit(status)
