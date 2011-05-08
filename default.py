# -*- coding: utf-8 -*-
"""

plugin video M6 Replay pour XBMC 

06-03-2011 Version 1.4.4 par Temhil et beenje
    + Ajout de pycrypto pour openELEC (patch de beenje)
    + Ajout selection de la plateforme dans les parametres
    + Configure le serveur 3 par defaut
    + Support vue Media Info pour les videos
    
23-02-2011 Version 1.4.3 par Temhil
    + Ajout du serveur 3
    
23-02-2011 Version 1.4.2 par Temhil
    + Configure le serveur 2 par defaut (a la place sur serveur 1)
	
22-02-2011 Version 1.4.1 par Temhil et beenje
    + Ajout de pycrypto pour ATV2 (patch de beenje)
    + Correction bug encodage (patch de beenje)
    + Correction bug affichage des jours de la semaines (decalage)
    
02-01-2011 Version 1.4.0 par Temhil
    + Ajout du choix du serveur dans les parametres du plugin
    + Utilisation de setResolvedUrl permettant d'utiliser le player par defaut d'XBMC:
      . Cela evite des problemes d'affichage lors du chargement de la video
      . permet le transfert automatique des informations (nom, icone) au player d'XBMC
    + Ajout de la bibliothèque "python-crypto" pour platformes MacOSX 32bits et XBOX
    + Ajout de la description de la video (resume, date de diffusion, date de fin, duree)
    + Activation du Tri
    + Resolution du bug lorsque les images affichee ne correspondaint pas a la categorie. 
      On efface desormais les thumbs du cache a chaque fois, le chargement des images sera donc plus
      lent, mais a moins de faire d'importantes modification du design actuel, cette solution reste
      un bon compromis 
      
08-11-2010 Version 1.3.0 par merindol
    + Affichage des différentes versions des medias quand il y en a (VF, VOSTFR, ...) 
    
06-11-2010 Version 1.2.0 par merindol
    ~ Le déchiffrage du catalogue se fait désormais grâce à la bibliothèque python "python-crypto" enbarquée

"""

REMOTE_DBG       = False # For remote debugging with PyDev (Eclipse)

__addonID__      = "plugin.video.M6Replay"
__author__       = "PECK, mighty_bombero, merindol, Temhil"
__url__          = "http://passion-xbmc.org/index.php"
__credits__      = "Team XBMC Passion"
__date__         = "06-03-2010"
__version__      = "1.4.4"

import urllib,sys,os,platform
import base64
import string
import pickle
import datetime
import re
from traceback import print_exc
from xml.dom.minidom import parseString

# xbmc modules
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon


__addon__ = xbmcaddon.Addon( __addonID__ )
__settings__ = __addon__
__language__ = __addon__.getLocalizedString
__addonDir__ = __settings__.getAddonInfo( "path" )

# Remote debugger using Eclipse and Pydev
if REMOTE_DBG:
    # Note pydevd module need to be copied in XBMC\system\python\Lib\pysrc
    try:
        import pysrc.pydevd as pydevd
        pydevd.settrace('localhost', stdoutToServer=True, stderrToServer=True)
    except ImportError:
        sys.stderr.write("Error: " +
            "You must add org.python.pydev.debug.pysrc to XBMC\system\python\Lib\pysrc")
        sys.exit(1)

ROOTDIR            = os.getcwd()
BASE_RESOURCE_PATH = os.path.join( ROOTDIR, "resources" )
MEDIA_PATH         = os.path.join( BASE_RESOURCE_PATH, "media" )
#ADDON_DATA         = __addonDir__
ADDON_DATA  = xbmc.translatePath( "special://profile/addon_data/%s/" % __addonID__ )
#DOWNLOADDIR        = os.path.join( ADDON_DATA, "downloads")
CACHEDIR           = os.path.join( ADDON_DATA, "cache")
THUMB_CACHE_PATH   = os.path.join( xbmc.translatePath( "special://profile/" ), "Thumbnails", "Video" )

