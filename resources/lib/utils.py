# -*- coding: cp1252 -*-

import StringIO
import os
import re
import time



def convertStrTime2Time(strTime):
    """
    Parse and convert '2010-12-31 20:45:00' format to a 'struct_time' as returned by gmtime() or localtime()
    Example of 'struct_time':
    time.struct_time(tm_year=2010, tm_mon=12, tm_mday=31, tm_hour=20, tm_min=45, tm_sec=0, tm_wday=4, tm_yday=365, tm_isdst=-1)
    """
    return time.strptime(strTime, "%Y-%m-%d %H:%M:%S")  

def convertTime2FrenchString(time):
    """
    Convert 'struct_time' to string (french representation) such as 'SAMEDI 1 JANVIER 2010 - 20H20"
    Example of 'struct_time':
    time.struct_time(tm_year=2010, tm_mon=12, tm_mday=31, tm_hour=20, tm_min=45, tm_sec=0, tm_wday=4, tm_yday=365, tm_isdst=-1)
    """
    try:
        int2monthTxt = [ u'INVALIDE'  , 
                         u'JANVIER'  , # We start at 1
                         u'FEVRIER'  , 
                         u'MARS'     , 
                         u'AVRIL'    , 
                         u'MAI'      , 
                         u'JUIN'     , 
                         u'JUILLET'  , 
                         u'AOUT'     , 
                         u'SEPTEMBRE', 
                         u'OCTOBRE'  , 
                         u'NOVEMBRE' , 
                         u'DECEMBRE'  
                        ]
        
        int2wdayTxt =  [ u'LUNDI'   , # We start at 0
                         u'MARDI'   , 
                         u'MERCREDI', 
                         u'JEUDI'   , 
                         u'VENDREDI', 
                         u'SAMEDI'  , 
                         u'DIMANCHE'
                       ]
        
        timeStr = "%s %d %s %d - %d:%d"%(int2wdayTxt[time.tm_wday], time.tm_mday, int2monthTxt[time.tm_mon], time.tm_year, time.tm_hour, time.tm_min)
    except:
        timeStr = ""
    return timeStr

def extractDateString(strTime):
    """
    Extract and convert time to the Format: u'17-12-2010' (used by Info Label Date)
    """
    try:
        s_time = convertStrTime2Time(strTime)
        #timeStr = strTime.split(" ")[0]
        timeStr = "%02d-%02d-%d"%(s_time.tm_mday,s_time.tm_mon, s_time.tm_year)
    except:
        timeStr = ""
    return timeStr

def convertMin2Hour(minStr):
    """
    Convert Minutes String to 'h:mm' string format used by Info Label Duration in XBMC
    """
    min = int(minStr)
    time = "%d:%02d"%( (min // 60), min%60 )
    return time 
    
def url_join(*args):
    """
    Join any arbitrary strings into a forward-slash delimited list.
    Do not strip leading / from first element, nor trailing / from last element.
    From Coders Eye
    """
    if len(args) == 0:
        return ""

    if len(args) == 1:
        return str(args[0])

    else:
        args = [str(arg).replace("\\", "/") for arg in args]

        work = [args[0]]
        for arg in args[1:]:
            if arg.startswith("/"):
                work.append(arg[1:])
            else:
                work.append(arg)

        joined = reduce(os.path.join, work)

    return joined.replace("\\", "/")

#NOTE: CE CODE PEUT ETRE REMPLACER PAR UN CODE MIEUX FAIT
def add_pretty_color( word, start="all", end=None, color=None ):
    """ FONCTION POUR METTRE EN COULEUR UN MOT OU UNE PARTIE """
    try:
        if color and start == "all":
            pretty_word = "[COLOR=" + color + "]" + word + "[/COLOR]"
        else:
            pretty_word = []
            for letter in word:
                if color and letter == start:
                    pretty_word.append( "[COLOR=" + color + "]" )
                elif color and letter == end:
                    pretty_word.append( letter )
                    pretty_word.append( "[/COLOR]" )
                    continue
                pretty_word.append( letter )
            pretty_word = "".join( pretty_word )
        return pretty_word
    except:
        print_exc()
        return word

def bold_text( text ):
    """ FONCTION POUR METTRE UN MOT GRAS """
    return "[B]%s[/B]" % ( text, )


def italic_text( text ):
    """ FONCTION POUR METTRE UN MOT ITALIQUE """
    return "[I]%s[/I]" % ( text, )

def set_xbmc_carriage_return( text ):
    """ only for xbmc """
    text = text.replace( "\r\n", "[CR]" )
    text = text.replace( "\n\n", "[CR]" )
    text = text.replace( "\n",   "[CR]" )
    text = text.replace( "\r\r", "[CR]" )
    text = text.replace( "\r",   "[CR]" )
    text = text.replace( "</br>",   "[CR]" )
    return text


def strip_off( text, by="", xbmc_labels_formatting=False ):
    """ FONCTION POUR RECUPERER UN TEXTE D'UN TAG """
    if xbmc_labels_formatting:
        #text = re.sub( "\[url[^>]*?\]|\[/url\]", by, text )
        text = text.replace( "[", "<" ).replace( "]", ">" )
    return re.sub( "(?s)<[^>]*>", by, text )
