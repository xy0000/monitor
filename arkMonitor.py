#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import logging
import json
import struct
import time
import socket
import commands
import argparse
import re


class Metric(object):

    def __init__(self, host, key, value, clock=None):

        self.host = host

        self.key = key

        self.value = value

        self.clock = clock

    def __repr__(self):

        result = None

        if self.clock is None:

            result = 'Metric(%r, %r, %r)' % (self.host, self.key, self.value)

        else:

            result = 'Metric(%r, %r, %r, %r)' % (self.host, self.key, self.value, self.clock)

        return result


def send_to_zabbix(metrics, zabbix_host='127.0.0.1', zabbix_port=10051, timeout=15):
    """Send set of metrics to Zabbix server."""
    j = json.dumps
    # Zabbix has very fragile JSON parser, and we cannot use json to dump whole packet
    metrics_data = []
    for m in metrics:
        print m
        clock1 = m.clock or time.time()
        clock = m.clock or ('%d' % time.time())
        metrics_data.append(
            ('{"host":%s,"key":%s,"value":%s,"clock":%s}') % (j(m.host), j(m.key), j(m.value), j(clock)))
    json_data = ('{"request":"sender data","data":[%s]}') % (','.join(metrics_data))
    data_len = struct.pack('<Q', len(json_data))
    packet = 'ZBXD\1' + data_len + json_data
    try:
        zabbix = socket.socket()
        zabbix.connect((zabbix_host, zabbix_port))
        zabbix.settimeout(timeout)
        # send metrics to zabbix
        zabbix.sendall(packet)
        # get response header from zabbix
        # resp_hdr = _recv_all(zabbix, 13)
        resp_hdr = zabbix.recv(13)
        if not resp_hdr.startswith('ZBXD') or len(resp_hdr) != 5:
            logger.error('Wrong zabbix response')
            return False
        return True
    except socket.timeout, e:
        logger.error("zabbix timeout: " + str(e))
        return False
    except Exception, e:
        logger.exception('Error while sending data to Zabbix: ' + str(e))
        return False
    finally:
        zabbix.close()


def getKey(settings, type, iterm):

    try:
        key = settings[type][iterm]
    except Exception as e:
        logger.error("do not have key \"%s\" in settings.json will set to None." % e)
        key = "None_%s" % iterm

    return key


def containerStatus(statusList, settings, host, containers):

    for container in containers:
        key = getKey(settings, "containerCheck", container)
        cmd = "docker inspect --format='{{.State.Running}}' " + container
        code, out = commands.getstatusoutput(cmd)

        if code != 0:
            value = 2
            logger.error("exec " + cmd + " failed " + out)
        else:
            if out == "true":
                value = 0
            elif out == "false":
                value = 1
            else:
                logger.error("unknown command out put: " + out)
                value = 3

        statusList.append(Metric(host, key, value))
    return


def procStatus(statusList, settings, host, procs):

    mainName = sys.argv[0].split("/")[-1]

    for user_proc_num in procs:

        a = []

        user, proc, num = user_proc_num.split(":")
        key = getKey(settings, "procCheck", proc)
        user = "^" + user + " "
        cmd = "ps -ef"
        code, out = commands.getstatusoutput(cmd)

        if code != 0:
            value = 2
            logger.error("exec " + cmd + " failed " + out)

        else:

            for i in out.split("\n"):
                if re.search(user, i):
                    if  re.search(proc, i):
                        if not re.search(mainName, i):
                            a.append(i)

            count = len(a)

            if int(count) == int(num):
                value = 0
            elif int(count) > int(num):
                value = 1
            elif int(count) < int(num):
                value = 2
            else:
                value = 3

        statusList.append(Metric(host, key, value))
    return


def portStatus(statusList, settings, ip, ports):

    for port in ports:

        key = getKey(settings, "portCheck", port)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)

        try:
            s.connect((ip, int(port)))
            s.close()
            value = 0
        except socket.timeout as e:
            logger.error("connect to %s:%s failed, %s" % (ip, port, e))
            value = 2
        except socket.error as e:
            logger.error("connect to %s:%s failed, %s" % (ip ,port, e))
            value = 1
        except Exception as e:
            logger.error(e)
            value = 3
        statusList.append(Metric(host, key, value))

    return


if __name__ == "__main__":

    logdir = os.path.dirname(os.path.abspath(sys.argv[0])) + "/" + "log"

    if not os.path.isdir(logdir):
        os.makedirs(logdir)

    logFile = logdir + "/" + "arkMonitor.log"

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S',
                        filename=logFile,
                        filemode='a')

    logger = logging.getLogger('arkLog')

    filePath = os.path.dirname(os.path.abspath(sys.argv[0]))
    fileName = "settings.json"
    file = filePath + "/" + fileName
    try:
        f = open(file)
        settings = json.load(f)
    except Exception as e:
        logger.error(e)
        print(e)
        sys.exit(1)

    # print(json.dumps(settings, indent=4))

    parse = argparse.ArgumentParser()
    parse.add_argument('-H', '--host', dest='host', action='store', help='host IP', default=None)
    parse.add_argument('-p', '--ports', dest='ports', action='store', help='listening port list', default=None)
    parse.add_argument('-c', '--containers', dest='containers', action='store', help='containers list', default=None)
    parse.add_argument('-P', '--procs', dest="procs", action='store', help='proc name list', default=None)
    args = parse.parse_args()

    zabbix_host = '40.2.214.18'  # Zabbix Server IP
    zabbix_port = 10051  # Zabbix Server Port

    allStatus = []

    if args.host == None:
        logger.error("No specified host IP.")

    host = args.host

    if args.containers != None:
        containerStatus(allStatus, settings, host, args.containers.replace(" ", "").split(","))

    if args.procs != None:
        procStatus(allStatus, settings, host, args.procs.replace(" ", "").split(","))

    if args.ports != None:
        portStatus(allStatus, settings, host, args.ports.replace(" ", "").split(","))


    if len(allStatus) == 0:
        logger.error("no Metrics.")
        sys.exit(1)

    print(allStatus)
    # send_to_zabbix(allStatus, zabbix_host=zabbix_host)