from socket import AF_PACKET, SOCK_RAW, socket
from sys import argv

from pysv.sv import DEFAULT_PATH, SamplesSynchronized, SVConfig, generate_sv_from
from pysv.utils import usleep


def run(interface: str, sv_config: "SVConfig") -> None:
    with socket(AF_PACKET, SOCK_RAW, 0xBA88) as nic:
        nic.bind((interface, 0))

        for time2sleep, _smp_cnt, sv in generate_sv_from(DEFAULT_PATH, sv_config):
            usleep(time2sleep)
            nic.sendall(sv)


if __name__ == "__main__":
    sv_config = SVConfig(
        dst_mac="01:0c:cd:04:00:00", src_mac="0030a7228d5d", app_id="4000", sv_id="4000", conf_rev=1,
        smp_sync=SamplesSynchronized.GLOBAL,
    )
    run(argv[1], sv_config)
