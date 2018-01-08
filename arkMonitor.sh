#!/usr/bin/env bash

sudo arkMonitor.py -H "127.0.0.1" -c "ovs, vlan" -P "root:mysql:1, mysql:mysql:1" -p "8080, 8081, 3306"
