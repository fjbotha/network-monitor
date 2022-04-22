#!/usr/bin/env python3
import argparse
from scapy.all import *
import time
import sys


def ping1(ip):
    pkt = IP(dst=ip)/ICMP()/Raw(64*'B')
    ans, unans = sr(pkt, filter='icmp', verbose=0, timeout=2)
    if len(ans) > 0:
        try:
            rx = ans[0][1]
            tx = ans[0][0]
            return rx.time-tx.sent_time
        except:
            print(ans)
            pass

    return None


def beep():
    for i in range(0, 10):
        print('\a', flush=True)
        time.sleep(50e-3)


def _usage():
    parser = argparse.ArgumentParser(description="ping-based network monitor")
    parser.add_argument("-d", "--dst-ip", help="Destination IP",
                        type=str, default="8.8.8.8")
    return parser


def main():
    args = _usage().parse_args()
    while True:
        s = ping1(args.dst_ip)
        if s is None:
            beep()
        time.sleep(1)


if __name__ == '__main__':
    main()
