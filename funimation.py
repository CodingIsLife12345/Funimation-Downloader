

import argparse
import subprocess, requests
import ffmpy, html, http
import time, shutil
import glob, json, urllib
import sys, os, re
import base64

import API.client as funi_client
import API.config as funi_cfg
import pyfiglet
from rich import print
from typing import DefaultDict
from subprocess import Popen
from unidecode import unidecode
from m3u8 import parse as m3u8parser
from Crypto.Cipher import AES

from os.path import isfile, join

currentFile = 'funimation'
realPath = os.path.realpath(currentFile)
dirPath = os.path.dirname(realPath)
SESSION = requests.Session()

title = pyfiglet.figlet_format('Funimation Downloader', font='slant')
print(f'[magenta]{title}[/magenta]')
print("by -∞WKS∞-#3982")

parser = argparse.ArgumentParser()
parser.add_argument("--url", dest="url")
parser.add_argument("-o", "--output", dest="output", default="output")
parser.add_argument("--alang", dest="audiolang", type=lambda x: x.split(','))
parser.add_argument("--slang", dest="sublang", nargs="*", default=[])
parser.add_argument("--no-video", dest="novideo", action="store_true")
parser.add_argument("--na", "--no-audio", dest="noaudio", action="store_true")

parser.add_argument("--no-subs", dest="nosubs", action="store_true")
parser.add_argument("-q", "--quality", dest="customquality", type=lambda x: [x.rstrip('p')], default=[])
parser.add_argument("-s", dest="season")
parser.add_argument("-e", "--episode", dest="episodeStart")
parser.add_argument("--tag", type=str, required=False)
args = parser.parse_args()

