import os, json, subprocess, time, redis, re

CONFIG = None
CACHE = None
r = None
ffmpeg = 'ffmpeg'

def init():
    global CACHE, r
    CACHE = CONFIG['CACHE']
    r = redis.StrictRedis(host='localhost', port=6379, db=0)

def touch_dir(p, file=''):
    if not os.path.exists(p):
        os.makedirs(p)
    return p+os.sep+file

def set_stats(path, st):
    r.hset('plugin:'+path, 'video:stats', st)
    print 'set_stats',st

def sha1(path):
    sig = r.hget('plugin:'+path, 'video:signature')
    if sig == None or sig == '':
        p = subprocess.Popen(['shasum', CONFIG['STORAGE']+path], stdout=subprocess.PIPE, shell=False)
        p.wait()
        result = re.findall("[0-9a-fA-F]{40}",p.stdout.read())
        
        if len(result) > 0:
            r.hset('plugin:'+path, 'video:signature', result[0])
            return result[0]
        else:
            return None
    else:
        return sig

def count_ts(path):
    f = open(path)
    ts = 0
    for l in f:
        if not l.startswith('#'):
            ts+=1
    f.close()
    return ts

def decode_video(path):
    tar_fullpath = CONFIG['STORAGE']+path
    info = json.loads(r.hget('plugin:'+path, 'video:info'))
    print path, info
    video = -1
    audio = -1
    for s in info['streams']:
        if video < 0 and s['codec_type'] == 'video':
            video = s['index']
            
        if audio < 0 and s['codec_type'] == 'audio':
            audio = s['index']
    
    sig = sha1(path)
    if not sig:
        set_stats(path,'-1')
        return
    wd = touch_dir(CACHE+os.sep+sig)
    
    set_stats(path,'3')
    final_m3u8 = wd+'v.m3u8'
    if not os.path.exists(final_m3u8):
        fake_m3u8 = wd+'fake.m3u8'
        fake_ts = touch_dir(wd+'fake_ts','%08d.ts')
        
        p = subprocess.Popen([ffmpeg,'-v','quiet','-y','-i',tar_fullpath,'-vcodec','copy','-vbsf','h264_mp4toannexb','-map','0:%d'%video,
            '-f','ssegment','-segment_time','120','-segment_format','mpegts','-segment_list',fake_m3u8,'-segment_list_size','9999',
            '-segment_list_type','m3u8',fake_ts])
        p.wait()
        
        fin = open(fake_m3u8)
        fout = open(final_m3u8, 'w')
        for l in fin:
            fout.write(re.sub('^/.*fake_','',l))
        fin.close()
        fout.close()
    
    set_stats(path,'4')
    real_m3u8 = wd+'real.m3u8'
    if not (os.path.exists(real_m3u8) and count_ts(real_m3u8) == count_ts(final_m3u8)):
        real_ts = touch_dir(wd+'ts','%08d.ts')
        
        p = subprocess.Popen([ffmpeg,'-v','quiet','-y','-i',tar_fullpath,'-vcodec','copy','-vbsf','h264_mp4toannexb','-acodec','copy',
            '-map','0:%d'%video,'-map','0:%d'%audio,
            '-f','ssegment','-segment_time','120','-segment_format','mpegts','-segment_list',real_m3u8,
            '-segment_list_type','m3u8',real_ts])
        p.wait()
        
    set_stats(path,'5')
    
# decode_video('/video/need4speed.mkv')
def start():    
    while True:
        time.sleep(1)
        path = r.lpop('plugin_video_queue')
        if path:
            decode_video(path)
