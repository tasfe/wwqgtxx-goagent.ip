#!/usr/bin/env python
# coding:utf-8
# Based on GAppProxy 2.0.0 by Du XiaoGang <dugang@188.com>
# Based on WallProxy 0.4.0 by Hust Moon <www.ehust@gmail.com>
# Contributor:
#      Phus Lu        <phus.lu@gmail.com>
#      Hewig Xu       <hewigovens@gmail.com>
#      Ayanamist Yang <ayanamist@gmail.com>
#      Max Lv         <max.c.lv@gmail.com>
#      AlsoTang       <alsotang@gmail.com>
#      Yonsm          <YonsmGuo@gmail.com>
#      Ming Bai       <mbbill@gmail.com>
#      Bin Yu         <yubinlove1991@gmail.com>

__version__ = '2.1.11'
__config__  = 'proxy.ini'
__bufsize__ = 1024*1024

import sys
import os

try:
    import gevent
    import gevent.queue
    import gevent.monkey
    import gevent.coros
    import gevent.server
    import gevent.pool
    import gevent.event
    import gevent.timeout
    gevent.monkey.patch_all(dns=gevent.version_info[0]>=1)
except ImportError:
    if os.name == 'nt':
        sys.stderr.write('WARNING: python-gevent not installed. `https://github.com/SiteSupport/gevent/downloads`\n')
    else:
        sys.stderr.write('WARNING: python-gevent not installed. `curl -k -L http://git.io/I9B7RQ|sh`\n')
    import Queue
    import thread
    import threading
    import SocketServer

    def GeventImport(name):
        import sys
        sys.modules[name] = type(sys)(name)
        return sys.modules[name]
    def GeventSpawn(target, *args, **kwargs):
        return thread.start_new_thread(target, args, kwargs)
    def GeventSpawnLater(seconds, target, *args, **kwargs):
        def wrap(*args, **kwargs):
            import time
            time.sleep(seconds)
            return target(*args, **kwargs)
        return thread.start_new_thread(wrap, args, kwargs)
    class GeventServerStreamServer(SocketServer.ThreadingTCPServer):
        allow_reuse_address = True
        def finish_request(self, request, client_address):
            self.RequestHandlerClass(request, client_address)
    class GeventServerDatagramServer(SocketServer.ThreadingUDPServer):
        allow_reuse_address = True
        def __init__(self, server_address, *args, **kwargs):
            SocketServer.ThreadingUDPServer.__init__(self, server_address, GeventServerDatagramServer.RequestHandlerClass, *args, **kwargs)
            self._writelock = threading.Semaphore()
        def sendto(self, *args):
            self._writelock.acquire()
            try:
                self.socket.sendto(*args)
            finally:
                self._writelock.release()
        @staticmethod
        def RequestHandlerClass((data, server_socket), client_addr, server):
            return server.handle(data, client_addr)
        def handle(self, data, address):
            raise NotImplemented()
    class GeventPoolPool(object):
        def __init__(self, size):
            self._lock = threading.Semaphore(size)
        def __target_wrapper(self, target, args, kwargs):
            t = threading.Thread(target=target, args=args, kwargs=kwargs)
            try:
                t.start()
                t.join()
            except Exception as e:
                logging.error('threading.Thread target=%r error:%s', target, e)
            finally:
                self._lock.release()
        def spawn(self, target, *args, **kwargs):
            self._lock.acquire()
            return thread.start_new_thread(self.__target_wrapper, (target, args, kwargs))

    gevent        = GeventImport('gevent')
    gevent.queue  = GeventImport('gevent.queue')
    gevent.coros  = GeventImport('gevent.coros')
    gevent.server = GeventImport('gevent.server')
    gevent.pool   = GeventImport('gevent.pool')

    gevent.queue.Queue           = Queue.Queue
    gevent.queue.Empty           = Queue.Empty
    gevent.coros.Semaphore       = threading.Semaphore
    gevent.getcurrent            = threading.currentThread
    gevent.spawn                 = GeventSpawn
    gevent.spawn_later           = GeventSpawnLater
    gevent.server.StreamServer   = GeventServerStreamServer
    gevent.server.DatagramServer = GeventServerDatagramServer
    gevent.pool.Pool             = GeventPoolPool

    del GeventImport, GeventSpawn, GeventSpawnLater, GeventServerStreamServer, GeventServerDatagramServer, GeventPoolPool