def Funimation_Tool():
    
    def convert_size(size_bytes):
        if size_bytes == 0:
            return '0bps'
        else:
            s = round(size_bytes / 1000, 0)
            return '%ikbps' % s

    TOKEN, USER_ID = funi_client.LOGIN(SESSION)
    m = re.search(r'www.funimation.com\/shows\/(.+?)$', str(args.url))
    if m:
        if '/' in m[1]:
            SHOW_NAME = m[1][:-1]
        else:
            SHOW_NAME = m[1]

    country_code = SESSION.get('https://ipinfo.io/json', timeout=5).json()["country"]
    if not args.season:
        args.season = 'all'

    def alphanumericSort(l):
        def convert(text):
            if text.isdigit():
                return int(text)
            else:
                return text

        def alphanum_key(key):
            return [convert(c) for c in re.split('([0-9]+)', key)]

        return sorted(l, key=alphanum_key)

    global folderdownloader
    if args.output:
        if not os.path.exists(args.output):
            os.makedirs(args.output)
        os.chdir(args.output)
        if ":" in str(args.output):
            folderdownloader = str(args.output).replace('/','\\').replace('.\\','\\')
        else:
            folderdownloader = dirPath + str(args.output).replace('/','\\').replace('.\\','\\')
    else:
        folderdownloader = dirPath.replace('/','\\').replace('.\\','\\')

    def mediainfo_(file):
        mediainfo_output = subprocess.Popen([funi_cfg.MEDIAINFO, '--Output=JSON', '-f', file], stdout=subprocess.PIPE)
        mediainfo_json = json.load(mediainfo_output.stdout)
        return mediainfo_json

    def downloadFile2(link, file_name):
        with open(file_name, 'wb') as (f):
            response = SESSION.get(link, stream=True)
            total_length = response.headers.get('content-length')
            if total_length is None:
                f.write(response.content)
            else:
                dl = 0
                total_length = int(total_length)
                for data in response.iter_content(chunk_size=4096):
                    dl += len(data)
                    f.write(data)

    def m3u8_parsing(contentJson):
        
        hasAudio = False
        audio_List = []
        try:
            for x in contentJson:
                m3u8_master_json = m3u8parser(SESSION.get(x['URL']).text)
                for media in m3u8_master_json['media']:
                    if media['type'] == 'AUDIO':
                        audio_dict = {
                            'LanguageID':media["language"], 
                            'Profile':media['group_id'], 
                            'URL':media["uri"]}
                        audio_List.append(audio_dict)
            hasAudio = True
        except KeyError:
            hasAudio = False
            pass
        
        m3u8_master_json = m3u8parser(SESSION.get(str(dict(contentJson[(0)])['URL'])).text)
        video_list = []
        for playlist in m3u8_master_json['playlists']:
            resolution = re.split('x', playlist['stream_info']['resolution'])
            codecs = re.split(',', playlist['stream_info']['codecs'])

            video_dict = {
                'Width':resolution[0], 
                'Height':resolution[-1], 
                'VideoCodec':codecs[0],
                'AudioCodec':codecs[1],
                'URL':playlist["uri"], 
                'Bitrate':playlist['stream_info']['bandwidth']}
            video_list.append(video_dict)

        video_list = sorted(video_list, key=(lambda k: int(k['Bitrate'])))

        while args.customquality != [] and int(video_list[(-1)]['Height']) > int(args.customquality[0]):
            video_list.pop(-1)

        video_height = str(dict(video_list[(-1)])['Height'])

        return video_list, video_height, audio_List, hasAudio

    def get_episodes(ep_str, num_eps):
        eps = ep_str.split(',')
        eps_final = []

        for ep in eps:
            if '-' in ep:
                (start, end) = ep.split('-')
                start = int(start)
                end = int(end or num_eps)
                eps_final += list(range(start, end + 1))
            else:
                eps_final.append(int(ep))

        return eps_final

    def replace_words(x):
        x = re.sub(r'[]¡!"#$%\'()*+,:;<=>¿?@\\^_`{|}~[-]', '', x)
        x = x.replace('\\', '').replace('/', ' & ').replace('"', '')
        return unidecode(x)

    def get_content():
        resp = SESSION.get(url=funi_cfg.ENDPOINTS["SHOWS"] % (SHOW_NAME), headers=funi_cfg.COMMON_HEADERS, params={"deviceType":"web","region":country_code}).json()

        seasons = []
        if args.season:
            if args.season == 'all':
                seasons = 'all'
            elif ',' in args.season:
                seasons = [int(x) for x in args.season.split(',')]
            elif '-' in args.season:
                (start, end) = args.season.split('-')
                seasons = list(range(int(start), int(end) + 1))
            else:
                seasons = [int(args.season)]
                
        if seasons == 'all':
            seasons = [x['number'] for x in resp['seasons']]

        for season_num in seasons:
            season_id = resp['seasons'][int(season_num)-1]['id']
            seasonresp = SESSION.get(url=funi_cfg.ENDPOINTS["SEASONS"] % (season_id), headers=funi_cfg.COMMON_HEADERS, params={"deviceType":"web","region":country_code}).json()
            seriesTitle = replace_words(seasonresp['show']['name'])
            episodes_list_new = []
            for num, x in enumerate(seasonresp["episodes"], 1):
                episodeNumber = x['episodeNumber']
                episodeName = replace_words(x['name'])
                seriesName = f'{seriesTitle} S{season_num:0>2}E{episodeNumber:0>2} - {episodeName}'
                folderName = f'{seriesTitle} S{season_num:0>2}'

                episodes_list_new.insert(num - 0, {
                    'id': x['id'],
                    'contentId': x["contentId"],
                    'seriesName': seriesName,
                    'folderName': folderName,
                    'slug':x["slug"],
                    'episode_num': num,
                    'type':"show"})
                episode_list = sorted(episodes_list_new, key=lambda x: x['episode_num'])
            
            if episode_list == []:
                print('No episodes available')
                exit()

            if args.episodeStart:
                eps = get_episodes(args.episodeStart, len(episode_list))
                episode_list = [x for x in episode_list if x['episode_num'] in eps]

            for episode in episode_list:
                start_process(episode)

    def get_video(slug):
        funi_cfg.ANDROID_HEADERS["authorization"] = "Token %s" % (TOKEN)
        Xresp = SESSION.get(url=funi_cfg.ENDPOINTS["EP_DATA"] % (SHOW_NAME, slug), headers=funi_cfg.ANDROID_HEADERS).json()["items"][0]
        
        video_list = []
        for x in Xresp["media"]:
            for y in x["languages"]:
                if x["mediaType"] == "experience":
                    for z in x["mediaChildren"]:
                        if z["ext"] == "mp4":
                            video_dict = {
                                'id':x["id"],
                                'langId':y["code"]}
                            video_list.append(video_dict)

        audioList_new = []
        if args.audiolang:
            for x in video_list:
                langAbbrev = x['langId']
                if langAbbrev in list(args.audiolang):
                    audioList_new.append(x)
            audio_list = audioList_new
        
        videoList = []
        for b in audio_list:
            resp = SESSION.get(url=funi_cfg.ENDPOINTS["VIDEOS"] % (b['id']), headers=funi_cfg.ANDROID_HEADERS).json()#["items"][0]
            for y in resp["items"]:
                if "m3u8" in y["videoType"]:
                    m3u8Url = y["src"]
            videoList.append({"langId": b['langId'], "URL": m3u8Url})
        return videoList, get_subtitles(Xresp)

    def get_subtitles(x):
        subs_list = []
        for a in x["media"]:
            for b in a["mediaChildren"]:
                if b["ext"] == "srt":
                    subsDict = {
                        'LanguageId':b["languages"][0]["code"], 
                        'URL':b['image'],
                        'Language':b["languages"][0]["title"]}
                    subs_list.append(subsDict)

        AudioLanguageList = []
        for x in subs_list:
            AudioLanguageList.append(x['LanguageId'])

        AudioLanguageList = alphanumericSort(list(set(AudioLanguageList)))
        subsList_new = []
        for y in AudioLanguageList:
            counter = 0
            for x in subs_list:
                if x['LanguageId'] == y and counter == 0:
                    subsListDict_new = {
                        'Language':x['Language'],  
                        'LanguageId':x['LanguageId'], 
                        'URL':x['URL']}
                    subsList_new.append(subsListDict_new)
                    counter = counter + 1

        subs_list = subsList_new

        subsList_new = []
        if args.sublang:
            for x in subs_list:
                langAbbrev = x['LanguageId']
                if langAbbrev in list(args.sublang):
                    subsList_new.append(x)
            subs_list = subsList_new

        return subs_list

    def start_process(eps):
        contentInfo, subs_list = get_video(eps["slug"])
        video_list, video_height, audio_List, hasAudio = m3u8_parsing(contentInfo)
        video_bandwidth = dict(video_list[(-1)])['Bitrate']
        video_height = str(dict(video_list[(-1)])['Height'])
        video_width = str(dict(video_list[(-1)])['Width'])
        video_codec = str(dict(video_list[(-1)])['VideoCodec'])
        audio_codec = str(dict(video_list[(-1)])['AudioCodec'])
        m3u8url = str(dict(video_list[(-1)])['URL'])
        print()
        if not args.novideo:
            print(m3u8url)
            print('VIDEO - Bitrate: ' + convert_size(int(video_bandwidth)) + ' - Profile: ' + video_codec + ' - Dimensions: ' + video_width + 'x' + video_height)
            print()

        if not args.noaudio:
            if audio_List != []:
                for x in audio_List:
                    audio_lang = x['LanguageID']
                    print('AUDIO - Bitrate: 256kbps - Profile: ' + audio_codec + ' - Channels: 2 - Language: ' + audio_lang)
                    print()

        if not args.nosubs:
            if subs_list != []:
                for z in subs_list:
                    sub_lang = z['LanguageId']
                    print('SUBTITLE - Profile: NORMAL - Language: ' + sub_lang)
                    print()

        print('Name: '+ eps['seriesName'] + '\n')

        CurrentName = eps['seriesName']
        CurrentHeigh = str(video_height)
        VideoOutputName = folderdownloader + '\\' + str(eps['folderName']) + '\\' + str(CurrentName) + ' [' + str(CurrentHeigh) + 'p] [FUNI].mkv'

        if not os.path.isfile(VideoOutputName):
            if not args.nosubs:
                if subs_list != []:
                    for z in subs_list:
                        rg = re.search(r'(https?://.+?/FunimationStoreFront)', m3u8url)
                        if rg:
                            subUrl = re.sub(r'(https?://.+?/FunimationStoreFront)', rg[1], z['URL'])
                        inputSubtitle = CurrentName + " " + "(" + z['LanguageId'] + ").srt"
                        print(inputSubtitle)
                        if os.path.isfile(inputSubtitle):
                            print("\n" + inputSubtitle + "\nFile has already been successfully downloaded previously.\n")
                        else:
                            downloadFile2(subUrl, inputSubtitle)
                            print("Done!\n")

            if not args.novideo:
                inputVideo = CurrentName + ' [' + str(CurrentHeigh) + 'p] [FUNI].mp4'
                if os.path.isfile(inputVideo):
                    print('\n' + inputVideo + '\nFile has already been successfully downloaded previously.\n')
                else:
                    call_streamlink(m3u8url, inputVideo)

            if hasAudio == True:
                for x in audio_List:
                    audio_lang = x['LanguageID']
                    inputAudio = CurrentName + ' ' + '(' + audio_lang + ')' + '.mp4'
                    inputAudio_demuxed = CurrentName + ' ' + '(' + audio_lang + ')' + '.m4a'
                    if os.path.isfile(inputAudio) or os.path.isfile(inputAudio_demuxed):
                        print('\n' + inputAudio + '\nFile has already been successfully downloaded previously.\n')
                    else:
                        call_streamlink(x["URL"], inputAudio)
                        DemuxAudio(inputAudio)

            if not args.novideo:
                print('\nMuxing...')
                fname = do_muxer(CurrentName, 
                                eps['folderName'],
                                "show",
                                CurrentHeigh,
                                audio_List,
                                subs_list)

                if args.tag:
                    inputName = CurrentName + ' [' + CurrentHeigh + 'p] [FUNI].mkv'

                    release_group(base_filename=inputName,
                                default_filename=CurrentName,
                                folder_name=eps['folderName'],
                                type="show",
                                video_height=CurrentHeigh)

                for f in os.listdir():
                    if re.fullmatch(re.escape(CurrentName) + r'.*\.(mp4|m4a|h264|h265|eac3|ac3|srt|txt|avs|lwi|mpd)', f):
                        os.remove(f)
                print('Done!')
        else:
            print("File '" + str(VideoOutputName) + "' already exists.")

    def call_streamlink(m3u8_url, output):
        print(output)
        streamlink_opts = [
             "streamlink",
                m3u8_url, "best", "--quiet",
                "--hls-segment-threads", "10",
                '-o', output]
        subprocess.run(streamlink_opts, check=True)
        print('Done!')

    def do_muxer(filename, foldername, contentype, video_height, audio_List, subs_list):

        inputVideo = filename + ' [' + video_height + 'p] [FUNI].mp4'

        if isfile(inputVideo):
            print(inputVideo)
            video_filename = inputVideo
            if contentype == 'show':
                muxed_filename = join(foldername, inputVideo[:-4])
            else:
                muxed_filename = inputVideo[:-4]
        
        mkvmerge_command = [
            funi_cfg.MKVMERGE,
            '-o', muxed_filename + '.mkv',
        ]

        mkvmerge_command += [
            '--language', '0:und',
            '(', video_filename, ')',
        ]

        AudioExtensionsList = [
            ".m4a",
            ".aac"
        ]

        lang_dict = {
            'pt-BR': 'por',
            'es-ES': 'spa',
            'en-AU': 'eng',
            'en-GB': 'eng',
            'fr-CA': 'fre',
            'nl-BE': 'dut',
            'sr-Cyrl': 'srp',
            'sr-Latn': 'srp',
            'yue': 'chi',
            'zh-CN': 'chi',
            'zh-Hans': 'chi',
            'zh-Hant': 'chi',
            'zh-TW': 'chi',
        }

        lang_name_dict = {
            'pt': 'European',
            'pt-BR': 'Brazilian',
            'es': 'Latin American',
            'es-ES': 'European',
            'fr-CA': 'Canadian',
            'nl-BE': 'Flemish',
            'sr-Cyrl': 'Cyrillic',
            'sr-Latn': 'Latin',
            'yue': 'Cantonese',
            'zh-CN': 'Simplified',
            'zh-Hans': 'Simplified',
            'zh-Hant': 'Traditional',
            'zh-TW': 'Traditional',
        }
        for audio_track in audio_List:
            for audio_extension in AudioExtensionsList:
                audio_filename = filename + ' ' + '(' + audio_track["LanguageID"] + ')' + audio_extension
                if isfile(audio_filename):
                    lc = audio_track["LanguageID"]
                    lang = '0:{}'.format(lang_dict.get(lc, lc) or 'und')
                    if '-' in lang:
                        newlang = lang.split('-')[0]
                        lang = newlang

                    lang_name = '0:{}'.format(lang_name_dict.get(lc) or '')

                    mkvmerge_command += ["--language",
                                        lang,
                                        "--track-name",
                                        lang_name,
                                        "--default-track",
                                        "0:yes",
                                        "(",
                                        audio_filename,
                                        ")"]

        for subtitle_track in subs_list:
            subs_filename = filename + ' ' + '(' + subtitle_track["LanguageId"] + ').srt'
            if isfile(subs_filename):
                lang = '0:{}'.format(subtitle_track["LanguageId"])
                lang_name = '0:{}'.format(subtitle_track["Language"])

                if lang == '0:es':
                    default = 'yes'
                else:
                    default = 'no'
                mkvmerge_command = mkvmerge_command + ["--language",
                                                        lang,
                                                        "--sub-charset",
                                                        "0:UTF-8",
                                                        "--track-name",
                                                        lang_name,
                                                        "--default-track",
                                                        f"0:{default}",
                                                        "--forced-track",
                                                        "0:no",
                                                        "(",
                                                        subs_filename,
                                                        ")"]
        mkvmerge_process = subprocess.run(mkvmerge_command)

    def release_group(base_filename, default_filename, folder_name, type, video_height):
        if type=='show':
            video_mkv = os.path.join(folder_name, base_filename)
        else:
            video_mkv = base_filename
        
        mediainfo = mediainfo_(video_mkv)
        for v in mediainfo['media']['track']: # mediainfo do video
            if v['@type'] == 'Video':
                video_format = v['Format']

        video_codec = ''
        if video_format == "AVC":
            video_codec = 'H.264'

        for m in mediainfo['media']['track']: # mediainfo do audio
            if m['@type'] == 'Audio':
                codec_name = m['Format']
                channels_number = m['Channels']

        audio_codec = ''
        audio_channels = ''
        if codec_name == "AAC":
            audio_codec = 'AAC'
            
        if channels_number == "2":
            audio_channels = "2.0"

        audio_ = audio_codec + audio_channels

        # renomear arquivo
        default_filename = default_filename.replace('&', '.and.')
        default_filename = re.sub(r'[]!"#$%\'()*+,:;<=>?@\\^_`{|}~[-]', '', default_filename)
        default_filename = default_filename.replace(' ', '.')
        default_filename = re.sub(r'\.{2,}', '.', default_filename)

        output_name = '{}.{}p.FUNI.WEB-DL.{}.{}-{}'.format(default_filename, video_height, audio_, video_codec, args.tag)
        if type=='show':
            outputName = os.path.join(folder_name, output_name + '.mkv')
        else:
            outputName = output_name + '.mkv'

        os.rename(video_mkv, outputName)
        print(output_name)
        print("Done!")

    def DemuxAudio(inputAudio):
        outputAudio_mka = inputAudio.replace('.mp4', '.m4a')
        print('\nDemuxing audio...')
        mkvmerge_command = [funi_cfg.MKVMERGE, '-q', '--output', outputAudio_mka, '--language', '0:und', inputAudio]
        mkvmerge_process = subprocess.run(mkvmerge_command)
    
        print("{} -> {}".format(inputAudio, outputAudio_mka))
        time.sleep (50.0/1000.0)
        os.remove(inputAudio)
        print("Done!")

    get_content()
Funimation_Tool()