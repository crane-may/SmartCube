from bottle import Bottle, get, post, request, run, static_file, abort, response, redirect
import os, json, subprocess, time, redis

app = Bottle()
r = None
PLUGINS = None
WEB = None
PLUGIN_CONFIGS = None

def init():
    global r, PLUGINS, WEB, PLUGIN_CONFIGS
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    WEB = app.config['ROOT']+'/web_server'
    PLUGINS = app.config['ROOT']+'/plugins'
    
    plugin_configs = {'BASE':{'port':app.config['PORT']}}
    for plugin in os.listdir(PLUGINS):
        p = PLUGINS+'/'+plugin+"/config.js"
        if os.path.exists(p):
            f = open(p)
            dic = json.loads(f.read())
            plugin_configs[dic['name']] = dic
            f.close()
    PLUGIN_CONFIGS = plugin_configs

@app.get('/')
def index(name=''):
    return static_file('index.html', root=WEB)

@app.get('/PLUGIN/all.js')
def doPlugin():
    ret = ""
    for plugin in os.listdir(PLUGINS):
        p = PLUGINS+'/'+plugin+"/plugin.js"
        if os.path.exists(p):
            f = open(p)
            ret += f.read()
            f.close()
    ret = 'var PLUGIN_CONFIGS = '+json.dumps(PLUGIN_CONFIGS)+';' + ret
    return ret

@app.get('/STATIC/<path:path>')
def doStatic(path = ''):
    return static_file(path, root=WEB)

@app.get('/GET/')
@app.get('/GET/<path:path>')
def doGet(path = ''):
    fullp = app.config['STORAGE']+'/'+path
    if os.path.exists(fullp) :
        if os.path.isdir(fullp):
            ret = []
            for nm in os.listdir(fullp):
                o = {}
                o["name"] = nm
                o["isDir"] = os.path.isdir(fullp+'/'+nm)
                if o["isDir"]:
                    o["size"] = 0
                else:
                    o["size"] = os.path.getsize(fullp+'/'+nm)
                    o["plugin"] = r.hgetall("plugin:/"+path+'/'+nm)
                ret.append(o)
                
            response.content_type = 'application/json; charset=utf8'
            return json.dumps({"result":ret})
        else:
            return static_file(path, root=app.config['STORAGE'])
    else :
        abort(404, "not found file or director")


#################################################################

@app.post('/POST/<path:path>')
def doPost(path = ''):
    pass

@app.get('/DELETE/<path:path>')
def doDelete(path = ''):
    pass
