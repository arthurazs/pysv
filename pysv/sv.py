from pathlib import Path
from struct import pack as s_pack
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterator, Sequence


def read_sample() -> "Iterator[Sequence[str]]":
    path = Path("data") / "1999sub0_analog.csv"
    with path.open() as csv:
        next(csv)  # skip header
        for data in csv:
            yield data.strip().split(",")


def parse_sample(string_sample: str) -> tuple[int, bytes]:
    sample = int(float(string_sample))
    return sample, s_pack("!i", sample) + b"\x00\x00\x00\x00"


def parse_neutral(sample: int) -> bytes:
    return s_pack("!i", sample) + b"\x00\x00\x20\x00"


def get_sv() -> "Iterator[tuple[bytes, bytes]]":
    src_addr = b"\x00\x30\xa7\x22\x8d\x5d"
    dst_addr = b"\x01\x0c\xcd\x04\x00\x01"
    sv_ether = b"\x88\xba"
    app_id = b"\x40\x00"
    length = b"\x00\x63"  # TODO calc?
    reserved = b"\x00\x00\x00\x00"
    sv_type = b"\x60"
    sv_len = b"\x59"  # TODO calc?
    num_asdu = b"\x80\x01\x01"
    seq_asdu_type = b"\xa2"
    seq_asdu_len = b"\x54"  # TODO calc?
    asdu_type = b"\x30"
    asdu_len = b"\x52"  # TODO calc?
    sv_id = b"\x80\x01\x32"
    conf_rev = b"\x83\x04\x00\x00\x00\x01"
    smp_synch = b"\x85\x01\x00"
    phs_meas_type_len = b"\x87\x40"
    for index, (i_as, i_bs, i_cs, v_as, v_bs, v_cs) in enumerate(read_sample()):
        i_ai, i_a = parse_sample(i_as)
        i_bi, i_b = parse_sample(i_bs)
        i_ci, i_c = parse_sample(i_cs)
        i_n = parse_neutral(i_ai + i_bi + i_ci)

        v_ai, v_a = parse_sample(v_as)
        v_bi, v_b = parse_sample(v_bs)
        v_ci, v_c = parse_sample(v_cs)
        v_n = parse_neutral(v_ai + v_bi + v_ci)
        smp_cnt = b"\x82\x02" + s_pack("!h", int(index))

        yield (
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
            + smp_synch,
            phs_meas_type_len + i_a + i_b + i_c + i_n + v_a + v_b + v_c + v_n,
        )
