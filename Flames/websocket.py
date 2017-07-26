import logging
from threading import Thread
from websocket_server import WebsocketServer
import event_manager

logger = logging.getLogger("flames")
websocket = None

def init(port):
    global websocket
    logger.info("Websocket Init, port {}".format(port))
    websocket = WebsocketServer(port, '0.0.0.0')
    websocket.serve_forever() # XXX will this not return? Need to check that!!!
    event_manager.addListener(handleMsg)
    print "AFTER SERVE FOREVER!!!"
    
def shutdown():
    global websocket
    if websocket != None:
        logger.info("Websocket Shutdown")
        websocket.server_close()
        websocket = None

def handleMsg(msg):
    websocket.send_to_all(msg)
    