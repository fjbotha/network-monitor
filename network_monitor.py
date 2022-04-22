#!/usr/bin/env python3
import argparse
from scapy.all import *
import time
import sys
import subprocess
import datetime
import logging
log = None


def _usage():
    parser = argparse.ArgumentParser(description="ping-based network monitor")
    parser.add_argument("-d", "--dst-ip", help="Destination IP",
                        type=str, default="8.8.8.8")
    parser.add_argument(
        "--allowable-downtime",
        help="Time duration in seconds for which connectivity loss is not considered an error",
        type=int, default=5)
    parser.add_argument(
        "--error-log-interval",
        help="Minimum duration in seconds before which subsequent error messages will be logged",
        type=int, default=5)
    parser.add_argument(
        "--notify-interval",
        help="Minimum duration in seconds before which subsequent graphical notifications will be issued (0 == disabled)",
        type=int, default=30)
    parser.add_argument(
        "-s", "--silent", help="Do not issue audible beeps when alerting",
        action='store_true')
    parser.add_argument("--log-level", help="Log level",
                        type=int, default=logging.INFO)
    return parser


def ping1(ip):
    pkt = IP(dst=ip)/ICMP()/Raw(64*'B')
    ans, unans = sr(pkt, promisc=False, filter='icmp', verbose=0, timeout=2)
    if len(ans) > 0:
        try:
            rx = ans[0][1]
            tx = ans[0][0]
            return rx.time-tx.sent_time
        except Exception as e:
            log.critical("Unexpected return:")
            log.critical(ans)
            pass

    return None


def beep():
    for i in range(0, 10):
        print('\r\a', end='', flush=True)
        time.sleep(50e-3)


def setup_logging(args):
    global log
    log = logging.getLogger("Network-Monitor " + args.dst_ip)
    logging.basicConfig(
        level=args.log_level,
        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')


def main():
    args = _usage().parse_args()
    setup_logging(args)
    log.info("Starting.")
    log.info(args)

    uptime = datetime.datetime.now()
    last_logged = datetime.datetime(1970, 1, 1)
    last_notify = datetime.datetime(1970, 1, 1)
    while True:
        s = ping1(args.dst_ip)
        if s is None:
            if not args.silent:
                beep()
            now = datetime.datetime.now()
            offline_duration = now - uptime
            delta = offline_duration.total_seconds()
            if delta > args.allowable_downtime:
                if (now - last_logged).total_seconds() > args.error_log_interval:
                    msg = "Network monitor: Offline for %.1f seconds." % delta
                    log.error(msg)
                    last_logged = datetime.datetime.now()
                if (now - last_notify).total_seconds() > args.notify_interval:
                    subprocess.run(["./notify_send.sh", msg])
                    last_notify = datetime.datetime.now()
        else:
            log.debug("Successfully reached destination.")
            uptime = datetime.datetime.now()
        time.sleep(1)


if __name__ == '__main__':
    main()
