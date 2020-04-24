'''
    FHEM for XBMC
    Copyright (C) 2011 Team XBMC

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import platform
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import sys
try:
    import urllib.request
except ImportError:
    import urllib2
import os
import re
import telnetlib
import xml.dom.minidom
import json
try:
 import http.client
except:
 import httplib

import datetime
import re
#import conn
#import emule
import getpass
import time
import glob
import search
from urllib.request import urlopen



from html.parser import HTMLParser
import os.path, time





from utilities import *
from bs4 import BeautifulSoup, BeautifulStoneSoup
from urllib.request import urlopen

if sys.version_info < (2, 7):
    import simplejson
else:
    import json as simplejson


__scriptname__ = sys.modules[ "__main__" ].__scriptname__
__settings__ = sys.modules[ "__main__" ].__settings__
__cwd__ = sys.modules[ "__main__" ].__cwd__
__icon__ = sys.modules[ "__main__" ].__icon__
__icondir__   = os.path.join( __cwd__,'resources','icons' )
__addonid__   = "plugin.video.missing"
__addon__     = xbmcaddon.Addon(id=__addonid__)


UT_ADDRESS = __addon__.getSetting('ip')
UT_PORT = __addon__.getSetting('port')
UT_USER = __addon__.getSetting('usr')
UT_PASSWORD = __addon__.getSetting('pwd')
UT_TYPE = __addon__.getSetting('type')

TNT_USER = __addon__.getSetting('tntusr')
TNT_PASSWORD = __addon__.getSetting('tntpwd')


UT_TDIR = xbmc.translatePath( __addon__.getSetting('tdir') )
baseurl = 'http://'+UT_ADDRESS+':'+UT_PORT+'/gui/?token='

BASE_DATA_PATH = sys.modules[ "__main__" ].__profile__
COOKIEFILE = os.path.join( BASE_DATA_PATH, "uTorrent_cookies" )



class TransmissionRPC(object):

    """TransmissionRPC lite library"""

    def __init__(self, host = UT_ADDRESS, port = UT_PORT, username = UT_USER, password = UT_PASSWORD):

        super(TransmissionRPC, self).__init__()

        self.url = 'http://' + host + ':' + str(port) + '/transmission/rpc'
        self.tag = 0
        self.session_id = 0
        self.session = {}
        if username and password:
            password_manager = urllib.HTTPPasswordMgrWithDefaultRealm()
            password_manager.add_password(realm = None, uri = self.url, user = username, passwd = password)
            opener = urllib.build_opener(urllib.HTTPBasicAuthHandler(password_manager), urllib.HTTPDigestAuthHandler(password_manager))
            opener.addheaders = [('User-agent', 'couchpotato-transmission-client/1.0')]
            urllib.install_opener(opener)
        self.session = self.get_session()

    def _request(self, ojson):
        self.tag += 1
        headers = {'x-transmission-session-id': str(self.session_id)}
        request = urllib.request.Request(self.url, json.dumps(ojson).encode('utf-8'), headers)
        try:
            open_request = urllib.request.urlopen(request)
            response = json.loads(open_request.read())
            #print ('response: %s', json.dumps(response))
            if response['result'] == 'success':
                #print ('Transmission action successfull')
                return response['arguments']
            else:
                print(('Unknown failure sending command to Transmission. Return text is: %s', response['result']))
                return False
        except (http.client.InvalidURL):
            print(('Invalid Transmission host, check your config %s', err))
            return False
        except urllib.request.HTTPError as err:
            if err.code == 401:
                print ('Invalid Transmission Username or Password, check your config')
                return False
            elif err.code == 409:
                msg = str(err.read())
                try:
                    self.session_id = \
                        re.search('X-Transmission-Session-Id:\s*(\w+)', msg).group(1)
                    print(('X-Transmission-Session-Id: %s', self.session_id))

                    # #resend request with the updated header

                    return self._request(ojson)
                except:
                    print(('Unable to get Transmission Session-Id %s', err))
            else:
                print(('TransmissionRPC HTTPError: %s', err))
        except (urllib.URLError, err):
            print(('Unable to connect to Transmission %s', err))

    def get_session(self):
        post_data = {'method': 'session-get', 'tag': self.tag}
        return self._request(post_data)

    def add_torrent_uri(self, torrent, arguments ={}):
        arguments['filename'] = torrent
        post_data = {'arguments': arguments, 'method': 'torrent-add', 'tag': self.tag}
        return self._request(post_data)

    def add_torrent_file(self, torrent, arguments):
        arguments['metainfo'] = torrent
        post_data = {'arguments': arguments, 'method': 'torrent-add', 'tag': self.tag}
        return self._request(post_data)

    def set_torrent(self, torrent_id, arguments):
        arguments['ids'] = torrent_id
        post_data = {'arguments': arguments, 'method': 'torrent-set', 'tag': self.tag}
        return self._request(post_data)



class Client(object):
    def __init__(self, address=UT_ADDRESS, port = UT_PORT, user = UT_USER, password = UT_PASSWORD ):
        base_url = 'http://' + address + ':' + port 
        self.url = base_url + '/gui/'
        self.MyCookies = http.cookiejar.LWPCookieJar()
        
        if True:
            password_manager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
            password_manager.add_password(realm=None, uri=self.url, user=user, passwd=password)
            if os.path.isfile(COOKIEFILE) : self.MyCookies.load(COOKIEFILE)
            opener = urllib.request.build_opener(
                urllib.request.HTTPCookieProcessor(self.MyCookies)
                , urllib.request.HTTPBasicAuthHandler(password_manager)
                )
            opener.addheaders = [('User-Agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1) chromeframe/4.0')]
            urllib.request.install_opener(opener)

    def HttpCmd(self, urldta, postdta=None, content=None):
        
        #xbmc.log( "%s::HttpCmd - url: %s" % ( __addonname__, urldta ), xbmc.LOGDEBUG )
        ## Standard code

        req = urllib.Request(urldta,postdta)

        ## Process only if Upload..
        if content != None   :
                req.add_header('Content-Type',content)

        if postdta != None   :
                req.add_header('Content-Length',str(len(postdta)))

        response = urllib.request.urlopen(req,timeout=100)
        link=response.read().strip()
        #print "lungo:" + str(sys.getsizeof(link)) 

        #print str(link)

        #xbmc.log( "%s::HttpCmd - data: %s" % ( "pippo", str(link) ), xbmc.LOGDEBUG )
        response.close()
        self.MyCookies.save(COOKIEFILE)
        return link


        
        
        
params = {
    'address': UT_ADDRESS,
    'port': UT_PORT,
    'user': UT_USER,
    'password': UT_PASSWORD
}
myClient = Client(**params)
eClient = Client()

tntClient = Client()


def getToken():
    tokenUrl = "http://"+UT_ADDRESS+":"+UT_PORT+"/gui/token.html"
    print (tokenUrl)

    data = myClient.HttpCmd(tokenUrl)
    match = re.compile("<div id='token' style='display:none;'>(.+?)</div>").findall(data)
    token = match[0]

    return token    

def adduTorrent(torrenturl,path):
  print (torrenturl)
  token = getToken()            
  url = 'http://'+UT_ADDRESS+':'+UT_PORT+'/gui/?token=' + token + '&action=list-dirs&t=1370371190822'
  data = myClient.HttpCmd(url)
  
  data = str(data, 'utf-8', errors='ignore')
  json_response = simplejson.loads(data)
  path = de_unc(path)
  #xbmc.executebuiltin('Notification("'+ path +'","' +path+'")')
  i = 0
  trovato = 0
  subpath = ""
  for dir in json_response['download-dirs']:
    npath = dir['path'].upper()
    if path.find(npath)>=0:
        trovato = i
        subpath = path[path.index(dir['path'].upper())+len(dir['path']):]
        break
    i = i + 1

  

  #xbmc.executebuiltin('Notification("'+ urllib.quote(torrenturl,'') +'","")') 
  url = 'http://'+UT_ADDRESS+':'+UT_PORT+'/gui/?token=' + token + '&action=add-url&s=' + urllib.parse.quote(torrenturl,'') + '&download_dir={0}&path='.format(i) + urllib.parse.quote(subpath,'') +'&t=1370375169507'
  
  data = myClient.HttpCmd(url)
  #xbmc.executebuiltin('Notification("'+ data +'","' +data+'")') 
    
    
def missing_fetch3(name,id,path):
  ret = True
  #print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
  path = de_unc(path)
  
  print (id)
  if UT_TYPE == "1":
      trpc = TransmissionRPC()
      params = {'download-dir': path
                }
      
      remote_torrent = trpc.add_torrent_uri(id, arguments = params)
      if remote_torrent:
        remote_torrent ="[COLOR green]success[/COLOR]"
      else:
        remote_torrent ="[COLOR red]failure[/COLOR]"

      xbmc.executebuiltin('Notification("'+ remote_torrent + " " + name+ '","' +path+' ", icon = xbmcgui.NOTIFICATION_INFO)')

  if UT_TYPE == "0":
    torrenturl = "http://torcache.net/torrent/"+id+".torrent"
    adduTorrent(torrenturl,path)
    xbmc.executebuiltin('Notification("[COLOR green]success[/COLOR] ' + name+ '","' +path+' ", icon = xbmcgui.NOTIFICATION_INFO)')
  
  return ret


def missing_fetch5():
  ret = True
  
  f = urlopen('http://www.mymovies.it/dvd/')
  data = f.read()
  
  soup = BeautifulStoneSoup(data,convertEntities=BeautifulSoup.HTML_ENTITIES)
  found = False
  data = ""
  for item in soup.html.body.findAll('h2'):
      title = item.a.text.encode('ascii', 'replace')
      title1 = title.replace('-',' ')
      title = title +"  [COLOR yellow]"
      image = item.findNext('img',{ "class" : "cornice_immagine" })['src'][:-5]+'.jpg'
      plot =""
      rating = 0
      for item1 in item.parent.parent.findAll(alt="*"):
        title = title + "*"
        rating = rating + 1         
      for item1 in item.parent.parent.findAll(alt="1/2"):
        title = title + "/"
        rating = rating + 0.5
      title = title + "[/COLOR][COLOR blue]"
      for item1 in item.parent.parent.parent.findNextSiblings('a',href=re.compile('data='),limit=1):
        data = item1['href'][-10:]
        oggi = str(datetime.date.today().day).zfill(2) 
        if oggi > data:
                            title = title + "[CR]                           [COLOR green]" + data 
        else:
                            title = title + "[CR]                           [COLOR red]" + data

      for item1 in item.parent.parent.findNextSiblings('a',href=re.compile('data='),limit=1):
        data = item1['href'][-10:]
        oggi = str(datetime.date.today().day).zfill(2) 
        if oggi > data:
                            title = title + "[CR]                            [COLOR green]" + data 
        else:
                            title = title + "[CR]                            [COLOR red]" + data
      title = title + "[/COLOR]"
      for item1 in item.parent.parent.parent.findNextSiblings('div',{ "class" : "linkblu" },limit=1):
        plot =  item1.findNext('p').text
      for item1 in item.parent.parent.findNextSiblings('div',{ "class" : "linkblu" },limit=1):
        plot =  item1.findNext('p').text
#       title = title + '[CR]' + item1.text
    
      addDir(title.encode('ascii', 'replace'),title1 ,2,image,True," ","/media/4T/Documenti/Film",data = data, plot = plot, rating = rating)
      

  # f = urlopen('http://www.amazon.it/gp/rss/bestsellers/dvd/')
  # soup = BeautifulStoneSoup(f.read())
  # found = False
  # for item in soup.findAll('item'):
      # title = item.title.text.encode('ascii', 'replace')[3:]
      # title=title.replace('-',' ')
      # addDir(title ,title ,2,"",True," ","e:/Documenti/Film")

  # f = urlopen('http://www.movieplayer.it/rss/film-in-uscita-homevideo.xml')
  
  # soup = BeautifulStoneSoup(f.read())
  # found = False
  # for item in soup.findAll('item'):
      # title = item.title.text.encode('ascii', 'replace')[:-60]
      # title=title.replace('-',' ')
      # addDir(title ,title ,2,item.enclosure['url'],True," ","e:/Documenti/Film")
                
  xbmcplugin.setContent(int(sys.argv[1]), 'movies')
  xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
  xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE)
  xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
  xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RATING)

  xbmcplugin.endOfDirectory(int(sys.argv[1]),cacheToDisc=True)

  return ret

def TNTDownload(name,url,path):
  ret = True
  #xbmc.executebuiltin('Notification("'+ path + '","' +name+'", icon = xbmcgui.NOTIFICATION_INFO)')
  xbmc.executebuiltin('Notification("ricevuto...","' +name+'", icon = xbmcgui.NOTIFICATION_INFO)')
  print (url)
  f = urlopen(url,timeout=100)
  data = f.read()
  soup = BeautifulStoneSoup(data)
  path = de_unc(path)
  
  for item in soup.html.body.findAll('a',{ 'title':'Scarica allegato' }):
      params = {'download-dir': path
                }
      remote_torrent = False
      
      if UT_TYPE == "1":
        trpc = TransmissionRPC()
        remote_torrent = trpc.add_torrent_uri(item['href'], arguments = params)
      if UT_TYPE == "0":
        adduTorrent(item['href'],path)
        remote_torrent = True

      if remote_torrent:
       remote_torrent ="[COLOR lime]success [/COLOR]"
      else:
        remote_torrent ="[COLOR red]failure [/COLOR]"
      xbmc.executebuiltin('Notification("'+ remote_torrent + path +' ","' +name+'", icon = xbmcgui.NOTIFICATION_INFO)')
      break
  return ret
  
  
def missing_fetch7(name,id,path):
 

  f = urlopen('http://forum.tntvillage.scambioetico.org/ssi.php?a=out&f='+id+'&show=200&type=rss')
  
  h = HTMLParser()

  soup = BeautifulStoneSoup(f.read(),convertEntities=BeautifulSoup.HTML_ENTITIES)
  found = False
  for item in soup.findAll('item'):
       
       desc = item.description.text
       desc = desc[desc.index('['):desc.index(']')+1]
       desc = colorize(h.unescape(desc).encode('ascii', 'ignore'))
       title = h.unescape(item.title.text).encode('ascii', 'ignore') + ' ' + desc
       url = item.link.text.encode('ascii', 'replace')
       i=""
       print (url)
       addDir(title ,url ,"TNTDownload",i,False," ",path)
                
  xbmcplugin.setContent(int(sys.argv[1]), 'movies')
  xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
  xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE)
  xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)

  xbmcplugin.endOfDirectory(int(sys.argv[1]),cacheToDisc=True)

  return   

def colorize(data):
  data=str(data)
  data = data.replace('<b>','[COLOR blue]')
  data = data.replace('</b>','[/COLOR] ')
  
  replace = re.compile(re.escape('ita'), re.IGNORECASE)  
  data = replace.sub('[COLOR green]ITA[/COLOR]',data)

  replace = re.compile(re.escape('1080'), re.IGNORECASE)  
  data = replace.sub('[COLOR red]1080[/COLOR]',data)
  
  replace = re.compile(re.escape('720'), re.IGNORECASE)  
  data = replace.sub('[COLOR red]720[/COLOR]',data)

  replace = re.compile(re.escape('264'), re.IGNORECASE)  
  data = replace.sub('[COLOR brown]264[/COLOR]',data)
  
  replace = re.compile(re.escape('265'), re.IGNORECASE)  
  data = replace.sub('[COLOR cyan]265[/COLOR]',data)
  
  replace = re.compile(re.escape('AC3'), re.IGNORECASE)  
  data = replace.sub('[COLOR yellow]AC3[/COLOR]',data)

  replace = re.compile(re.escape('DTS'), re.IGNORECASE)  
  data = replace.sub('[COLOR yellow]DTS[/COLOR]',data)
  return data

  
def cercaTNT(name,id,path):
  #print "-----------------------------------------------------------------------------------------------------------------------------------"
  #print name
  #print id
  #print "puntate:"+puntate
  #addDir("aMule global",id,6,"",True,puntate,path)
  #addDir("aMule kad",id,6,"",True,puntate,path)

  #addDir("eMule global",id,6,"",True,puntate,path)
  #addDir("eMule kad",id,6,"",True,puntate,path)
  

  Contentx = 'application/x-www-form-urlencoded'
  terms = id

  if True:
      #print "log in ------------------------------------------------------------"  
      Postx='referer=http%3A%2F%2Fforum.tntvillage.scambioetico.org%2Findex.php%3Fact%3Dallreleases&UserName='+TNT_USER+'&PassWord='+TNT_PASSWORD+'&CookieDate=1'
      url = 'http://forum.tntvillage.scambioetico.org/index.php?act=Login&CODE=01'
      
      Response = tntClient.HttpCmd(url, postdta=Postx, content=Contentx)

      Postx='sb=0&sd=0&cat=0&stn=20&filter='+terms+'&set=Imposta+filtro'
      url = 'http://forum.tntvillage.scambioetico.org/index.php?act=allreleases'
      
      Response = tntClient.HttpCmd(url, postdta=Postx, content=Contentx)
      
  #print Response
  
  

  
      soup = BeautifulStoneSoup(Response,convertEntities=BeautifulSoup.HTML_ENTITIES)
      found = False
      for item in soup.html.body.findAll('tr',{ 'class':'row4'}):
       #print item
     #try:
       
        title = colorize(item.text.encode('ascii', 'ignore'))
        url = item.a['href'].encode('ascii', 'replace')
       #f = urlopen(url)
       #soup1 = BeautifulStoneSoup(f.read())
       #for img in soup1.html.body.findAll('img',{ 'alt':'user posted image' }):
        #   i=img['src'] 
        #   break
        i=""
        addDir(title ,url ,"TNTDownload",i,False," ",path)
      xbmcplugin.endOfDirectory(int(sys.argv[1]),cacheToDisc=False)
     #except:
        #print "error"
def second_level(name,url,path):
    xbmc.log( "second : %s" % ( url ), xbmc.LOGSEVERE ) 
    f = urlopen(url)
    anothersoup = BeautifulSoup(f.read())
    magnet = anothersoup.find( 'a', href=re.compile('magnet.*'))
    #xbmc.log( "anothge : %s" % ( magnet ), xbmc.LOGSEVERE ) 
    xbmc.log( "magnet : %s" % ( magnet['href'] ), xbmc.LOGSEVERE ) 
    
    missing_fetch3(name,magnet['href'],path)
def missing_fetch2(name,id,puntate,path):
  ret = True
                  
  
  
  #xbmcplugin.endOfDirectory(int(sys.argv[1]),cacheToDisc=False)

  #return ret
  #addDir("--------------Kickass----------------" ,"" ,0,"",False," ",path)
  #p = xbmcgui.DialogProgress()
  #p.create("test", "test")
  terms = ' '.join(id.split(' '))
  if not (puntate is None):
    terms = terms+' '+' '.join(puntate.split('|'))
    
  xbmc.executebuiltin( id)
  #cercaTNT(name,terms,path)
  #return
  xbmc.log( "name: %s" % ( puntate ), xbmc.LOGSEVERE ) 
  if True:
      if name is 'popular':
        results = search.x1337x().popular(puntate)
      else:
        results = search.x1337x().search(terms)
      #try:
      #  results = search.x1337().search(terms)
      #except: 
      #  xbmc.executebuiltin('Notification("niente su Mininova","provo su TNT", icon = xbmcgui.NOTIFICATION_INFO)')
      # cercaTNT(name,terms,path)
      #p.close()
      if not results:
         xbmcgui.Dialog().ok("error", "no result")
         return
      
      addDir("TNT Village" ,terms ,"cercaTNT","",True," ",path)
      
      for t in results:
        magnet='&'.join(t['magnet'].split('&')[:2])
        print (magnet)
        xbmc.log( "second : %s,%s,%s" % ( name,t['size'],path ), xbmc.LOGSEVERE ) 
        addDir(colorize(t['name'] + '[CR][COLOR green]                                      ' + t['size'] + '[/COLOR]'),t['url'],"second_level",path,True,path,path)

      pages = terms.split('/')
      page = '2'
      if len(pages) > 1:
        print ("caso 1  ")
        page = str(int(pages[len(pages)-1])+1)
        pages[len(pages)-1] = page
      else:
        print ("caso 2  ")
        pages.append('2')
      
      addDir("Page "+page ,'/'.join(pages) ,2,"",True,"",path)

    
  if False:
   addDir("--------------TORRENTZ----------------" ,"" ,0,"",False,"",path)
   if not "file" in id:
     addDir("cerca nei file","file:"+id,2,"",True,puntate,path)

   if (len(puntate)>325):
       addDir("more...",id,2,"",True,'|'.join(puntate.split('|')[50:]),path)
       puntate = '|'.join(puntate.split('|')[0:50])

  #print nid
   url = 'http://torrentz.eu/search?f='+'+'.join(id.split(' '))+'+'+puntate
  
  
  
  #print url
   f = urlopen(url)
   data = colorize(f.read())
  
  
   replace = re.compile(re.escape(id), re.IGNORECASE)  
   data = replace.sub('[COLOR lime]'+id+'[/COLOR]',data)

  
   soup = BeautifulStoneSoup(data,convertEntities=BeautifulSoup.HTML_ENTITIES)
   found = False
   i = 3
   for item in soup.findAll('dl'):
       i=i+1
       if i > 3:
         found = True
         try:
             hash=item.dt.a['href'][1:]
             print (hash)
             testo = item.dt.a.text
             for xxitem in item.findAll('span',{ 'class':'u'}):
                  testo = testo + " [COLOR green]" + xxitem.text + "[/COLOR]"
             for xxitem in item.findAll('span',{ 'class':'d'}):
                  testo = testo + " [COLOR red]" + xxitem.text + "[/COLOR]"
             addDir(testo,'magnet:?xt=urn:btih:'+hash,3,"",False,path)
         except:
             print ("error")
        

  # addDir("----------------------------------------------------","",0)
  # nid = id + ' ' + season
  # search_uri = 'http://torrentz.eu/feed?q=%s+ita'
  # url = search_uri % '+'.join(nid.split(' '))
  # print url
  # f = urlopen(url)
  # soup = BeautifulStoneSoup(f.read())
  # found = False
  # for item in soup.findAll('item'):
      # ls=item.link.text.split('/')
      # found = True
      # addDir(item.title.text.encode('ascii', 'replace'),ls[3],3,"",False,path)
  # if not found :
      # search_uri = 'http://torrentz.eu/feed?q=%s+ita'
      # nid = id + ' ' + name
      # url = search_uri % '+'.join(nid.split(' '))
      # print url
      # f = urlopen(url)
      # soup = BeautifulStoneSoup(f.read())
      # for item in soup.findAll('item'):
          # ls=item.link.text.split('/')
          # found = True
          # addDir(item.title.text.encode('ascii', 'replace'),ls[3],3,"",False,path)
  # if not found :
      # search_uri = 'http://torrentz.eu/feed?q=%s+ita'
      # nid = id + ' ' + season
      # nid = nid[:-3]
      # url = search_uri % '+'.join(nid.split(' '))
      # print url
      # f = urlopen(url)
      # soup = BeautifulStoneSoup(f.read())
      # for item in soup.findAll('item'):
          # ls=item.link.text.split('/')
          # found = True
          # addDir(item.title.text.encode('ascii', 'replace'),ls[3],3,"",False,path)
  # if not found :
      # search_uri = 'http://torrentz.eu/feed?q=%s'
      # nid = id + ' ' + name
      # url = search_uri % '+'.join(nid.split(' '))
      # print url
      # f = urlopen(url)
      # soup = BeautifulStoneSoup(f.read())
      # for item in soup.findAll('item'):
          # ls=item.link.text.split('/')
          # found = True
          # addDir(item.title.text.encode('ascii', 'replace'),ls[3],3,"",False,path)
  # if not found :
      # search_uri = 'http://torrentz.eu/feed?q=%s'
      # nid = id + ' ' + season
      # url = search_uri % '+'.join(nid.split(' '))
      # print url
      # f = urlopen(url)
      # soup = BeautifulStoneSoup(f.read())
      # for item in soup.findAll('item'):
          # ls=item.link.text.split('/')
          # found = True
          # addDir(item.title.text.encode('ascii', 'replace'),ls[3],3,"",False,path)
  # if not found :
      # search_uri = 'http://torrentz.eu/feed?q=%s'
      # nid = nid[:-3]
      # url = search_uri % '+'.join(nid.split(' '))
      # print url
      # f = urlopen(url)
      # soup = BeautifulStoneSoup(f.read())
      # for item in soup.findAll('item'):
          # ls=item.link.text.split('/')
          # found = True
          # addDir(item.title.text.encode('ascii', 'replace'),ls[3],3,"",False,path)


  #search_uri = 'http://thepiratebay.se/search/%s+ita/'
  #url = search_uri % '+'.join(nid.split(' '))
  #print url
  #f = urlopen(url)
  #soup = BeautifulStoneSoup(f.read())
  #for item in soup.findAll('a', {'class': 'detLink'}):
  #          #(seeds, leechers) = re.findall('Ratio: (\d+) seeds, (\d+) leechers', item.description.text)[0]
            
  #          addDir(item.text,"",2,"",False,"")
  #          #torrents.append({
  #          #    'url': item.enclosure['url'],
  #          #    'name': item.title.text,
  #          #    'seeds': int(seeds),
  #          #    'leechers': int(leechers),
  #          #})
  xbmcplugin.endOfDirectory(int(sys.argv[1]),cacheToDisc=False)
  
  return ret

def tvdb(name):
  req = urllib.request.Request("http://thetvdb.com/api/GetSeries.php?seriesname="+ urllib.parse.quote_plus(name) +"&language=en")
  try: handle = urllib.request.urlopen(req)
  except (IOError, e):
    xbmc.log('missing... url ' + "http://thetvdb.com/api/GetSeries.php?seriesname="+ urllib.parse.quote_plus(name) +"&language=it", level=xbmc.LOGERROR)
    queue = handle.read()
  else:
    queue = handle.read()
    handle.close()

  xmldata = xml.dom.minidom.parseString(queue)
  serieid=xmldata.getElementsByTagName('seriesid')[0].firstChild.nodeValue
  for Serie in xmldata.getElementsByTagName('Series'):
    xbmc.log('iter ' + Serie.getElementsByTagName('SeriesName')[0].firstChild.nodeValue, level=xbmc.LOGERROR)
    if Serie.getElementsByTagName('SeriesName')[0].firstChild.nodeValue==name:
        serieid=Serie.getElementsByTagName('seriesid')[0].firstChild.nodeValue

  xbmc.log('serieid ' + serieid, level=xbmc.LOGERROR)
  req = urllib.request.Request("http://thetvdb.com/api/6E82FED600783400/series/"+serieid+"/all/it.xml")
  try: handle = urllib.request.urlopen(req)
  except (IOError, e):
    xbmc.log('SABnzbd-Suite: could not determine SABnzbds status', level=xbmc.LOGERROR)
  else:
    queue = handle.read().decode('utf-8') #.read()
    handle.close()
  return queue

def de_unc(path):
    searchpath = path
    #searchpath = (searchpath.replace('/','\\')).upper()
    searchpath = (searchpath.replace('nfs://odroidxu4',''))
    searchpath = (searchpath.replace('smb:',''))
    return searchpath
  

def missing_fetch1(name,id,path):
  ret = True
  file = path+'/cache.tdb'
  #file = file.replace('/','\\')
  file = file.replace('nfs://odroidxu4/export','/media')
  file = file.replace('smb:','')
  
  if os.path.isfile(file) and (datetime.datetime.now()-datetime.datetime.fromtimestamp(os.path.getmtime(file))).days<10:
   with open(file, 'r') as content_file:
      queue = content_file.read()
  else: 
     queue = tvdb(name)  
     xbmc.log(queue, level=xbmc.LOGERROR)
     try:
         xbmc.log(queue, level=xbmc.LOGERROR)
         with open(file, 'w') as content_file:
          content_file.write(queue)
          xbmc.executebuiltin('Notification("'+ name +' reloaded","' +path+' ", icon = xbmcgui.NOTIFICATION_INFO)')
     except:
          xbmc.executebuiltin('Notification("'+ name +' fail writing cache","' +path+' ", icon = xbmcgui.NOTIFICATION_INFO)')
     
     
  
  file = de_unc(path)+'search.tdb'
  if os.path.isfile(file):
         with open(file, 'r') as content_file:
          name = content_file.read()
  else: 
         name = name
  
    
  print (queue)
  xmldata = xml.dom.minidom.parseString(str(queue))
  allepisodes=xmldata.getElementsByTagName('Episode')
  json_query_season = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": {"properties": ["season", "episode"], "sort": { "method": "label" }, "tvshowid":'+id+'}, "id": 1}')
  xbmc.log('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": {"properties": ["season", "episode"], "sort": { "method": "label" }, "tvshowid":'+id+'}, "id": 1}', level=xbmc.LOGERROR)
  print (json_query_season)
  xbmc.log(json_query_season, level=xbmc.LOGERROR)
  jsonobject_season = simplejson.loads(json_query_season)
  #Get start/end and total seasons
  #if jsonobject_season['result'].has_key('limits'):
  #  season_limit = jsonobject_season['result']['limits']
   #Get the season numbers


  tutti = "" 
  separator = ""
  addDir("Any",name,2,"",True," ",path)
  if 'episodes' in jsonobject_season['result']:
    episodes = jsonobject_season['result']['episodes']
    for epi in allepisodes:
      if (int(epi.getElementsByTagName('SeasonNumber')[0].firstChild.nodeValue) > 0):
        #print "---------------------------------------"+epi.getElementsByTagName('SeasonNumber')[0].firstChild.nodeValue+"x"+epi.getElementsByTagName('EpisodeNumber')[0].firstChild.nodeValue
        nepi = int(epi.getElementsByTagName('EpisodeNumber')[0].firstChild.nodeValue)
        nseason = int(epi.getElementsByTagName('SeasonNumber')[0].firstChild.nodeValue)
        found = False
        for episode in episodes:
            try:
                #print str(episode.get('season'))+"x"+str(episode.get('episode'))
                if nepi < episode.get('episode') and nseason < episode.get('season'):
                    print ("break")
                    break

                if nepi == episode.get('episode') and nseason == episode.get('season'):
                    found = True
                    #print "found"
                    #print str(episode.get('season'))+"x"+str(episode.get('episode'))
                    episodes.remove(episode)
                    break
            except:
                xbmc.log('SABnzbd-Suite: could not determine SABnzbds status', level=xbmc.LOGERROR)

        if not found:
                print ("NOT found")
            #try:
                ll = 'S{0:02d}E{1:02d}'.format(nseason,nepi)
                tutti = tutti + separator + ll
                separator = "|"
                #print ll
                image = "";
                ie = epi.getElementsByTagName('filename')
                if ie.length >0 :
                    node=ie[0].firstChild
                    if node is not None:
                        image = "http://www.nextepisode.tv/uploads/tvdb/"+node.nodeValue

                        
                ename = 'S{0:02}E{1:02}'.format(nseason,nepi)
                

                ie = epi.getElementsByTagName('EpisodeName')
                if ie.length >0 :
                    node=ie[0].firstChild
                    if node is not None:
                        ename = ename +" "+node.nodeValue #.encode('ascii', 'replace') 
                data = ""
                ie = epi.getElementsByTagName('FirstAired')
                if ie.length >0 :
                    node=ie[0].firstChild
                    if node is not None:
                        data = node.nodeValue 
                        oggi = str(datetime.date.today())
                        #print oggi
                        if oggi > data:
                            ename = ename + "[CR]                                             [COLOR green]" + node.nodeValue + "[/COLOR]"
                        else:
                            ename = ename + "[CR]                                             [COLOR red]" + node.nodeValue + "[/COLOR]"

                #pattern = '*{0}?{1:02}*.!UT'.format(nseason,nepi)
                #searchpath = de_unc(path)
                #print searchpath
                

                #for yname in glob.glob(os.path.join(searchpath,pattern)):
                #   ename = "[COLOR red]*[/COLOR]" + ename

                #for yname in glob.glob(os.path.join(searchpath,"*/" + pattern)):
                #   ename = "[COLOR red]*[/COLOR]" + ename
                    
                #for yname in glob.glob(os.path.join(searchpath,"*/*/" + pattern)):
                #   ename = "[COLOR red]*[/COLOR]" + ename
                #print ename    
                addDir(ename ,name,2,image,True,ll,path,data) 
            #except:
             #   addDir(epi.getElementsByTagName('SeasonNumber')[0].firstChild.nodeValue+"x"+epi.getElementsByTagName('EpisodeNumber')[0].firstChild.nodeValue ,name,2,"",True,epi.getElementsByTagName('SeasonNumber')[0].firstChild.nodeValue+"x"+epi.getElementsByTagName('EpisodeNumber')[0].firstChild.nodeValue,season) 


  #print tutti           
  addDir("Tutti",name,2,"",True,tutti,path)
  xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
  xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE)
  xbmcplugin.addSortMethod( int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_DATE)
  xbmcplugin.endOfDirectory(int(sys.argv[1]),cacheToDisc=True)

  

  return ret

  
def amule(name,url,path):
  #print "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
  #print name
  #print url
  ec = conn.ECConnection("openelec", UT_ADDRESS)
  request= conn.create_ecpacket_add_link_req(url)
  reply = ec.send_and_recv_ecpacket(request)
  file = '/media/2T/temp/aMule/'+name + '.mv'
  with open(file, 'w') as content_file:
     content_file.write(path)  
  xbmc.executebuiltin('Notification("'+ name +'","' +path+' ", icon = xbmcgui.NOTIFICATION_INFO)')



def emule(name,url,path):
  #print "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
  #print name
  #print url
  eClient.HttpCmd(url)
  xbmc.executebuiltin('Notification("'+ name +'","' +path+' ", icon = xbmcgui.NOTIFICATION_INFO)')


def cercaEMule(tag,path,type='global'): 
  tag = '+'.join(tag.split(' '))+'+ITA'
  Postx='p=tabbarano&w=password'
  Contentx = 'application/x-www-form-urlencoded'
  url = 'http://bender:4711'
  #print tag
  Response = eClient.HttpCmd(url, postdta=Postx, content=Contentx)
  match = re.compile('<input type="hidden" name=ses value="(.*)">').findall(Response)
  token = match[0]
  url = 'http://bender:4711/?tosearch='+tag+'&unicode=on&sort=3&sortAsc=0&type=&min=&max=&avail=&ext=&method='+type+'&ses='+token+'&w=search'
  #print url
  
  Response = eClient.HttpCmd(url)
  #print Response;

  soup = BeautifulStoneSoup(Response,convertEntities=BeautifulSoup.HTML_ENTITIES)
  found = False
  data = ""
  for item in soup.html.body.findAll('td',{ 'class':'search-line-left'}):
      for i1 in item.parent.findNextSiblings('td',{ 'class':'search-line'},limit=1):
        for i2 in i1.findNextSiblings('td',{ 'class':'search-line'},limit=1):
            link = 'http://bender:4711/?ses='+token+'&w=search&downloads='+i1.findNext('font').text
            addDir(item.findNext('font').text.encode('ascii', 'replace'),link,"emule","",False,"-md",path,rating = i2.findNext('font').text)

  #print token

  
def cercaMule(tag,path,type='global'): 
  #print tag

  ec = conn.ECConnection("openelec", UT_ADDRESS)
  if (type=='global'):
    request= conn.create_ecpacket_search_global_req (tag)
  elif (type=='kad'):
    request= conn.create_ecpacket_search_kad_req (tag)
  
  reply = ec.send_and_recv_ecpacket(request)
#  print reply.debugrepr()
  
  finito = False

  #print "---------------------------------------------------------------------------------------------------------------------------"

  while (not finito):
    time.sleep(10)
    request= conn.create_ecpacket_search_progress_req ()
    reply = ec.send_and_recv_ecpacket(request)
    if len(reply.subtags)>0:
     if reply.subtags[0].tagdata == 0:
        finito = True

  request= conn.create_ecpacket_search_results_req ()
  reply = ec.send_and_recv_ecpacket(request)
  
  for item in reply.subtags:
    
    try:
        link = "ed2k://|file|" + urllib.parse.quote(item.subtags[3].tagdata) + "|" + str(item.subtags[4].tagdata) + "|" + (item.subtags[5].tagdata).encode("hex") + "|/" 
        addDir(item.subtags[3].tagdata,link,"amule","",False,"-md",path,rating=item.subtags[0].tagdata)
    except:
       print ("errore")
  
def missing_fetch6(name,tag,puntate,path):
  #print "///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////"
  #print puntate
  type='global'
  if (name=="eMule kad"):
    type='kademlia'
  if puntate != None:
    cercaMule(tag+" " +puntate,path,type)
    try:
        cercaMule(tag+" " +str(int(puntate[1:3])) + "x" + str(int(puntate[4:6])),path,type)  
    except:
        print ("error")
  else:
    cercaMule(tag,path,type)  
  

  
#  addDir("Ricerca ita aMule","ita",6,"",True,"-md","e:/Documenti/Film")
  xbmcplugin.setContent(int(sys.argv[1]), 'movies')
  #xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
  xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RATING)
  #xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE)
  #xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
  xbmcplugin.endOfDirectory(int(sys.argv[1]),cacheToDisc=True)
  
  
def missing_fetch():
  ret = True
  Medialist = []
  
  json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": {"properties": ["file", "imdbnumber", "art"], "sort": { "method": "label" } }, "id": 1}')
  #json_query = str(json_query, 'utf-8', errors='ignore')
  jsonobject = simplejson.loads(json_query)
  if 'tvshows' in jsonobject['result']:
    for item in jsonobject['result']['tvshows']:
        #print item
        addDir(item.get('label',''), str(item.get('tvshowid','')),1, str(item.get('art','').get('poster','')),True,item.get('file',''),banner = str(item.get('art','').get('banner','')))

#  addDir("Ricerca ita eMule","ita",6,"",True,"","/media/VOLUME/Documenti/Film")
  addDir("Ricerca -md",    "age%3ayear"   ,2,"",True,"","/media/4T/Documenti/Film")
  addDir("Ricerca ita -md","ITA",2,"",True,"-md","/media/4T/Documenti/Film")
  addDir("Ricerca -md last week","age%3aweek",2,"",True,"","/media/4T/Documenti/Film")
  addDir("Ricerca ita -md last week","ITA",2,"",True,"-md age%3aweek","/media/4T/Documenti/Film")
  addDir("TNTVillage Cartoni","405",7,"",True,"","/media/4T/Documenti/Cartoni")
  addDir("TNTVillage TV","539",7,"",True," -md+added%3A3d","/media/4T/Documenti/Serie")
  addDir("TNTVillage Film","401",7,"",True," -md+added%3A3d","/media/4T/Documenti/Film")
  addDir("DVD in uscita","",5)
  addDir("net stat","xxx","popular","xxx",True,"","/media/4T/scripts")
  addDir("Popular movies","movies","popular","movies",True,"","/media/4T/Documenti/Film")
  addDir("Popular movies week","movies-week","popular","movies",True,"","/media/4T/Documenti/Film")
  addDir("Popular tv series","tv","popular","tv",True,"","/media/4T/Documenti/transmission")
  addDir("Popular tv series week","tv-week","popular","tv",True,"","/media/4T/Documenti/transmission")
  addDir("Ricerca libera torrentz","ita","libera","",True,"","/media/4T/Documenti/Film")

  addDir("Nuova Serie","ita","nuova_serie","",True,"","/media/4T/Documenti/Serie/")
  
  xbmcplugin.endOfDirectory(int(sys.argv[1]),cacheToDisc=True)
  
  
  return ret

def libera(name,url,path):
      keyboard = xbmc.Keyboard()
      keyboard.doModal()
      if (keyboard.isConfirmed()):
            missing_fetch2("cerca",keyboard.getText(),"","/media/4T/Documenti/Film")
          
def popular(name,url,path):
    xbmc.log( "url: %s" % ( url ), xbmc.LOGSEVERE ) 
    missing_fetch2("popular",url,url,path)
          



def nuova_serie(name,url,path):
      #keyboard = xbmc.Keyboard()
      #keyboard.doModal()
      #if (keyboard.isConfirmed()):
    #       missing_fetch2("cerca",keyboard.getText(),"",path+keyboard.getText())
 kb = xbmc.Keyboard('', '')
 kb.doModal()
 if not kb.isConfirmed():
     return
 terms = kb.getText()
 p = xbmcgui.DialogProgress()
 p.create("test", "test")
 try:
     results = search.x1337x().search(terms)
 except:
     p.close()
     xbmcgui.Dialog().ok("test", "test")
     return
 p.close()
 if not results:
     xbmcgui.Dialog().ok("test", "test")
     return
 selected = xbmcgui.Dialog().select("test", ['[S:%d L:%d] %s' % (t['seeds'], t['leechers'], t['name']) for t in results])
 if selected < 0:
     return
 try:
      trpc = TransmissionRPC()
      params = {'download-dir': path+'/'+terms
                }
      remote_torrent = trpc.add_torrent_uri(results[selected]['url'], arguments = params)
      if remote_torrent:
            remote_torrent ="[COLOR green]success[/COLOR]"
      else:
            remote_torrent ="[COLOR red]failure[/COLOR]"
      xbmc.executebuiltin('Notification("'+ remote_torrent + " " + name+ '","' +path+' ", icon = xbmcgui.NOTIFICATION_INFO)')
 except:
     xbmcgui.Dialog().ok(_(32000), _(32293))
     return
              
          
          
  
  
def context(name,url,path):
      
      file = de_unc(path)+'search.tdb'
      
      if os.path.isfile(file):
         with open(file, 'r') as content_file:
          queue = content_file.read()
      else: 
         queue = name

      keyboard = xbmc.Keyboard(queue)
      keyboard.doModal()
      if (keyboard.isConfirmed()):
          with open(file, 'w') as content_file:
              content_file.write(keyboard.getText())


def addDir(name,url,mode,iconimage="",folder=True,season="",path="",data="",plot = "",banner="",rating=0):
    u = sys.argv[0]+"?id="+sys.argv[1]+"&url="+urllib.parse.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.parse.quote_plus(name)+"&season="+urllib.parse.quote_plus(season)+"&path="+urllib.parse.quote_plus(path)
    #print u
    ok = True
    icon = iconimage
    #icon1 = 'http://192.168.178.1:8085/fhem?cmd=showlog%20weblink_Bagno_grande%20FileLog_Bagno_grande%20temp5hum4%20Bagno_grande-2012-12.log&pos='
    point = xbmcgui.ListItem(label=name,iconImage=banner,label2=data,thumbnailImage = icon)
    
    
    infoLabels = dict()
    infoLabels['title'] = name
    infoLabels['plot'] = plot
    infoLabels['plotoutline'] = plot
    infoLabels['rating'] = rating 
    if data!="" :
        infoLabels['date'] =data
    #infoLabels['duration'] = str(movie['length_in_minutes'])
    #infoLabels['cast'] = movie['cast']
    #infoLabels['director'] = ' / '.join(movie['directors'])
    #infoLabels['mpaa'] = str(movie['age_rating'])
    #infoLabels['code'] = str(movie['imdb_id'])
    #infoLabels['genre'] = ' / '.join(movie['genres'])  
    
    point.setInfo( type='video', infoLabels=infoLabels )
    #point.setLabel2(data)
    #point.setProperty('label2',data)
    point.setProperty('fanart_image',icon)
    point.setProperty('banner',banner)
    rp = "XBMC.RunPlugin(%s?mode=%s&name=%s&url=TNTDownload&path=%s)"

    point.addContextMenuItems([("Cambia search string", rp % (sys.argv[0], "context",name,urllib.parse.quote_plus(season))),("Nuova serie", rp % (sys.argv[0], "nuova_serie",name,urllib.parse.quote_plus(season)))],replaceItems=False)
    
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=point,isFolder=folder,totalItems = 25)
    
    
 
def media_path(path):
    # Check for stacked movies
    try:
        path = os.path.split(path)[0].rsplit(' , ', 1)[1].replace(",,",",")
    except:
        path = os.path.split(path)[0]
    # Fixes problems with rared movies and multipath
    if path.startswith("rar://"):
        path = [os.path.split(urllib.request.url2pathname(path.replace("rar://","")))[0]]
    elif path.startswith("multipath://"):
        temp_path = path.replace("multipath://","").split('%2f/')
        path = []
        for item in temp_path:
            path.append(urllib.request.url2pathname(item))
    else:
        path = [path]
    return path
