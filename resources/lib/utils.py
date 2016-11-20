#!/usr/bin/python
# -*- coding: utf-8 -*-

'''Various helper methods'''

import xbmcgui
import xbmc
import xbmcvfs
import sys
import urllib
from traceback import format_exc
import os
import unicodedata

ADDON_ID = "script.skin.helper.skinbackup"
KODI_VERSION = int(xbmc.getInfoLabel("System.BuildVersion").split(".")[0])
SKIN_NAME = xbmc.getSkinDir().decode("utf-8").replace("skin.", "").split("krypton")[0].split("jarvis")[0]


def log_msg(msg, loglevel=xbmc.LOGDEBUG):
    '''log to kodi logfile'''
    if isinstance(msg, unicode):
        msg = msg.encode('utf-8')
    xbmc.log("Skin Helper Backup --> %s" % msg, level=loglevel)


def log_exception(modulename, exceptiondetails):
    '''helper to properly log exception details'''
    log_msg(format_exc(sys.exc_info()))
    log_msg("ERROR in %s ! --> %s" % (modulename, exceptiondetails), xbmc.LOGERROR)


def kodi_json(jsonmethod, params=None, returntype=None):
    '''get info from the kodi json api'''
    import json
    kodi_json = {}
    kodi_json["jsonrpc"] = "2.0"
    kodi_json["method"] = jsonmethod
    if not params:
        params = {}
    kodi_json["params"] = params
    kodi_json["id"] = 1
    json_response = xbmc.executeJSONRPC(json.dumps(kodi_json).encode("utf-8"))
    json_object = json.loads(json_response.decode('utf-8', 'replace'))
    result = None
    if 'result' in json_object:
        # look for correct returntype
        if isinstance(json_object['result'], dict):
            for key, value in json_object['result'].iteritems():
                if not key == "limits":
                    result = value
                    break
        else:
            return json_object['result']
    return result


def recursive_delete_dir(fullpath):
    '''helper to recursively delete a directory'''
    success = True
    dirs, files = xbmcvfs.listdir(fullpath)
    for file in files:
        success = xbmcvfs.delete(os.path.join(fullpath, file))
    for dir in dirs:
        success = recursive_delete_dir(os.path.join(fullpath, dir))
    success = xbmcvfs.rmdir(fullpath)
    return success


def get_clean_image(image):
    '''helper to strip all kodi tags/formatting of an image path/url'''
    if image and "image://" in image:
        image = image.replace("image://", "")
        image = urllib.unquote(image.encode("utf-8"))
        if image.endswith("/"):
            image = image[:-1]
    if not isinstance(image, unicode):
        image = image.decode("utf8")
    if "music@" in image:
        # filter out embedded covers
        image = ""
    return image


def normalize_string(text):
    '''normalize string, strip all special chars'''
    text = text.replace(":", "")
    text = text.replace("/", "-")
    text = text.replace("\\", "-")
    text = text.replace("<", "")
    text = text.replace(">", "")
    text = text.replace("*", "")
    text = text.replace("?", "")
    text = text.replace('|', "")
    text = text.replace('(', "")
    text = text.replace(')', "")
    text = text.replace("\"", "")
    text = text.strip()
    text = text.rstrip('.')
    if not isinstance(text, unicode):
        text = text.decode("utf-8")
    text = unicodedata.normalize('NFKD', text)
    return text


def add_tozip(src, zf, abs_src):
    '''helper method'''
    dirs, files = xbmcvfs.listdir(src)
    for filename in files:
        filename = filename.decode("utf-8")
        log_msg("zipping %s" % filename)
        filepath = xbmc.translatePath(os.path.join(src, filename)).decode("utf-8")
        absname = os.path.abspath(filepath)
        arcname = absname[len(abs_src) + 1:]
        try:
            # newer python can use unicode for the files in the zip
            zf.write(absname, arcname)
        except Exception:
            # older python version uses utf-8 for filenames in the zip
            zf.write(absname.encode("utf-8"), arcname.encode("utf-8"))
    for dir in dirs:
        add_tozip(os.path.join(src, dir), zf, abs_src)
    return zf


def zip_tofile(src, dst):
    '''method to create a zip file from all files/dirs in a path'''
    import zipfile
    zf = zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED)
    abs_src = os.path.abspath(xbmc.translatePath(src).decode("utf-8"))
    zf = add_tozip(src, zf, abs_src)
    zf.close()


def unzip_fromfile(zip_file, dest_path):
    '''method to unzip a zipfile to a destination path'''
    import shutil
    import zipfile
    zip_file = xbmc.translatePath(zip_file).decode("utf-8")
    dest_path = xbmc.translatePath(dest_path).decode("utf-8")
    log_msg("START UNZIP of file %s  to path %s " % (zip_file, dest_path))
    f = zipfile.ZipFile(zip_file, 'r')
    for fileinfo in f.infolist():
        filename = fileinfo.filename
        if not isinstance(filename, unicode):
            filename = filename.decode("utf-8")
        log_msg("unzipping " + filename)
        if "\\" in filename:
            xbmcvfs.mkdirs(os.path.join(dest_path, filename.rsplit("\\", 1)[0]))
        elif "/" in filename:
            xbmcvfs.mkdirs(os.path.join(dest_path, filename.rsplit("/", 1)[0]))
        filename = os.path.join(dest_path, filename)
        log_msg("unzipping " + filename)
        try:
            # newer python uses unicode
            outputfile = open(filename, "wb")
        except Exception:
            # older python uses utf-8
            outputfile = open(filename.encode("utf-8"), "wb")
        # use shutil to support non-ascii formatted files in the zip
        shutil.copyfileobj(f.open(fileinfo.filename), outputfile)
        outputfile.close()
    f.close()
    log_msg("UNZIP DONE of file %s  to path %s " % (zip_file, dest_path))
