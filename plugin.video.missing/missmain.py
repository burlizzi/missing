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
import xbmc
import xbmcaddon
import xbmcgui
import time
import os
import urllib, sys, os, re, time
import xbmcaddon, xbmcplugin, xbmcgui, xbmc

__addonname__ = "Missing"
__settings__   = xbmcaddon.Addon(id='plugin.video.missing')
__cwd__        = __settings__.getAddonInfo('path')
__icon__       = os.path.join(__cwd__,"icon.png")
__scriptname__ = "XBMC missing"
__profile__   = xbmc.translatePath( __settings__.getAddonInfo('profile') )

BASE_RESOURCE_PATH = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ) )
sys.path.append (BASE_RESOURCE_PATH)

from fhem import *
from utilities import *



  

        
def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
            params=sys.argv[2]
            cleanedparams=params.replace('?','')
            if (params[len(params)-1]=='/'):
                    params=params[0:len(params)-2]
            pairsofparams=cleanedparams.split('&')
            param={}
            for i in range(len(pairsofparams)):
                    splitparams={}
                    splitparams=pairsofparams[i].split('=')
                    if (len(splitparams))==2:
                            param[splitparams[0]]=splitparams[1]

    return param




mode = 0
params = get_params()  
season = None

try:
    url = urllib.unquote_plus(params['url'])
except:
    pass
try:
    path = urllib.unquote_plus(params['path'])
except:
    pass
try:
    name = urllib.unquote_plus(params['name'])
except:
    pass

try:
    season = urllib.unquote_plus(params['season'])
except:
    pass
	
try:
    mode = int(params['mode'])
except:
	#try:
	if len(params)>0:
		m = params['mode'] 
		globals()[m](name,url,path)
		mode = -1
	#except:
	#	pass
	pass

if  mode == 7:
  missing_fetch7(name,url,path)
if  mode == 6:
  missing_fetch6(name,url,season,path)
if  mode == 5:
  missing_fetch5()
if  mode == 3:
  missing_fetch3(name,url,season)
if  mode == 2:
  missing_fetch2(name,url,season,path)
elif mode == 1:
  missing_fetch1(name,url,season)
elif mode == 0:
  missing_fetch()
  