import collections
import errno
import time
import cStringIO
import struct
import re
import zlib
import random
import base64
import urlparse
import socket
import ssl
import select
import traceback
import hashlib
import fnmatch
import ConfigParser
import httplib
import urllib2
import heapq
import threading
try:
    import ctypes
except ImportError:
    ctypes = None
try:
    import OpenSSL
except ImportError:
    OpenSSL = None

class Logging(type(sys)):
    CRITICAL = 50
    FATAL = CRITICAL
    ERROR = 40
    WARNING = 30
    WARN = WARNING
    INFO = 20
    DEBUG = 10
    NOTSET = 0
    def __init__(self, *args, **kwargs):
        self.level = self.__class__.INFO
        if self.level > self.__class__.DEBUG:
            self.debug = self.dummy
        self.__write = __write = sys.stdout.write
        if os.name == 'nt':
            SetConsoleTextAttribute = ctypes.windll.kernel32.SetConsoleTextAttribute
            GetStdHandle = ctypes.windll.kernel32.GetStdHandle
            self.__set_error_color = lambda:SetConsoleTextAttribute(GetStdHandle(-11), 0x04)
            self.__set_warning_color = lambda:SetConsoleTextAttribute(GetStdHandle(-11), 0x06)
            self.__reset_color = lambda:SetConsoleTextAttribute(GetStdHandle(-11), 0x07)
        elif os.name == 'posix':
            self.__set_error_color = lambda:__write('\033[31m')
            self.__set_warning_color = lambda:__write('\033[33m')
            self.__reset_color = lambda:__write('\033[0m')
        else:
            self.__set_error_color = lambda:None
            self.__set_warning_color = lambda:None
            self.__reset_color = lambda:None
    @classmethod
    def getLogger(cls, *args, **kwargs):
        return cls(*args, **kwargs)
    def basicConfig(self, *args, **kwargs):
        self.level = kwargs.get('level', self.__class__.INFO)
        if self.level > self.__class__.DEBUG:
            self.debug = self.dummy
    def log(self, level, fmt, *args, **kwargs):
        self.__write('%s - - [%s] %s\n' % (level, time.ctime()[4:-5], fmt%args))
    def dummy(self, *args, **kwargs):
        pass
    def debug(self, fmt, *args, **kwargs):
        self.log('DEBUG', fmt, *args, **kwargs)
    def info(self, fmt, *args, **kwargs):
        self.log('INFO', fmt, *args)
    def warning(self, fmt, *args, **kwargs):
        self.__set_warning_color()
        self.log('WARNING', fmt, *args, **kwargs)
        self.__reset_color()
    def warn(self, fmt, *args, **kwargs):
        self.warning(fmt, *args, **kwargs)
    def error(self, fmt, *args, **kwargs):
        self.__set_error_color()
        self.log('ERROR', fmt, *args, **kwargs)
        self.__reset_color()
    def exception(self, fmt, *args, **kwargs):
        self.error(fmt, *args, **kwargs)
        traceback.print_exc(file=sys.stderr)
    def critical(self, fmt, *args, **kwargs):
        self.__set_error_color()
        self.log('CRITICAL', fmt, *args, **kwargs)
        self.__reset_color()
logging = sys.modules['logging'] = Logging('logging')

