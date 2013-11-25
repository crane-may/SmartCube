import bottle, sys, daemon, os
import web_server.server
import plugins.video.app_server
import plugins.video.decoder
from config import config

op = { 'run' : 'web' }
    
if 'web' in sys.argv:
    op['run'] = 'web'
elif 'video' in sys.argv:
    op['run'] = 'video'
elif 'decoder' in sys.argv:
    op['run'] = 'decoder'

def runit():
    print 'loading', op['run'], '...'
    if op['run'] == 'web':
        web_server.server.app.config.update(config)
        web_server.server.init()
        bottle.run(web_server.server.app, port = config['PORT'])
    
    if op['run'] == 'video':
        plugins.video.app_server.app.config.update(config)
        plugins.video.app_server.init()
        bottle.run(plugins.video.app_server.app, port = plugins.video.app_server.PORT)
        
    if op['run'] == 'decoder':
        plugins.video.decoder.CONFIG = config
        plugins.video.decoder.init()
        plugins.video.decoder.start()

if '-k' in sys.argv:
    os.system("ps aux | grep loader.py | grep -v grep | gawk '{print $2}' | xargs kill")
    exit(0)

if '-d' in sys.argv:
    with daemon.DaemonContext():
        runit()
else:
    runit()