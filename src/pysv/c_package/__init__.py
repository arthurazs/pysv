import logging
from ctypes import CDLL
from pathlib import Path
from time import perf_counter
from typing import TYPE_CHECKING, Callable  # noqa: UP035

from pysv.sv import generate_sv_from, return_sv_from

if TYPE_CHECKING:

    from pysv.sv import SVConfig

logger = logging.getLogger(__name__)
dll_path = Path(__file__).parent
c_pub = CDLL(str(next(dll_path.glob("publisher*.so"))))


SendSvFunc = Callable[[int, int, int, bytes, int], int]
NewSendSvFunc = Callable[[int, int, bytes, int, int, int], int]


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
    socket_num: int, interface_index: int, func: SendSvFunc, time2sleep: int, bytestring: bytes, length: int,
) -> None:
    # len is necessary bc C's strlen does not work when there's \x00 values inside the SV frame
    status = func(socket_num, interface_index, time2sleep, bytestring, length)
    if status < 0:
        msg = "Could not send SV, status %d" % status
        logger.error(msg)
        raise RuntimeError(msg)


def _send_default_sv(
    socket_num: int, interface_index: int, func: NewSendSvFunc,
    all_svs: bytes, sv_count: int, sv_length: int, time2sleep: int,
) -> None:
    # len is necessary bc C's strlen does not work when there's \x00 values inside the SV frame
    status = func(socket_num, interface_index, all_svs, sv_count, sv_length, time2sleep)
    if status < 0:
        msg = "Could not send SV, status %d" % status
        logger.error(msg)
        raise RuntimeError(msg)


def _publisher_smart(interface: str, csv_path: "Path", sv_config: "SVConfig", func: SendSvFunc) -> None:
    socket_num, interface_index = _publisher(interface)

    previous_slept, previous_time2sleep = 0, 0

    first = True
    t2s = 250
    for _, smp_cnt, sv in generate_sv_from(csv_path, sv_config):
        before = perf_counter()
        diff = previous_time2sleep - previous_slept
        if diff < -t2s:
            logger.critical(
                "\nprevious2sleep %d\nprevious_slept %d\ndiff %d\ntime2sleep %d\ntime2sleep + diff %d\nsmp cnt %d",
                previous_time2sleep, previous_slept, diff, t2s, t2s + diff, smp_cnt,
            )
            diff = 0
        if first:
            _send_sv(
                socket_num, interface_index, c_pub.send_first_sv_busy_wait,
                t2s + diff, sv, len(sv),
            )
            first = False
            previous_slept = t2s
        else:
            _send_sv(socket_num, interface_index, func, t2s + diff, sv, len(sv))
            previous_slept = int((perf_counter() - before) * 1e6)
        previous_time2sleep = t2s

    c_pub.close_socket(socket_num)


def _publisher_dumb(interface: str, csv_path: "Path", sv_config: "SVConfig", func: SendSvFunc) -> None:
    socket_num, interface_index = _publisher(interface)

    for time2sleep, _smp_cnt, sv in generate_sv_from(csv_path, sv_config):
        _send_sv(socket_num, interface_index, func, time2sleep, sv, len(sv))

    c_pub.close_socket(socket_num)


def _publisher_default(interface: str, csv_path: "Path", sv_config: "SVConfig", func: NewSendSvFunc) -> None:
    socket_num, interface_index = _publisher(interface)

    logger.info("Loading file and parsing into bytes..")
    time2sleep, svs, count, sv_len = return_sv_from(csv_path, sv_config)
    logger.info("Sending SV frames...")
    _send_default_sv(socket_num, interface_index, func, svs, count, sv_len, time2sleep)

    c_pub.close_socket(socket_num)


def publisher_default(interface: str, csv_path: "Path", sv_config: "SVConfig") -> None:
    _publisher_default(interface, csv_path, sv_config, c_pub.send_sv)


def publisher_busy_smart(interface: str, csv_path: "Path", sv_config: "SVConfig") -> None:
    _publisher_smart(interface, csv_path, sv_config, c_pub.send_sv_busy_wait)


def publisher_busy_dumb(interface: str, csv_path: "Path", sv_config: "SVConfig") -> None:
    _publisher_dumb(interface, csv_path, sv_config, c_pub.send_sv_busy_wait)


def publisher_rt_smart(interface: str, csv_path: "Path", sv_config: "SVConfig") -> None:
    _publisher_smart(interface, csv_path, sv_config, c_pub.send_sv_rt)


def publisher_rt_dumb(interface: str, csv_path: "Path", sv_config: "SVConfig") -> None:
    _publisher_dumb(interface, csv_path, sv_config, c_pub.send_sv_rt)
