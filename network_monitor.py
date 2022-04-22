#!/usr/bin/env python3
import argparse
from scapy.all import *
import time
import sys
import subprocess
import datetime
#from gi.repository import Notify


def _usage():
    parser = argparse.ArgumentParser(description="ping-based network monitor")
    parser.add_argument("-d", "--dst-ip", help="Destination IP",
                        type=str, default="8.8.8.8")
    return parser


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
        print('\r\a', end='', flush=True)
        time.sleep(50e-3)


def main():
    args = _usage().parse_args()
    #Notify.init('Network Monitor')

    uptime = datetime.datetime.now()
    last_notify = datetime.datetime(1970, 1, 1)
    while True:
        s = ping1(args.dst_ip)
        if s is None:
            beep()
            now = datetime.datetime.now()
            offline_duration = now - uptime
            delta = offline_duration.total_seconds()
            if delta > 1:
                if (now - last_notify).total_seconds() > 30:
                    msg = "Network monitor: Offline for %.1f seconds." % delta
                    print(msg)
                    # notifier = Notify.Notification.new(msg)
                    # notifier.show()
                    subprocess.run(["./notify_send.sh", msg])
                    last_notify = datetime.datetime.now()
        else:
            uptime = datetime.datetime.now()
        time.sleep(1)


if __name__ == '__main__':
    main()
