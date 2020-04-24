import urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse, http.cookiejar, sys, os
from base64 import b64encode
import xbmc

__addonname__ = sys.modules[ "__main__" ].__addonname__

# base paths
BASE_DATA_PATH = sys.modules[ "__main__" ].__profile__
BASE_RESOURCE_PATH = sys.modules[ "__main__" ].BASE_RESOURCE_PATH
COOKIEFILE = os.path.join( BASE_DATA_PATH, "uTorrent_cookies" )

def _create_base_paths():
    """ creates the base folders """
    if ( not os.path.isdir( BASE_DATA_PATH ) ):
        os.makedirs( BASE_DATA_PATH )
_create_base_paths()

def MultiPart(fields,files,ftype) :
    Boundary = '----------ThIs_Is_tHe_bouNdaRY_---$---'
    CrLf = '\r\n'
    L = []

    ## Process the Fields required..
    for (key, value) in fields:
        L.append('--' + Boundary)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    ## Process the Files..
    for (key, filename, value) in files:
        L.append('--' + Boundary)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        ## Set filetype based on .torrent or .nzb files.
        if ftype == 'torrent':
            filetype = 'application/x-bittorrent'
        else:
            filetype = 'text/xml'
        L.append('Content-Type: %s' % filetype)
        ## Now add the actual Files Data
        L.append('')
        L.append(value)
    ## Add End of data..
    L.append('--' + Boundary + '--')
    L.append('')
    ## Heres the Main stuff that we will be passing back..
    post = CrLf.join(L)
    content_type = 'multipart/form-data; boundary=%s' % Boundary
    ## Return the formatted data..
    return content_type, post

class Client(object):
    def __init__(self, address='localhost', port='8080', user=None, password=None):
        base_url = 'http://' + address + ':' + port
        self.url = base_url + '/gui/'
        if user:
            password_manager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
            password_manager.add_password(realm=None, uri=self.url, user=user, passwd=password)
            self.MyCookies = http.cookiejar.LWPCookieJar()
            if os.path.isfile(COOKIEFILE) : self.MyCookies.load(COOKIEFILE)
            opener = urllib.request.build_opener(
                urllib.request.HTTPCookieProcessor(self.MyCookies)
                , urllib.request.HTTPBasicAuthHandler(password_manager)
                )
            opener.addheaders = [('User-Agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1) chromeframe/4.0')]
            urllib.request.install_opener(opener)

    def HttpCmd(self, urldta, postdta=None, content=None):
        xbmc.log( "%s::HttpCmd - url: %s" % ( __addonname__, urldta ), xbmc.LOGDEBUG )
        ## Standard code

        req = urllib.request.Request(urldta,postdta)

        ## Process only if Upload..
        if content != None   :
                req.add_header('Content-Type',content)
                req.add_header('Content-Length',str(len(postdta)))

        response = urllib.request.urlopen(req)
        link=response.read()
        xbmc.log( "%s::HttpCmd - data: %s" % ( __addonname__, str(link) ), xbmc.LOGDEBUG )
        response.close()
        self.MyCookies.save(COOKIEFILE)
        return link


