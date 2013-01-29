def main():
    import httplib
    conn = httplib.HTTPSConnection("www.google.cn", 443, False)
    conn.request('GET', '/svn/bootstrap.txt', headers = {"Host": "gfangqiang.googlecode.com"})
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
