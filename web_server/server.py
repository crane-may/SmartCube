from bottle import get, post, request, run, static_file, abort, response, redirect
import os, json, subprocess, time, redis

ROOT = '/Users/claire/Desktop/WirelessStorage/web_server'
STORAGE = '/Users/claire/Desktop/WirelessStorage/storage'
APPS = '/Users/claire/Desktop/WirelessStorage/apps'
PORT = 8080

PLUGIN_CONFIGS = {'BASE':{'port':PORT}}
for app in os.listdir(APPS):
    p = APPS+os.sep+app+os.sep+"config.js"
    if os.path.exists(p):
        f = open(p)
        dic = json.loads(f.read())
        PLUGIN_CONFIGS[dic['name']] = dic
        f.close()

r = redis.StrictRedis(host='localhost', port=6379, db=0)

@get('/')
def index(name=''):
    return static_file('index.html', root=ROOT)

@get('/PLUGIN/all.js')
def doPlugin():
    ret = ""
    for app in os.listdir(APPS):
        p = APPS+os.sep+app+os.sep+"plugin.js"
        if os.path.exists(p):
            f = open(p)
            ret += f.read()
            f.close()
            
    ret = 'var PLUGIN_CONFIGS = '+json.dumps(PLUGIN_CONFIGS)+';' + ret
    return ret

@get('/STATIC/<path:path>')
def doStatic(path = ''):
    return static_file(path, root=ROOT)

@get('/GET/')
@get('/GET/<path:path>')
def doGet(path = ''):
    fullp = STORAGE+os.sep+path
    if os.path.exists(fullp) :
        if os.path.isdir(fullp):
            ret = []
            for nm in os.listdir(fullp):
                o = {}
                o["name"] = nm
                o["isDir"] = os.path.isdir(fullp+os.sep+nm)
                if o["isDir"]:
                    o["size"] = 0
                else:
                    o["size"] = os.path.getsize(fullp+os.sep+nm)
                    o["plugin"] = r.hgetall("plugin:/"+path+os.sep+nm)
                ret.append(o)
                
            response.content_type = 'application/json; charset=utf8'
            return json.dumps({"result":ret})
        else:
            return static_file(path, root=STORAGE)
    else :
        abort(404, "not found file or director")


@get('/PLUGIN/<name>/<path:path>')
def doPlugin(name = '', path = ''):
    if PLUGIN_CONFIGS.has_key(name):
        h = request.headers.get("Host").replace(":8080", ":%d"%PLUGIN_CONFIGS[name]["port"])
        redirect('http://'+h+'/'+path)



#################################################################

@post('/POST/<path:path>')
def doPost(path = ''):
    pass

@get('/DELETE/<path:path>')
def doDelete(path = ''):
    pass

run(host='0.0.0.0', port=PORT)
