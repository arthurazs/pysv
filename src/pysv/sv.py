import decimal as dec
import logging
from pathlib import Path
from struct import pack as s_pack
from struct import unpack as s_unpack
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
    return sample, s_pack("!i", sample) + b"\x00\x00\x00\x00"


def parse_neutral(sample: int) -> bytes:
    return s_pack("!i", sample) + b"\x00\x00\x20\x00"


def generate_sv_from(path: "Path") -> "Iterator[tuple[int, bytes, bytes]]":
    src_addr = b"\x00\x30\xa7\x22\x8d\x5d"
    dst_addr = b"\x01\x0c\xcd\x04\x00\x01"
    sv_ether = b"\x88\xba"
    app_id = b"\x40\x00"
    length = b"\x00\x63"  # TODO(arthurazs): calc?
    reserved = b"\x00\x00\x00\x00"
    sv_type = b"\x60"
    sv_len = b"\x59"  # TODO(arthurazs): calc?
    num_asdu = b"\x80\x01\x01"
    seq_asdu_type = b"\xa2"
    seq_asdu_len = b"\x54"  # TODO(arthurazs): calc?
    asdu_type = b"\x30"
    asdu_len = b"\x52"  # TODO(arthurazs): calc?
    sv_id = b"\x80\x01\x32"
    conf_rev = b"\x83\x04\x00\x00\x00\x01"
    smp_synch = b"\x85\x01\x00"
    phs_meas_type_len = b"\x87\x40"
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
        smp_cnt = b"\x82\x02" + s_pack("!h", int(index % 4000))

        header = (
            dst_addr
            + src_addr
            + sv_ether
            + app_id
            + length
            + reserved
            + sv_type
            + sv_len
            + num_asdu
            + seq_asdu_type
            + seq_asdu_len
            + asdu_type
            + asdu_len
            + sv_id
            + smp_cnt
            + conf_rev
            + smp_synch
        )
        pdu = phs_meas_type_len + i_a + i_b + i_c + i_n + v_a + v_b + v_c + v_n
        yield int(time2sleep), header, pdu


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
    _length = s_unpack("!H", bytes_string[16:18])
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
    i_a, _, i_b, _, i_c, _, i_n, _ = s_unpack("!8i", phs_meas1.value[: 8 * 4])
    v_a, _, v_b, _, v_c, _, v_n, _ = s_unpack("!8i", phs_meas1.value[8 * 4:])

    smp_cnt = s_unpack("!B" if smp_cnt_asn1.length == 1 else "!H", smp_cnt_asn1.value)[0]
    return PhsMeas(
        smp_cnt=smp_cnt,
        i_a=i_a,
        i_b=i_b,
        i_c=i_c,
        i_n=i_n,
        v_a=v_a,
        v_b=v_b,
        v_c=v_c,
        v_n=v_n,
    )
