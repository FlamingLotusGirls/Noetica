import logging
from threading import Thread
from websocket_server import WebsocketServer
import event_manager

logger = logging.getLogger("flames")
websocket = None
websocketThread = None

def init(port):
    global websocket
    global websocketThread
    logger.info("Websocket Init, port {}".format(port))
    websocket = WebsocketServer(port, '0.0.0.0')
    websocketThread = Thread(target=websocket.serve_forever)
    
    #websocket.serve_forever() 
    event_manager.addListener(handleMsg)
    
def shutdown():
    global websocket
    if websocket != None:
        logger.info("Websocket Shutdown")
        websocket.server_close()
        websocket = None

def handleMsg(msg):
    websocket.send_to_all(msg)
    