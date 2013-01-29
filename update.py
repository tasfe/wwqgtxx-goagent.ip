import httplib
import check_google_ip
from check_google_ip import common

things = ''
conn   = None

def get(ip):
    conn = httplib.HTTPConnection(ip, 80)
    conn.request('GET', '/git-history/wwqgtxx-goagent2.1-/wwqgtxx-goagent2.1-/proxy.ini', headers = {"Host": "wwqgtxx-goagent.googlecode.com"})
    res = conn.getresponse()
    print 'version:', res.version
    print 'reason:', res.reason
    print 'status:', res.status
    print 'msg:', res.msg
    print 'headers:', res.getheaders()
    #html
    print '\n' + '-' * 50 + '\n'
    things = res.read()

def main(ips):
    for ip in ips:
        try:
            print 'try get update from'+ip
            get(ip)	
            print 'get update from'+ip+'successful!!!'
        except socket.error as e:
            print 'get update from'+ip+'unsuccessful'
            continue
        except Exception, e:
            print e
        finally:
            if conn:
                conn.close()