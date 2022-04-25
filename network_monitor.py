#!/usr/bin/env python3
import argparse
from scapy.all import *
import time
import sys
import subprocess
import datetime
import yaml
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
    parser.add_argument(
        '--config', help="configuration file *.yaml", type=str,
        default='config.yaml')
    parser.add_argument("--log-level", help="Log level",
                        type=int, default=logging.INFO)
    parser.add_argument("--user", help="User to notify", type=str)

    args = parser.parse_args()

    # Merge in yaml config file. Commandline arguments take precedence.
    with open(args.config, 'r') as f:
        t_args = argparse.Namespace()
        yargs = yaml.load(f, Loader=yaml.FullLoader)
        t_args.__dict__.update(yargs)
        args = parser.parse_args(namespace=t_args)

    return args


class Pinger():
    def __init__(self):
        self._iface = ""
        self.update_default_iface()

    def update_default_iface(self):
        cmd = "ip -4 route show default"
        ret = subprocess.run(cmd.split(' '), stdout=subprocess.PIPE)
        if ret.returncode != 0:
            return

        s = str(ret.stdout)
        iface = s.split(' ')[4]
        if iface != self._iface:
            log.info("Updating interface to %s." % iface)
            self._iface = iface

    def ping1(self, ip):
        pkt = IP(dst=ip)/ICMP()/Raw(64*'B')
        ans, unans = sr(pkt, promisc=False, filter='icmp', iface=self._iface,
                        verbose=0, timeout=2)
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
        format='%(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')


class Notifier():
    NOTIFY_SEND = "/usr/bin/notify-send"

    def __init__(self, user):
        cmd = "id -u %s" % user
        ret = subprocess.run(cmd.split(' '), stdout=subprocess.PIPE)
        if ret.returncode != 0:
            raise Exception("%s failed" % cmd)
        cmd = "sudo -u %s" % user
        cmd += " DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%s/bus" % str(
            int(ret.stdout))
        cmd += " %s" % Notifier.NOTIFY_SEND
        self._prefix = cmd.split(' ')

    def notify(self, msg):
        cmd = self._prefix + ["\"%s\"" % msg]
        subprocess.run(cmd)


def main():
    args = _usage()
    setup_logging(args)
    log.info("Starting.")
    log.info(args)
    notifier = Notifier(args.user)
    pinger = Pinger()

    uptime = datetime.datetime.now()
    last_logged = datetime.datetime(1970, 1, 1)
    last_notify = datetime.datetime(1970, 1, 1)
    last_updated = datetime.datetime(1970, 1, 1)
    while True:
        s = pinger.ping1(args.dst_ip)
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
                if args.notify_interval and (
                        now - last_notify).total_seconds() > args.notify_interval:
                    notifier.notify(msg)
                    last_notify = datetime.datetime.now()
            if (now - last_updated).total_seconds() > 5:
                pinger.update_default_iface()
                last_updated = datetime.datetime.now()
        else:
            log.debug("Successfully reached destination.")
            uptime = datetime.datetime.now()
        time.sleep(1)


if __name__ == '__main__':
    main()
