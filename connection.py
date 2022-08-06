#!/usr/bin/python3
import libvirt
import sys
class lvconn:
    conn=None
    def connect(self):
        try:
            self.conn = libvirt.open("qemu:///system")
        except libvirt.libvirtError as e:
            print(repr(e), file=sys.stderr)
            exit(1)

    def __init__(self):
        if self.conn == None:
            self.connect()