#modules custom
try:
    from resources.lib.utils import convertStrTime2Time, convertTime2FrenchString, bold_text, add_pretty_color, extractDateString, convertMin2Hour
except:
    print_exc()

# Server List
srv_list = [ {'rtmp': "rtmpe://m6replayfs.fplive.net/m6replay/streaming", 'app': "m6replay/streaming"}, # France (semble ne plus fonctionner)
             {'rtmp': "rtmpe://m6dev.fcod.llnwd.net:443/a3100/d1",        'app': "a3100/d1"},           # International
             {'rtmp': "rtmp://groupemsix.fcod.llnwd.net/a3100/d1",        'app': "a3100/d1"}]          # International

# List of directories to check at startup
dirCheckList   = ( CACHEDIR, ) 

# Check the platform
SYSTEM_PLATFORM = None
CRYPTO_PATH = None
if ( __settings__.getSetting('autoplatform') == 'true'):
    os_type_list = ['Windows', 'mac', 'mac_arm', 'Linux', 'Xbox']
    cpu_type_list = ['32bit', '64bit']
    paths = []
    os_type_id  = int( __settings__.getSetting('ostype') )
    cpu_type_id = int( __settings__.getSetting('cputype') )
    print os_type_list[os_type_id]
    print cpu_type_list[cpu_type_id]
    if os_type_list[os_type_id] in ['Windows', 'Linux']:
        CRYPTO_PATH = os.path.join( __addonDir__, "resources", "platform_libraries", os_type_list[os_type_id], cpu_type_list[cpu_type_id] )
    elif os_type_list[os_type_id] == 'mac':
        CRYPTO_PATH = os.path.join( __addonDir__, "resources", "platform_libraries","Darwin", cpu_type_list[cpu_type_id] )
    elif os_type_list[os_type_id] == 'mac_arm':
        CRYPTO_PATH = os.path.join( __addonDir__, "resources", "platform_libraries","Darwin", "arm" )
    elif os_type_list[os_type_id] == 'Xbox':
        CRYPTO_PATH = os.path.join( __addonDir__, "resources", "platform_libraries", "Xbox" )
else:  
    if xbmc.getCondVisibility( "system.platform.linux" ):
        SYSTEM_PLATFORM = "linux"
        #CRYPTO_PATH = os.path.join( __addonDir__, "resources", "platform_libraries", platform.system(), platform.architecture()[0] )
        if os.uname()[4] == 'i686':
            architecture = '32bit'
        else:
            architecture = '64bit'
        CRYPTO_PATH = os.path.join( __addonDir__, "resources", "platform_libraries", os.uname()[0], architecture )     
    elif xbmc.getCondVisibility( "system.platform.xbox" ):
        SYSTEM_PLATFORM = "xbox"
        CRYPTO_PATH = os.path.join( __addonDir__, "resources", "platform_libraries", "Xbox" )
    elif xbmc.getCondVisibility( "system.platform.windows" ):
        SYSTEM_PLATFORM = "windows"
        # Only 32bits on Windows for timebeing
        CRYPTO_PATH = os.path.join( __addonDir__, "resources", "platform_libraries", "Windows", "32bit" )
    elif xbmc.getCondVisibility( "system.platform.osx" ):
        SYSTEM_PLATFORM = "darwin"
        if 'RELEASE_ARM' in os.uname()[3]:
            architecture = 'arm'
        else:
            architecture = platform.architecture()[0]
        CRYPTO_PATH = os.path.join( __addonDir__, "resources", "platform_libraries", os.uname()[0], architecture )

if CRYPTO_PATH:
    sys.path.append(CRYPTO_PATH)
else:
    print "Impossible to determine the platform and set an import path"
    dialog = xbmcgui.Dialog()
    dialog.ok( __language__(30201), __language__(30202) ,__language__(30203))

#print "CRYPTO_PATH: %s"%CRYPTO_PATH

# Import Crypto lib
try:
    from Crypto.Cipher import DES
except:
    print "Impossible to import Crypto.Cipher"
    dialog = xbmcgui.Dialog()
    dialog.ok( __language__(30201), __language__(30204) ,__language__(30203))
    

