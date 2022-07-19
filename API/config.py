from shutil import which
from os.path import dirname, realpath, join
from os import pathsep, environ

ENDPOINTS = {
    'LOGIN': 'https://prod-api-funimationnow.dadcdigital.com/api/auth/login/',
    'EP_DATA':'https://prod-api-funimationnow.dadcdigital.com/api/source/catalog/episode/%s/%s/',
    'SHOWS':'https://title-api.prd.funimationsvc.com/v2/shows/%s',
    'SEASONS': 'https://title-api.prd.funimationsvc.com/v1/seasons/%s',
    'VIDEOS': 'https://prod-api-funimationnow.dadcdigital.com/api/source/catalog/video/%s/signed/',
}

SCRIPT_PATH = dirname(realpath('funimation'))

BINARIES_FOLDER = join(SCRIPT_PATH, 'binaries')

MEDIAINFO_BINARY = 'mediainfo'
MP4DUMP_BINARY = 'mp4dump'
MKVMERGE_BINARY = 'mkvmerge'
FFMPEG_BINARY = 'ffmpeg'
ARIA2C_BINARY = 'aria2c'
SUBTITLE_EDIT_BINARY = 'subtitleedit'

# Add binaries folder to PATH as the first item
environ['PATH'] = pathsep.join([BINARIES_FOLDER, environ['PATH']])

MEDIAINFO = which(MEDIAINFO_BINARY)
MP4DUMP = which(MP4DUMP_BINARY)
MKVMERGE = which(MKVMERGE_BINARY)
FFMPEG = which(FFMPEG_BINARY)
ARIA2C = which(ARIA2C_BINARY)
SUBTITLE_EDIT = which(SUBTITLE_EDIT_BINARY)

LOGIN_HEADERS = {
    'authority': 'prod-api-funimationnow.dadcdigital.com',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
}

COMMON_HEADERS = {
    'authority': 'title-api.prd.funimationsvc.com',
    'accept': 'application/json, text/plain, */*',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
    'referer': 'https://www.funimation.com/',
}

ANDROID_HEADERS = {
    'Host': 'prod-api-funimationnow.dadcdigital.com',
    'devicetype': 'Android Phone',
    'accept-language': 'en-US',
    'user-agent': 'okhttp/3.14.9',
}