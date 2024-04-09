from pysv.utils import enet_stom
from struct import pack, unpack
from dataclasses import dataclass
from enum import Enum
import decimal as dec
import logging
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

from pysn1.triplet import Triplet

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

logger = logging.getLogger(__name__)

DEFAULT_PATH = Path("data") / "REGUAS_BJDLAPA_50.csv"
UNPACKER_LENGTH = {1: "!B", 2: "!H"}


def read_sample(path: "Path") -> "Iterator[Sequence[str]]":
    with path.open() as csv:
        next(csv)  # skip header
        for data in csv:
            yield data.strip().split(",")


def parse_sample(string_sample: str) -> tuple[int, bytes]:
    sample = int(float(string_sample))
    return sample, pack("!i", sample) + b"\x00\x00\x00\x00"


def parse_neutral(sample: int) -> bytes:
    return pack("!i", sample) + b"\x00\x00\x20\x00"


class SamplesSynchronized(Enum):
    NONE = 0
    LOCAL = 1
    GLOBAL = 2

    def triplet(self: "SamplesSynchronized") -> "Triplet":
        return Triplet.build(tag=0x85, value=pack("!B", self.value))

    def __bytes__(self: "SamplesSynchronized") -> bytes:
        return bytes(self.triplet())


@dataclass
class SVHeader:
    # TODO @arthurazs: params should be classes instead of str, e.g., bytes(sv_header.src_addr)
    src_addr: str
    dst_addr: str
    app_id: str
    sv_id: str
    smp_sync: "SamplesSynchronized"

    @property
    def src_addr_bytes(self: "SVHeader") -> bytes:
        return enet_stom(self.src_addr)

    @property
    def dst_addr_bytes(self: "SVHeader") -> bytes:
        return enet_stom(self.src_addr)

    @property
    def app_id_bytes(self: "SVHeader") -> bytes:
        # see 61850-9-2
        return pack("!H", int(self.app_id, 16))

    @property
    def sv_id_bytes(self: "SVHeader") -> bytes:
        return bytes(Triplet.build(tag=0x80, value=self.sv_id.encode()))  # vString129

    @property
    def smp_sync_bytes(self: "SVHeader") -> bytes:
        return bytes(self.smp_sync)


def generate_sv_from(
    path: "Path", sv_header: "SVHeader", frequency: int = 4000,
) -> "Iterator[tuple[int, int, bytes, bytes]]":
    """Generates SV frames.

    Returns:
         (time2sleep_in_us, header, pdu)
    """
    src_addr = sv_header.src_addr_bytes
    dst_addr = sv_header.dst_addr_bytes
    sv_ether = b"\x88\xba"
    app_id = sv_header.app_id_bytes
    length = b"\x00\x66"  # TODO(arthurazs): calc?
    reserved = b"\x00\x00\x00\x00"
    sav_pdu = Triplet.build(tag=0x60, value=b"")
    sv_type = b"\x60"
    sv_len = b"\x5C"  # TODO(arthurazs): calc?
    num_asdu = b"\x80\x01\x01"
    seq_asdu_type = b"\xa2"
    seq_asdu_len = b"\x57"  # TODO(arthurazs): calc?
    asdu_type = b"\x30"
    asdu_len = b"\x55"  # TODO(arthurazs): calc?
    sv_id = sv_header.sv_id_bytes
    conf_rev = b"\x83\x04\x00\x00\x00\x01"
    smp_synch = sv_header.smp_sync_bytes
    previous_sleep_time = dec.Decimal(0)
    for index, (sleep_time, i_as, i_bs, i_cs, v_as, v_bs, v_cs) in enumerate(read_sample(path)):
        current_sleep_time = dec.Decimal(sleep_time)
        time2sleep = current_sleep_time - previous_sleep_time
        previous_sleep_time = current_sleep_time
        logger.debug(
            "time2sleep %.0f us | current %.0f us | previous %.0f us",
            time2sleep,
            current_sleep_time,
            previous_sleep_time,
        )
        i_ai, i_a = parse_sample(i_as)
        i_bi, i_b = parse_sample(i_bs)
        i_ci, i_c = parse_sample(i_cs)
        i_n = parse_neutral(i_ai + i_bi + i_ci)

        v_ai, v_a = parse_sample(v_as)
        v_bi, v_b = parse_sample(v_bs)
        v_ci, v_c = parse_sample(v_cs)
        v_n = parse_neutral(v_ai + v_bi + v_ci)
        smp_cnt = int(index % frequency)
        smp_cnt_bytes = b"\x82\x02" + pack("!h", smp_cnt)

        header = (
            dst_addr + src_addr + sv_ether + app_id + length + reserved + sv_type + sv_len + num_asdu + seq_asdu_type +
            seq_asdu_len + asdu_type + asdu_len + sv_id + smp_cnt_bytes + conf_rev + smp_synch
        )
        pdu = bytes(Triplet.build(tag=0x87, value=i_a + i_b + i_c + i_n + v_a + v_b + v_c + v_n))
        yield int(time2sleep), smp_cnt, header, pdu


class PhsMeas(NamedTuple):
    smp_cnt: int
    i_a: int
    i_b: int
    i_c: int
    i_n: int
    v_a: int
    v_b: int
    v_c: int
    v_n: int


def unpack_sv(bytes_string: bytes) -> PhsMeas:
    _dst = bytes_string[0:6]
    _src = bytes_string[6:12]
    _eth_type = bytes_string[12:14]
    _app_id = bytes_string[14:16]
    _length = unpack("!H", bytes_string[16:18])
    _reserved1 = bytes_string[18:20]
    _reserved2 = bytes_string[20:22]
    sav_pdu = Triplet.from_bytes(bytes_string[22:])
    num_of_asdu = Triplet.from_bytes(sav_pdu.value)
    seq_asdu = Triplet.from_bytes(sav_pdu.value[len(num_of_asdu):])
    asdu = Triplet.from_bytes(seq_asdu.value)
    sv_id = Triplet.from_bytes(asdu.value)
    tmp_index = len(sv_id)
    smp_cnt_asn1 = Triplet.from_bytes(asdu.value[tmp_index:])
    tmp_index += len(smp_cnt_asn1)
    conf_rev = Triplet.from_bytes(asdu.value[tmp_index:])
    tmp_index += len(conf_rev)
    smp_synch = Triplet.from_bytes(asdu.value[tmp_index:])
    tmp_index += len(smp_synch)
    phs_meas1 = Triplet.from_bytes(asdu.value[tmp_index:])
    del tmp_index
    i_a, _, i_b, _, i_c, _, i_n, _ = unpack("!8i", phs_meas1.value[: 8 * 4])
    v_a, _, v_b, _, v_c, _, v_n, _ = unpack("!8i", phs_meas1.value[8 * 4:])

    smp_cnt = unpack("!B" if smp_cnt_asn1.length == 1 else "!H", smp_cnt_asn1.value)[0]
    return PhsMeas(smp_cnt=smp_cnt, i_a=i_a, i_b=i_b, i_c=i_c, i_n=i_n, v_a=v_a, v_b=v_b, v_c=v_c, v_n=v_n)
