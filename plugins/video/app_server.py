from bottle import Bottle, get, post, request, run, static_file, abort, response, redirect
import os, json, subprocess, time, redis, re, chardet

# video:stats
# 0: not process
# 1: info extracted
# 2: ready to decode
# 3: indexing
# 4: decoding
# 5: done

app = Bottle()
CACHE = None
r = None
PORT = None

def init():
    global CACHE, r, PORT
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    CACHE = app.config['CACHE']
    f = open(app.config['ROOT']+'/plugins/video/config.js')
    PORT = json.loads(f.read())['port']
    f.close()
    if not os.path.exists(CACHE):
        os.makedirs(CACHE)
    

def filter(d, keylist):
    if type(d) == dict:
        keys = d.keys()
        for k in keys:
            if k in keylist:
                filter(d[k], keylist)
            else:
                del(d[k])
                
    elif type(d) == list:
        for i in d:
            filter(i, keylist)

# plugin:<path>
#   video:stats
#   video:info

@app.get('/INFO/<path:path>')
def doInfo(path = ''):
    path = '/'+path
    p = subprocess.Popen(['ffprobe','-v','quiet','-print_format','json','-show_format','-show_streams',app.config['STORAGE']+path], stdout=subprocess.PIPE, shell=False)
    p.wait()
    result = json.loads(p.stdout.read())
    filter(result, ['streams','index','codec_name','codec_type','width','height','tags','language','format','format_name','duration'])
    r.hset('plugin:'+path, 'video:stats', '1')
    r.hset('plugin:'+path, 'video:info', json.dumps(result))
    return "location.reload();"

# plugin_video_queue
@app.get('/DECODE/<path:path>')
def doDecode(path = ''):
    path = '/'+path
    stats = r.hget('plugin:'+path, 'video:stats')
    if stats == '1':
        r.hset('plugin:'+path, 'video:stats', '2')
        r.lpush('plugin_video_queue', path)
    return "location.reload();"

@app.get('/PLAY/<path:path>')
def doPlay(path = ''):
    path = '/'+path
    fullpath = CACHE+path
    wk = CACHE+'/'+path.split('/')[1]
    
    if path.endswith('vsub.m3u8') and not os.path.exists(fullpath):
        srtfullpath = app.config['STORAGE'] + request.query.get('srt')
        if os.path.exists(srtfullpath):
            lasttimeline = ''
            
            vtt = wk +'/sub.vtt'
            if not os.path.exists(vtt):
                fin = open(srtfullpath)
                subtitle = fin.read()
                enc = chardet.detect(subtitle)['encoding']
                if enc != 'utf-8':
                    subtitle = subtitle.decode(enc).encode('utf-8')
                fin.close()
                
                fout = open(vtt, 'w')
                fout.write('WEBVTT\nX-TIMESTAMP-MAP=MPEGTS:0,LOCAL:00:00:00.000\n\n')
                
                for l in re.split('\r?\n', subtitle):
                    if re.search('-[ -]>',l):
                        l = l.replace('- >','-->').replace(',','.')
                        lasttimeline = l
                    fout.write(l+"\n")
                fout.close()
                fin.close()
            
            sub_m3u8 = wk + '/sub.m3u8'
            if not os.path.exists(sub_m3u8):
                times = re.search('\d+:\d+:\d+[,.]\d+\s+-[ -]>\s+(\d+):(\d+):(\d+)[,.]\d+\s*',lasttimeline)
                if times:
                    maxtime = int(times.group(1))*3600 + int(times.group(2))*60 + int(times.group(3)) + 1
                    fout = open(sub_m3u8, 'w')
                    fout.write('#EXTM3U\n#EXT-X-TARGETDURATION:%d\n#EXT-X-VERSION:3\n#EXT-X-MEDIA-SEQUENCE:1\n#EXTINF:%d.0,\nsub.vtt\n#EXT-X-ENDLIST'%(maxtime,maxtime))
                    fout.close()
            
                    fout = open(fullpath, 'w')
                    fout.write('#EXTM3U\n#EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",NAME="English",DEFAULT=YES,AUTOSELECT=YES,FORCED=NO,LANGUAGE="eng",URI="sub.m3u8"\n#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=10000,SUBTITLES="subs"\nv.m3u8')
                    fout.close()
    
    if path.endswith('.ts'):
        real_m3u8 = wk +'/real.m3u8'
        if os.path.exists(real_m3u8):
            filename = path.split('/')[-1]
            
            s = 'xxx'
            while s.find(filename) < 0 :
                if s != 'xxx':
                    time.sleep(2)
                f = open(real_m3u8)
                s = f.read()
                f.close()
                
            return static_file(path, root=CACHE)
    else:
        if os.path.exists(fullpath):
            return static_file(path, root=CACHE)
            
    abort(404, "not found file")
