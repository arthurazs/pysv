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
class SVConfig:
    # TODO @arthurazs: params should be classes instead of str, e.g., bytes(sv_config.src_addr)
    src_addr: str
    dst_addr: str
    app_id: str
    sv_id: str
    conf_rev: int
    smp_sync: "SamplesSynchronized"

    @property
    def src_addr_bytes(self: "SVConfig") -> bytes:
        return enet_stom(self.src_addr)

    @property
    def dst_addr_bytes(self: "SVConfig") -> bytes:
        return enet_stom(self.src_addr)

    @property
    def app_id_bytes(self: "SVConfig") -> bytes:
        # see 61850-9-2
        return pack("!H", int(self.app_id, 16))

    @property
    def sv_id_bytes(self: "SVConfig") -> bytes:
        return bytes(Triplet.build(tag=0x80, value=self.sv_id.encode()))  # vString129

    @property
    def conf_rev_bytes(self: "SVConfig") -> bytes:
        return bytes(Triplet.build(tag=0x83, value=pack("!I", self.conf_rev)))

    @property
    def smp_sync_bytes(self: "SVConfig") -> bytes:
        return bytes(self.smp_sync)


def generate_sv_from(
    path: "Path", sv_config: "SVConfig", frequency: int = 4000,
) -> "Iterator[tuple[int, int, bytes, bytes]]":
    """Generates SV frames.

    Returns:
         (time2sleep_in_us, header, pdu)
    """
    dst_mac = sv_config.dst_addr_bytes
    src_mac = sv_config.src_addr_bytes
    ether_type = b"\x88ba"
    header = dst_mac + src_mac + ether_type

    app_id = sv_config.app_id_bytes
    reserved1 = b"\x00\x00"
    reserved2 = b"\x00\x00"

    sv_id = sv_config.sv_id_bytes
    conf_rev = sv_config.smp_sync_bytes
    smp_sync = sv_config.smp_sync_bytes

    no_asdu = b"\x80\x01\x01"

    previous_sleep_time = dec.Decimal(0)
    for index, (sleep_time, i_as, i_bs, i_cs, v_as, v_bs, v_cs) in enumerate(read_sample(path)):
        current_sleep_time = dec.Decimal(sleep_time)
        time2sleep = current_sleep_time - previous_sleep_time
        previous_sleep_time = current_sleep_time

        i_ai, i_a = parse_sample(i_as)
        i_bi, i_b = parse_sample(i_bs)
        i_ci, i_c = parse_sample(i_cs)
        i_n = parse_neutral(i_ai + i_bi + i_ci)

        v_ai, v_a = parse_sample(v_as)
        v_bi, v_b = parse_sample(v_bs)
        v_ci, v_c = parse_sample(v_cs)
        v_n = parse_neutral(v_ai + v_bi + v_ci)

        smp_cnt_int = int(index % frequency)
        smp_cnt = bytes(Triplet.build(tag=0x82, value=pack("!H", smp_cnt_int)))
        phs_meas = bytes(Triplet.build(tag=0x87, value=i_a + i_b + i_c + i_n + v_a + v_b + v_c + v_n))
        asdu = bytes(Triplet.build(tag=0x30, value=sv_id + smp_cnt + conf_rev + smp_sync + phs_meas))

        seq_asdu = bytes(Triplet.build(tag=0xa2, value=asdu))
        sav_pdu = bytes(Triplet.build(tag=0x60, value=no_asdu + seq_asdu))

        # TODO @arthurazs: improve length calc (it should always be the same)
        length = pack("!H", len(sav_pdu) + 8)
        sv = app_id + length + reserved1 + reserved2 + sav_pdu

        yield int(time2sleep), smp_cnt_int, header, sv


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
    no_asdu = Triplet.from_bytes(sav_pdu.value)
    seq_asdu = Triplet.from_bytes(sav_pdu.value[len(no_asdu):])
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
