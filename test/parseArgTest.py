#!/usr/bin/python
# -*- coding: utf-8 -*-

# TODO 检查是否为合法IP地址
# TODO 检查端口合法性
# TODO python管理进程

# TODO 指定用户的进程数
# TODO 检查进程数的函数是否需要修改，改为出入 shell 命令的方式
# TODO 并添加指定用户的功能

# TODO 重新定义日志位置
# TODO 若日志目录不存在，则创建目录


import argparse

a = []

parse = argparse.ArgumentParser()

parse.add_argument("-H", "--host", dest='host', action='store', help='host IP', default=None)
parse.add_argument("-p", "--port", dest='port', action='store', help='listening port', default=None, type=int)
parse.add_argument('-P', "--proc", dest="proc", action='store', help='proc name', default=None)

args = parse.parse_args()

print(args)

print(args.host, args.port, args.proc)
print(args.host, type(args.host))
print(args.port, type(args.port))

if args.proc == None:
    print(args.proc)
else:
    print("%s not None" % args.proc)

def test(a):
    a.append("sjief")

test(a)

print(a)