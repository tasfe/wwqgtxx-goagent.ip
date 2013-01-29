#!/usr/bin/env python
# coding:utf-8
# by:wwqgtxx,phus

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

__config__   = 'proxy.ini'
__file__     = 'check_google_ip.py'
__filename__ = 'ip.txt'



class Common(object):

    def __init__(self):
        """load config from proxy.ini"""
        ConfigParser.RawConfigParser.OPTCRE = re.compile(r'(?P<option>[^=\s][^=]*)\s*(?P<vi>[=])\s*(?P<value>.*)$')
        self.CONFIG = ConfigParser.ConfigParser()
        self.CONFIG.read(os.path.join(os.path.dirname(__file__), __config__))
        self.IPS = []


    def getfile(self,filename):
        global __file__
        __file__ = os.path.abspath(__file__)
        if os.path.islink(__file__):
            __file__ = getattr(os, 'readlink', lambda x:x)(__file__)
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(os.path.dirname(__file__), filename)

    def ifhasfile(self):
        if os.path.isfile(self.getfile(__filename__)):
            os.remove(self.getfile(__filename__)) 
		
    def write(self,str_ips):
        f = open(self.getfile(__filename__),'a+') 
        print str_ips
        f.write(str_ips)
        f.close()

    def getln(self):
        if os.name == 'nt':
            return '\r\n'
        else:
            return '\n'

    def writeln(self):
        self.write(self.getln())
	
    def writeline(self):
        self.writeln()
        self.write('----------------------------------------------------')
        self.writeln()
	
    def writeip(self,ip):
        self.write(ip)
        common.IPS.append(ip)

    def writeips(self,section, option):
        str_ips = ''
        if self.IPS!=[]:
            for item in self.IPS:
                str_ips = str_ips+item
            print str_ips
            self.writeconfig(section, option,str_ips)
            self.IPS = []

    def writeconfig(self,section, option,str):
        self.CONFIG.set(section,option,str)
        f = open(self.getfile(__config__),'w') 
        self.CONFIG.write(f)
        f.close()
    
    def getconfig(self,section, option):
        return self.CONFIG.get(section, option)
		
		
common = Common()


class Check_ip(object):
    ips = []
    def check_ip(self,ip):
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
    def run(self,filename,ip_head,ip_start,ip_end):
        for a in xrange(ip_start,(ip_end+1)):
            global ips
            str_a = '%d' % a
            greenlets = [gevent.spawn(self.check_ip, ip_head+str_a+'.%d' % i)for i in xrange(1, 256)]
            gevent.joinall(greenlets)
            str_ips = ''
            print common.getln()
            if self.ips!=[]:
                for item in self.ips:
                    str_ips = str_ips+item+'|'
                common.writeip(str_ips)
                self.ips = []
            else:
                print ip_head+str_a+'.* is no useable ip.'
            print common.getln()
			
check_ip = Check_ip()


def main():
    print '------------------------------------------------------ \n Google Cn Ip Getter \n by wwqgtxx \n------------------------------------------------------ \n '
    need_google_hk = False
    common.ifhasfile()
    common.writeline()
    common.write('Google Cn Ip:')
    common.writeline()
    common.writeconfig('google_cn','hosts','')
    check_ip.run(__filename__,'203.208.',46,47)
    common.writeips('google_cn','hosts')
    if common.getconfig('google_cn','hosts') == '' :
        print 'Can\'t Find Google Cn Ip,Change To Google_hk'
        common.writeconfig('gae','profile','google_hk')
    else :
        common.writeconfig('gae','profile','google_cn')
        print 'Find Google Cn Ip Successful,Change To Google_cn'
    if need_google_hk:
        common.writeline()
        common.write('Google Hk Ip:')
        common.writeline()
        check_ip.run(__filename__,'74.125.',0,255)
        common.writeconfig('google_hk','hosts')
    print '------------------------------------------------------ \n Google Cn Ip Getter \n by wwqgtxx \n------------------------------------------------------ \n '

if __name__ == '__main__':
    main()