def verifrep( folder ):
    """
        Source MyCine (thanks!)
        Check a folder exists and make it if necessary
    """
    try:
        #print("verifrep check if directory: " + folder + " exists")
        if not os.path.exists( folder ):
            print( "verifrep Impossible to find the directory - trying to create the directory: " + folder )
            os.makedirs( folder )
    except Exception, e:
        print( "Exception while creating folder " + folder )
        print( str( e ) )


class Catalog:
    def __init__(self, catalog):
        self.catalog = catalog
        self.timestamp = datetime.datetime.now()
    def is_old(self):
        delta = datetime.datetime.now() - self.timestamp
        limit = int(__settings__.getSetting('catalog_refresh_rate'))
        print "delta: " + str(delta.seconds) + " / " + str(limit)
        if delta.seconds > limit:
            return True
        else:
            return False
class M6Replay:
    """
    main plugin class
    """
    debug_mode = False # Debug mode
    
    def __init__( self, *args, **kwargs ):
        print "==============================="
        print "  M6 Replay - Version: %s"%__version__
        print "==============================="
        print
        self.set_debug_mode()
        ok = False
        if self.debug_mode:
            print "URL du plugin:"
            print sys.argv[ 0 ] + sys.argv[ 2 ]
            print "ROOTDIR: %s"%ROOTDIR
            print "ADDON_DATA: %s"%ADDON_DATA
            print "CACHEDIR: %s"%CACHEDIR
            print "SYSTEM_PLATFORM: %s"%SYSTEM_PLATFORM
            print "CRYPTO_PATH: %s"%CRYPTO_PATH
            #print xbmc.getCondVisibility( "system.platform.xbox" )
            #print xbmc.getCondVisibility( "system.platform.osx" )
            #print xbmc.getCondVisibility( "system.platform.linux" )
            #print xbmc.getCondVisibility( "system.platform.windows" )
        
        # Check if directories in user data exist
        for i in range( len( dirCheckList ) ):
            verifrep( dirCheckList[i] ) 
        
        #xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category= __language__ ( 30000 )) # Catégories
        #xbmcplugin.setContent(int(sys.argv[1]), "Video")
        
        if ( not sys.argv[ 2 ] ):
            # Main Categories
            try:
                dico=self.get_categorie("http://www.m6replay.fr/catalogue/catalogueWeb3.xml")
                for cat in range(len(dico['categorie'])):
                    #infoLabels={ "Title": dico['categorie'][cat],
                    #             "count": cat}
                    ok = self.add_menu_item(dico['categorie'][cat], "display_pos="+str(dico['pos'][cat]), len(dico['categorie']), dico['image'][cat], True)               
                    # if user cancels, call raise to exit loop
                    if ( not ok ): raise
            except Exception, e:
                # oops, notify user what error occurred
                print_exc()
                
            # if successful (or not the play video case) and user did not cancel, add all the required sort methods and set plugin category
            if ( ok ):
                xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
                xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
       
        elif ( "display_pos=" in sys.argv[ 2 ] ):
            # Sub Categories
            try:
                dico=self.get_sub_categorie("http://www.m6replay.fr/catalogue/catalogueWeb3.xml",int(sys.argv[ 2 ].split("=")[1]))
                for cat in range(len(dico['categorie'])):
                    #infoLabels={ "Title": dico['categorie'][cat],
                    #             "count": cat}
                    ok = self.add_menu_item(dico['categorie'][cat], "display_produit="+str(dico['pos'][cat]), len(dico['categorie']), dico['image'][cat], True)
                    # if user cancels, call raise to exit loop
                    if ( not ok ): raise
            except Exception, e:
                # oops, notify user what error occurred
                print_exc()
                
            # if successful (or not the play video case) and user did not cancel, add all the required sort methods and set plugin category
            if ( ok ):
                xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
                xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
        
        elif ( "display_produit=" in sys.argv[ 2 ] ):
            # Produit
            try:
                dico=self.get_produit("http://www.m6replay.fr/catalogue/catalogueWeb3.xml",int(sys.argv[ 2 ].split("=")[1]))
                for produit in range(len(dico['nom'])):
                    infoLabels={ "Title": dico['nom'][produit],#+ " " + video["publication_date"],
                                 #"Rating":5,
                                 "Date": extractDateString( dico['date'][produit] ), # Format: u'17-12-2010'
                                 "Aired": extractDateString( dico['date'][produit] ), # Format: u'17-12-2010'
                                 "Duration": convertMin2Hour(dico['duree'][produit]),
                                 "Plot": bold_text( __language__ ( 30001 ) ) + add_pretty_color( self.convert_time_to_string( dico['date'][produit] ), color='FFFFCC00' ) + "[CR]" 
                                       + bold_text( __language__ ( 30002 ) ) + add_pretty_color( self.convert_time_to_string( dico['date_fin'][produit] ), color='FFFF0000' ) + "[CR][CR]" 
                                       + dico['description'][produit]}
                    #{ "TVShowTitle": "CNN Video", "Season": 1, "Episode": 1, "Title": video.title, "Genre": self.args.title, "Duration": video.duration, "Date": video.date, "Premiered": video.date }
                    #{ "Title": pname, "Duration": duration, "Label": name, "SortLetter":sort_letter, "date": date, "Year": year, "Plot":plot, "Rating":rating, "Path":path, "Director":director, "Genre":genre, "Tagline":tagline, "Writer":writer, "Studio": str(id)  }
                    ok = self.add_menu_item(dico['nom'][produit], "stream="+dico['path'][produit], len(dico['nom']), dico['image'][produit], False, itemInfoLabels=infoLabels)
                    # if user cancels, call raise to exit loop
                    if ( not ok ): raise
            except Exception, e:
                # oops, notify user what error occurred
                print_exc()
                
            # if successful (or not the play video case) and user did not cancel, add all the required sort methods and set plugin category
            if ( ok ):
                xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
                xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
                xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_DATE )
                xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
                #xbmcplugin.setContent(int(sys.argv[1]), "movies")
                xbmcplugin.setContent(int(sys.argv[1]), "episodes")
                
                
        elif ( "stream=" in sys.argv[ 2 ] ): 
            # Resolve URL in order to play a video   
            server_id = int( __settings__.getSetting( 'server' ) )
            rtmp = srv_list[server_id]['rtmp']
            app = srv_list[server_id]['app']
            playpath = re.sub( "[ ]", "%20", sys.argv[ 2 ].split("=")[1] )
            url = rtmp + " app=" + app + " swfUrl=http://l3.player.m6.fr/swf/StatPlaylibrary_20100401.swf playpath=" + playpath + " swfvfy=true socks=80.67.172.70:9050 flashVer=LNX 10,0,45,2"
            if rtmp =="":
                url = playpath

            # Play  video
            item = xbmcgui.ListItem(path=url)
        
            if self.debug_mode:
                print "Lecture de la video: %s"%url
            xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=item)


        # set our plugin category
        xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=__language__ ( 30000 ) )
        
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
           
    def set_debug_mode(self):
        debug =__settings__.getSetting('debug')
        if debug == 'true':
            self.debug_mode = True
        else:
            self.debug_mode = False
        print "M6 Replay: debug Mode:"
        print self.debug_mode
        
    def m6_decrypt(self, url):
        key = 'RWxGc2cuT3Q='
        no_catalog = False
        if os.path.isfile(os.path.join( CACHEDIR, "current_catalog")):
            f = open(os.path.join( CACHEDIR, "current_catalog"), 'r')
            try:
                #PB TODO
                catalog = pickle.load(f)
            except:
                no_catalog = True
            f.close()
        else:
            no_catalog = True

        if no_catalog or catalog.is_old():
            data = urllib.urlopen( url ).read()
            cipher = DES.new( base64.b64decode(key), DES.MODE_ECB )
            catalog_xml = cipher.decrypt( base64.standard_b64decode(data) )
            catalog_xml = string.rstrip( string.split( catalog_xml, '</template_exchange_WEB>' )[0] ) + '</template_exchange_WEB>'
            catalog = Catalog( catalog_xml )
            f = open(os.path.join( CACHEDIR, "current_catalog"), 'w')
            pickle.dump(catalog, f)
            #PB TODO
            f.close()
            if self.debug_mode:
                open(os.path.join(CACHEDIR,'catalog_m6.xml').encode('utf8'),"w").write(catalog_xml)
    
        return catalog.catalog     
    
    def get_categorie(self, xml_url):
        dico = {}
        categorie = []
        image = []
        pos= []
        dico['categorie']=categorie
        dico['image']=image
        dico['pos']=pos    
        cleartext=self.m6_decrypt(xml_url)
        xml_end = cleartext.rfind('>') + 1
        cleartext=cleartext[:xml_end]
        xmlrss=parseString(cleartext)
        
        for item in range(len(xmlrss.getElementsByTagName("template_exchange_WEB")[0].getElementsByTagName("categorie"))):
            if not xmlrss.getElementsByTagName("template_exchange_WEB")[0].getElementsByTagName("categorie")[item].hasAttribute("tag_dart"):
                categorie.append(xmlrss.getElementsByTagName("template_exchange_WEB")[0].getElementsByTagName("categorie")[item].getElementsByTagName("nom")[0].childNodes[0].data)
                image.append("http://images.m6replay.fr"+xmlrss.getElementsByTagName("template_exchange_WEB")[0].getElementsByTagName("categorie")[item].getAttribute("big_img_url"))
                pos.append(item)
        if self.debug_mode:
            print "Categories:"
            print dico    
        return dico
    
    def get_sub_categorie(self, xml_url,parent_pos):
        dico = {}
        categorie = []
        image = []
        pos= []
        dico['categorie']=categorie
        dico['image']=image
        dico['pos']=pos    
        cleartext=self.m6_decrypt(xml_url)
        xml_end = cleartext.rfind('>') + 1
        cleartext=cleartext[:xml_end]
        xmlrss=parseString(cleartext)
        
        for item in range(parent_pos+1,len(xmlrss.getElementsByTagName("template_exchange_WEB")[0].getElementsByTagName("categorie"))):
            if xmlrss.getElementsByTagName("template_exchange_WEB")[0].getElementsByTagName("categorie")[item].hasAttribute("tag_dart"):
                categorie.append(xmlrss.getElementsByTagName("template_exchange_WEB")[0].getElementsByTagName("categorie")[item].getElementsByTagName("nom")[0].childNodes[0].data)
                image.append("http://images.m6replay.fr"+xmlrss.getElementsByTagName("template_exchange_WEB")[0].getElementsByTagName("categorie")[item].getAttribute("big_img_url"))
                pos.append(item)
            else:
                break
        if self.debug_mode:
            print "Sous Categories:"
            print dico    
        return dico
    
    def get_produit(self, xml_url,parent_pos):
        dico = {}
        path = []
        image = []
        nom = []
        description = []
        date = []
        date_fin = []
        description = []
        duree = []
        dico['nom']=nom
        dico['path']=path
        dico['image']=image    
        dico['description']=description    
        dico['date']=date    
        dico['date_fin']=date_fin
        dico['duree']= duree
        cleartext=self.m6_decrypt(xml_url)
        xml_end = cleartext.rfind('>') + 1
        cleartext=cleartext[:xml_end]
        xmlrss=parseString(cleartext)
        
        for item in range(len(xmlrss.getElementsByTagName("template_exchange_WEB")[0].getElementsByTagName("categorie")[parent_pos].getElementsByTagName("produit"))):
           
           medias = xmlrss.getElementsByTagName("template_exchange_WEB")[0].getElementsByTagName("categorie")[parent_pos].getElementsByTagName("produit")[item].getElementsByTagName("fichemedia")
           
           # Parcours les "fiche_media" pour en extraire le lien vidéo. Normalement il n'y en a qu'une, sauf pour les séries VOSTFR/VF
           for media in medias:
               if( len(medias) == 1 ):
                   nom_media = ''
               else:
                   nom_media = " ["+media.getAttribute("langue")+"]"
               nom.append(xmlrss.getElementsByTagName("template_exchange_WEB")[0].getElementsByTagName("categorie")[parent_pos].getElementsByTagName("produit")[item].getElementsByTagName("nom")[0].childNodes[0].data + nom_media)        
               path.append(media.getAttribute("video_url"))
               duree.append(media.getAttribute("duree"))
               image.append("http://images.m6replay.fr"+xmlrss.getElementsByTagName("template_exchange_WEB")[0].getElementsByTagName("categorie")[parent_pos].getElementsByTagName("produit")[item].getAttribute("big_img_url"))
               description.append(xmlrss.getElementsByTagName("template_exchange_WEB")[0].getElementsByTagName("categorie")[parent_pos].getElementsByTagName("produit")[item].getElementsByTagName("resume")[0].childNodes[0].data)
               date.append(xmlrss.getElementsByTagName("template_exchange_WEB")[0].getElementsByTagName("categorie")[parent_pos].getElementsByTagName("produit")[item].getElementsByTagName("diffusion")[0].getAttribute("date"))
               date_fin.append(xmlrss.getElementsByTagName("template_exchange_WEB")[0].getElementsByTagName("categorie")[parent_pos].getElementsByTagName("produit")[item].getElementsByTagName("diffusion")[0].getAttribute("dateFin"))
        if self.debug_mode:
            print "Produits:"
            print dico    
        return dico
    
    def add_menu_item(self, title,action,size,thumb,folder, itemInfoLabels=None):
        if self.debug_mode:
            print "add_menu_item:"
            print "title = %s"%repr(title)
            print "thumb= %s"%(thumb)
            print "action= %s"%(action)
            print "itemInfoLabels:"
            print itemInfoLabels
            print
        item=xbmcgui.ListItem(title,thumbnailImage=thumb)
        cm = []    
        cm +=[ (title,"XBMC.RunPlugin("+sys.argv[ 0 ]+"?"+action+")")]
        url=sys.argv[ 0 ]+"?"+action
        
        # Clean the Thumb (cache thumbnail name being based on plugin URL)
        self.clean_thumbnail(url)
        
        item.addContextMenuItems(cm, replaceItems=True)
        if itemInfoLabels:
            iLabels = itemInfoLabels
        else:
            iLabels = { "Title": title }
        if not folder:
            item.setInfo( type="Video", infoLabels=iLabels)
            item.setProperty('IsPlayable', 'true')
            
        ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=item,isFolder=folder,totalItems=size)
        return ok

    def convert_time_to_string(self, xmlTime):
        """
        Convert time retrieved from XMl to a date in French such as 'samedi 2 janvier 2010'
        """
        time = convertStrTime2Time(xmlTime)
        return convertTime2FrenchString(time)

    def clean_thumbnail(self, video_url):
        """
        Clean thumb
        This is done because XBMC does not use the right thumb in the case of sub categories
        The reason is the Cache Thumb Name is based on a URL such as 'plugin://plugin.video.M6Replay/?display_pos=0'
        Which can reprensent different category (for the same URL) depending on the change in the XML
        """
        try:
            filename = xbmc.getCacheThumbName( video_url )
            filepath = xbmc.translatePath( os.path.join( THUMB_CACHE_PATH, filename[ 0 ], filename ) )
            if os.path.isfile( filepath ):
                os.remove(filepath)
                if self.debug_mode:
                    print "Deleted %s thumb matching to %s video"%(filepath, video_url)
            elif self.debug_mode:
                print "No thumb found %s thumb matching to %s video"%(filepath, video_url)
                
            return True
        except:
            print "Error: clean_thumbnail()"
            print_exc()
            return False
#######################################################################################################################    
# BEGIN !
#######################################################################################################################

if ( __name__ == "__main__" ):
    try:
        M6Replay()
    except:
        print_exc()
    
