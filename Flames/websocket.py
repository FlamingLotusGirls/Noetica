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
    
    event_manager.addListener(handleMsg)
    
def shutdown():
    global websocket
    if websocket != None:
        logger.info("Websocket Shutdown")
        websocket.server_close()
        websocket = None

def handleMsg(msg):
    websocket.send_message_to_all(msg)
    

if __name__ == "__main__":
    import mock_event_producer
    import time
    
    logging.basicConfig(format='%(asctime)-15s %(levelname)s %(module)s %(lineno)d:  %(message)s', level=logging.DEBUG)

    try:
    
        event_manager.init()
        mock_event_producer.init()
        init(5001)
        
        while(True):
            time.sleep(10)
   
    except Exception as e:
        print "Exception occurs!", e
    except KeyboardInterrupt:
        print "Keyboard Interrupt!"
        
    event_manager.shutdown()
    mock_event_producer.shutdown()
    shutdown()


    