from bottle import Bottle, get, post, request, run, static_file, abort, response, redirect
import os, json, subprocess, time, redis, re

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

def fileInfo(nm, fullpath, path):
    o = {}
    o["name"] = nm
    o["isDir"] = os.path.isdir(fullpath)
    if o["isDir"]:
        o["size"] = 0
    else:
        o["size"] = os.path.getsize(fullpath)
        o["plugin"] = r.hgetall("plugin:"+path)
    return o

@app.get('/LS/')
@app.get('/LS/<path:path>')
def doGet(path = ''):
    path = '/'+path
    fullp = app.config['STORAGE']+path
    if os.path.exists(fullp) :
        if os.path.isdir(fullp):
            ret = []
            for nm in os.listdir(fullp):
                ret.append(fileInfo(nm, fullp+'/'+nm, path+'/'+nm))
                
            response.content_type = 'application/json; charset=utf8'
            return json.dumps({"result":ret})
        else:
            response.content_type = 'application/json; charset=utf8'
            return json.dumps({"result":fileInfo(path.split('/')[-1], fullp, path)})
    else :
        abort(404, "not found file or director")


#################################################################

@app.post('/POST')
def doPost():
    ref = request.forms.get('ref')
    path = request.forms.get('path')
    
    if request.forms.get('isDir', False):
        name = request.forms.get('name')
        os.makedirs( app.config['STORAGE']+path+'/'+name )
    else:
        upload = request.files.get('upload')
        with open(app.config['STORAGE']+path+'/'+upload.filename, 'wb') as open_file:
            open_file.write(upload.file.read())
    
    redirect(ref)

@app.post('/MV')
def doMv():
    oldpath = request.forms.get('old')
    newpath = request.forms.get('new')
    os.rename(app.config['STORAGE']+oldpath, app.config['STORAGE']+newpath)
    redirect('/#'+newpath)
    
@app.post('/DELETE/<path:path>')
def doDelete(path = ''):
    path = '/'+path
    if path.find('..') < 0:
        os.system("rm -rf '"+app.config['STORAGE']+path+"'")
    father = re.sub('/[^/]+$','',path)
    redirect('/#'+father)
    