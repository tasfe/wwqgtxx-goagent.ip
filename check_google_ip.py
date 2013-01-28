#!/usr/bin/env python
# coding:utf-8
# by:wwqgtxx

import sys
import os
import re

try:
    import gevent
    import gevent.monkey
    import gevent.timeout
    gevent.monkey.patch_all()
except ImportError:
    if os.name == 'nt':
        sys.stderr.write('WARNING: python-gevent not installed. `https://github.com/SiteSupport/gevent/downloads`\n')
    else:
        sys.stderr.write('WARNING: python-gevent not installed. `curl -k -L http://git.io/I9B7RQ|sh`\n')
    sys.exit(-1)

import ssl
import socket
import ConfigParser

__config__  = 'proxy.ini'
__file__    = 'check_google_ip.py'



class Common(object):

    def __init__(self):
        """load config from proxy.ini"""
        ConfigParser.RawConfigParser.OPTCRE = re.compile(r'(?P<option>[^=\s][^=]*)\s*(?P<vi>[=])\s*(?P<value>.*)$')
        self.CONFIG = ConfigParser.ConfigParser()
        self.CONFIG.read(getfile( __config__))
        self.IPS = []
        self.filename = 'ip.txt'

common = Common()


class FilesUntil(object):
    def getfile(filename):
        global __file__
        __file__ = os.path.abspath(__file__)
        if os.path.islink(__file__):
            __file__ = getattr(os, 'readlink', lambda x:x)(__file__)
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(os.path.dirname(__file__), filename)

    def ifhasfile():
        if os.path.isfile(getfile(common.filename)):
            os.remove(getfile(common.filename)) 
		
    def write(str_ips):
        f = open(getfile(common.filename),'a+') 
        print str_ips
        f.write(str_ips)
        f.close()

    def getln():
        if os.name == 'nt':
            return '\r\n'
        else:
            return '\n'

    def writeln():
        write(getln())
	
    def writeline():
        writeln()
        write('----------------------------------------------------')
        writeln()
	
    def writeip(ip):
        write(ip)
        common.IPS.append(ip)
		
		
fileuntil = FilesUntil()


class Check_ip(object):
    ips = []
    def check_ip(ip):
        try:
            with gevent.timeout.Timeout(5):
                sock = socket.create_connection((ip, 443))
                ssl_sock = ssl.wrap_socket(sock)
                peer_cert = ssl_sock.getpeercert(True)
                if '.google.com' in peer_cert:
                    print ip
                    self.ips.append(ip)
                    #print self.ips
        except gevent.timeout.Timeout as e:
            pass
        except Exception as e:
            pass
    def run(filename,ip_head,ip_start,ip_end):
        for a in xrange(ip_start,(ip_end+1)):
            global ips
            str_a = '%d' % a
            greenlets = [gevent.spawn(check_ip, ip_head+str_a+'.%d' % i)for i in xrange(1, 256)]
            gevent.joinall(greenlets)
            str_ips = ''
            print getln()
            if self.ips!=[]:
                for item in self.ips:
                    str_ips = str_ips+item+'|'
                fileuntil.write(filename,str_ips)
                self.ips = []
            else:
                print ip_head+str_a+'.* is no useable ip.'
            print getln()
			
check_ip = Check_ip()


def main():
    need_google_hk = False
    fileuntil.ifhasfile(filename)
    fileuntil.writeline(filename)
    fileuntil.write(filename,'Google Cn Ip:')
    fileuntil.writeline(filename)
    check_ip.run(filename,'203.208.',36,37)
    if need_google_hk:
        fileuntil.writeline(filename)
        fileuntil.write(filename,'Google Hk Ip:')
        fileuntil.writeline(filename)
        check_ip.run(filename,'74.125.',0,255)

if __name__ == '__main__':
    main()