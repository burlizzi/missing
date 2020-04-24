import xbmc
import re
import socket
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen
import zlib
from zlib import decompress
from bs4 import BeautifulSoup, BeautifulStoneSoup
from io import StringIO
import gzip
import xbmcgui

socket.setdefaulttimeout(15)

class Search:
    def __init__(self):
        return NotImplemented
    def search(terms):
        return NotImplemented

        

class x1337x(Search):
    def __init__(self):
        self.search_uri = 'http://1337x.to/search/%s/1/'
    def search(self, terms):
        torrents = []
        url = self.search_uri % '+'.join(terms.split(' '))
        xbmc.log( "url: %s" % ( url ), xbmc.LOGSEVERE )
        f = urlopen(url)
        soup = BeautifulSoup(f.read())
        for table in soup.findAll('table',{'class': 'table-list table table-responsive table-striped'}):
         for row in table.find('tbody').findAll('tr'):
            xbmc.log( "row: %s" % ( row ), xbmc.LOGSEVERE )
            details=row.find('td', class_='coll-1 name');
            size=row.find('td',class_=re.compile('coll-4 .*'));
            name = details.text
            test = 'http://1337x.to' + details.find( 'a', {"class": None})['href']
          
            magnet = ""
            seeds = 0
            leechers = 0
            torrents.append({
                'url': test,
                'name': str(name),
                'size': size.text,
                'seeds': seeds,
                'leechers': leechers,
                'magnet' : magnet,
            })
        return torrents        
        
    def popular(self, terms):
        torrents = []
        url = "http://1337x.to/popular-" + terms
        xbmc.log( "url: %s" % ( url ), xbmc.LOGSEVERE )
        f = urlopen(url)
        content=f.read()
        print(content)
        soup = BeautifulSoup(content)
        for table in soup.findAll('table',{'class': 'table-list table table-responsive table-striped'}):
         for row in table.find('tbody').findAll('tr'):
            xbmc.log( "row: %s" % ( row ), xbmc.LOGSEVERE )
            details=row.find('td', class_='coll-1 name');
            size=row.find('td',class_=re.compile('coll-4 .*'));
            name = details.text
            test = 'http://1337x.to' + details.find( 'a', {"class": None})['href']
          
            magnet = ""
            seeds = 0
            leechers = 0
            torrents.append({
                'url': test,
                'name': str(name),
                'size': size.text,
                'seeds': seeds,
                'leechers': leechers,
                'magnet' : magnet,
            })
        return torrents        
        
class Mininova(Search):
    def __init__(self):
        self.search_uri = 'http://www.mininova.org/rss/%s'
    def search(self, terms):
        torrents = []
        url = self.search_uri % '+'.join(terms.split(' '))
        xbmcgui.Dialog().ok("debug",  url)
        f = urlopen(url)
        soup = BeautifulStoneSoup(f.read())
        for item in soup.findAll('item'):
            (seeds, leechers) = re.findall('Ratio: (\d+) seeds, (\d+) leechers', item.description.text)[0]
            torrents.append({
                'url': item.enclosure['url'],
                'name': item.title.text,
                'seeds': int(seeds),
                'leechers': int(leechers),
            })
        return torrents
class TPB(Search):
    def __init__(self):
        self.search_uris = ['http://thepiratebay.se/search/%s/',
                            'http://pirateproxy.net/search/%s/']
    def search(self, terms):
        torrents = []
        f = None
        for url in [u % '+'.join(terms.split(' ')) for u in self.search_uris]:
            try:
                f = urlopen(url)
                break
            except URLError:
                continue
        if not f:
            raise Exception('Out of pirate bay proxies')
        soup = BeautifulSoup(f.read())
        for details in soup.findAll('a', {'class': 'detLink'}):
            name = details.text
            url = details.findNext('a', {'href': re.compile('^magnet:')})['href']
            td = details.findNext('td')
            seeds = int(td.text)
            td = td.findNext('td')
            leechers = int(td.text)
            torrents.append({
                'url': url,
                'name': name,
                'seeds': seeds,
                'leechers': leechers,
            })
        return torrents
class Kickass(Search):
    def __init__(self):
        self.search_uri = 'http://kat.cr/usearch/%s/?field=seeders&sorder=desc&rss=1'
    def search(self, terms):
        torrents = []
        url = self.search_uri % '+'.join(terms.split(' '))
        xbmc.log( "url: %s" % ( url ), xbmc.LOGSEVERE )
        f = urlopen(url)
        if f.info().get('Content-Encoding') == 'gzip':
           buf = StringIO( f.read())
           f = gzip.GzipFile(fileobj=buf)

        soup = BeautifulStoneSoup(f.read())
        for item in soup.findAll('item'):
            torrents.append({
                'magnet': item.find('torrent:magneturi').text,
                'url': item.enclosure['url'],
                'name': item.title.text,
                'seeds': int(item.find('torrent:seeds').text),
                'leechers': int(item.find('torrent:peers').text),
            })
        return torrents

if __name__ == '__main__':
    s = Kickass()
    results = s.search('zettai')
