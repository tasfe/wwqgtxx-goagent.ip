def main():
    import httplib
    conn = httplib.HTTPConnection("www.google.cn", 80, False)
    conn.request('GET', '/git-history/wwqgtxx-goagent2.1-/wwqgtxx-goagent2.1-/proxy.ini', headers = {"Host": "wwqgtxx-goagent.googlecode.com"})
    res = conn.getresponse()
    print 'version:', res.version
    print 'reason:', res.reason
    print 'status:', res.status
    print 'msg:', res.msg
    print 'headers:', res.getheaders()
    #html
    print '\n' + '-' * 50 + '\n'
    print res.read()
    conn.close()

if __name__ == '__main__':
    main()