class Common(object):
    """Global Config Object"""

    def __init__(self):
        """load config from proxy.ini"""
        ConfigParser.RawConfigParser.OPTCRE = re.compile(r'(?P<option>[^=\s][^=]*)\s*(?P<vi>[=])\s*(?P<value>.*)$')
        self.CONFIG = ConfigParser.ConfigParser()
        self.CONFIG.read(os.path.join(os.path.dirname(__file__), __config__))

        self.LISTEN_IP            = self.CONFIG.get('listen', 'ip')
        self.LISTEN_PORT          = self.CONFIG.getint('listen', 'port')
        self.LISTEN_VISIBLE       = self.CONFIG.getint('listen', 'visible')
        self.LISTEN_DEBUGINFO     = self.CONFIG.getint('listen', 'debuginfo') if self.CONFIG.has_option('listen', 'debuginfo') else 0

        self.GAE_APPIDS           = re.findall('[\w\-\.]+', self.CONFIG.get('gae', 'appid').replace('.appspot.com', ''))
        self.GAE_PASSWORD         = self.CONFIG.get('gae', 'password').strip()
        self.GAE_PATH             = self.CONFIG.get('gae', 'path')
        self.GAE_PROFILE          = self.CONFIG.get('gae', 'profile')
        self.GAE_CRLF             = self.CONFIG.getint('gae', 'crlf')

        self.PAC_ENABLE           = self.CONFIG.getint('pac','enable')
        self.PAC_IP               = self.CONFIG.get('pac','ip')
        self.PAC_PORT             = self.CONFIG.getint('pac','port')
        self.PAC_FILE             = self.CONFIG.get('pac','file').lstrip('/')
        self.PAC_GFWLIST          = self.CONFIG.get('pac', 'gfwlist')

        self.PAAS_ENABLE           = self.CONFIG.getint('paas', 'enable')
        self.PAAS_LISTEN           = self.CONFIG.get('paas', 'listen')
        self.PAAS_PASSWORD         = self.CONFIG.get('paas', 'password') if self.CONFIG.has_option('paas', 'password') else ''
        self.PAAS_FETCHSERVER      = self.CONFIG.get('paas', 'fetchserver')

        self.PROXY_ENABLE         = self.CONFIG.getint('proxy', 'enable')
        self.PROXY_AUTODETECT     = self.CONFIG.getint('proxy', 'autodetect') if self.CONFIG.has_option('proxy', 'autodetect') else 0
        self.PROXY_HOST           = self.CONFIG.get('proxy', 'host')
        self.PROXY_PORT           = self.CONFIG.getint('proxy', 'port')
        self.PROXY_USERNAME       = self.CONFIG.get('proxy', 'username')
        self.PROXY_PASSWROD       = self.CONFIG.get('proxy', 'password')

        if not self.PROXY_ENABLE and self.PROXY_AUTODETECT:
            try:
                proxies = (x for x in urllib2.build_opener().handlers if isinstance(x, urllib2.ProxyHandler)).next().proxies
                proxy = proxies.get('https') or proxies.get('http') or ''
                if self.LISTEN_IP not in proxy:
                    scheme, username, password, address = urllib2._parse_proxy(proxy)
                    proxyhost, _, proxyport = address.rpartition(':')
                    self.PROXY_ENABLE   = 1
                    self.PROXY_USERNAME = username
                    self.PROXY_PASSWROD = password
                    self.PROXY_HOST     = proxyhost
                    self.PROXY_PORT     = int(proxyport)
            except StopIteration:
                pass
        if self.PROXY_ENABLE:
            self.GOOGLE_MODE = 'https'
            self.proxy = 'https://%s:%s@%s:%d' % (self.PROXY_USERNAME or '' , self.PROXY_PASSWROD or '', self.PROXY_HOST, self.PROXY_PORT)
        else:
            self.proxy = ''

        self.GOOGLE_MODE          = self.CONFIG.get(self.GAE_PROFILE, 'mode')
        self.GOOGLE_WINDOW        = self.CONFIG.getint(self.GAE_PROFILE, 'window') if self.CONFIG.has_option(self.GAE_PROFILE, 'window') else 4
        self.GOOGLE_HOSTS         = tuple(x for x in self.CONFIG.get(self.GAE_PROFILE, 'hosts').split('|') if x)
        self.GOOGLE_SITES         = tuple(x for x in self.CONFIG.get(self.GAE_PROFILE, 'sites').split('|') if x)
        self.GOOGLE_FORCEHTTPS    = tuple('http://'+x for x in self.CONFIG.get(self.GAE_PROFILE, 'forcehttps').split('|') if x)
        self.GOOGLE_WITHGAE       = set(x for x in self.CONFIG.get(self.GAE_PROFILE, 'withgae').split('|') if x)

        self.AUTORANGE_HOSTS      = tuple(self.CONFIG.get('autorange', 'hosts').split('|'))
        self.AUTORANGE_HOSTS_TAIL = tuple(x.rpartition('*')[2] for x in self.AUTORANGE_HOSTS)
        self.AUTORANGE_MAXSIZE    = self.CONFIG.getint('autorange', 'maxsize')
        self.AUTORANGE_WAITSIZE   = self.CONFIG.getint('autorange', 'waitsize')
        self.AUTORANGE_BUFSIZE    = self.CONFIG.getint('autorange', 'bufsize')
        self.AUTORANGE_THREADS    = self.CONFIG.getint('autorange', 'threads')

        self.FETCHMAX_LOCAL       = self.CONFIG.getint('fetchmax', 'local') if self.CONFIG.get('fetchmax', 'local') else 3
        self.FETCHMAX_SERVER      = self.CONFIG.get('fetchmax', 'server')

        if self.CONFIG.has_section('crlf'):
            # XXX, cowork with GoAgentX
            self.CRLF_ENABLE          = self.CONFIG.getint('crlf', 'enable')
            self.CRLF_DNSSERVER       = self.CONFIG.get('crlf', 'dns')
            self.CRLF_SITES           = tuple(self.CONFIG.get('crlf', 'sites').split('|'))
        else:
            self.CRLF_ENABLE          = 0

        if self.CONFIG.has_section('dns'):
            self.DNS_ENABLE = self.CONFIG.getint('dns', 'enable')
            self.DNS_LISTEN = self.CONFIG.get('dns', 'listen')
            self.DNS_REMOTE = self.CONFIG.get('dns', 'remote')
            self.DNS_CACHESIZE = self.CONFIG.getint('dns', 'cachesize')
            self.DNS_TIMEOUT   = self.CONFIG.getint('dns', 'timeout')
        else:
            self.DNS_ENABLE = 0

        if self.CONFIG.has_section('socks5'):
            self.SOCKS5_ENABLE           = self.CONFIG.getint('socks5', 'enable')
            self.SOCKS5_LISTEN           = self.CONFIG.get('socks5', 'listen')
            self.SOCKS5_PASSWORD         = self.CONFIG.get('socks5', 'password')
            self.SOCKS5_FETCHSERVER      = self.CONFIG.get('socks5', 'fetchserver')
        else:
            self.SOCKS5_ENABLE           = 0

        self.USERAGENT_ENABLE     = self.CONFIG.getint('useragent', 'enable')
        self.USERAGENT_STRING     = self.CONFIG.get('useragent', 'string')

        self.LOVE_ENABLE          = self.CONFIG.getint('love','enable')
        self.LOVE_TIMESTAMP       = self.CONFIG.get('love', 'timestamp')
        self.LOVE_TIP             = [re.sub(r'\\u([0-9a-fA-F]{4})', lambda m:unichr(int(m.group(1), 16)), x) for x in self.CONFIG.get('love','tip').split('|')]

        self.HOSTS                = dict((k, tuple(v.split('|')) if v else tuple()) for k, v in self.CONFIG.items('hosts'))

        #random.shuffle(self.GAE_APPIDS)
        self.FIRST_APPID = self.GAE_APPIDS[0]
        self.NEED_SWITCH   = True
        self.FIRST_SWITCH  = True
        self.GAE_FETCHSERVER = '%s://%s.appspot.com%s?' % (self.GOOGLE_MODE, self.GAE_APPIDS[0], self.GAE_PATH)

    def info(self):
        info = ''
        info += '------------------------------------------------------\n'
        info += 'GoAgent Version    : %s (python/%s gevent/%s pyopenssl/%s)\n' % (__version__, sys.version.partition(' ')[0], getattr(gevent, '__version__', None), (OpenSSL.version.__version__ if OpenSSL else 'Disabled'))
        info += 'Listen Address     : %s:%d\n' % (self.LISTEN_IP,self.LISTEN_PORT)
        info += 'Local Proxy        : %s:%s\n' % (self.PROXY_HOST, self.PROXY_PORT) if self.PROXY_ENABLE else ''
        info += 'Debug INFO         : %s\n' % self.LISTEN_DEBUGINFO if self.LISTEN_DEBUGINFO else ''
        info += 'GAE Mode           : %s\n' % self.GOOGLE_MODE
        info += 'GAE Profile        : %s\n' % self.GAE_PROFILE
        info += 'GAE APPID          : %s\n' % '|'.join(self.GAE_APPIDS)
        if common.PAAS_ENABLE:
            info += 'PAAS Listen        : %s\n' % common.PAAS_LISTEN
            info += 'PAAS FetchServer   : %s\n' % common.PAAS_FETCHSERVER
        if common.DNS_ENABLE:
            info += 'DNS Listen        : %s\n' % common.DNS_LISTEN
            info += 'DNS Remote        : %s\n' % common.DNS_REMOTE
        if common.SOCKS5_ENABLE:
            info += 'SOCKS5 Listen      : %s\n' % common.SOCKS5_LISTEN
            info += 'SOCKS5 FetchServer : %s\n' % common.SOCKS5_FETCHSERVER
        if common.PAC_ENABLE:
            info += 'Pac Server         : http://%s:%d/%s\n' % (self.PAC_IP,self.PAC_PORT,self.PAC_FILE)
        if common.CRLF_ENABLE:
            #http://www.acunetix.com/websitesecurity/crlf-injection.htm
            info += 'CRLF Injection     : %s\n' % '|'.join(self.CRLF_SITES)
        info += '------------------------------------------------------\n'
        return info


