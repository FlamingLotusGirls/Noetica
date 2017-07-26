#!/usr/bin/python


import logging
import sys
import time
import Queue
import ConfigParser

import triggers
import flames_drv
import flames_highlevel
import flame_api
import event_manager
import websocket
import pattern_manager

# default parameters - configuration file overrides
HTTP_PORT     = 9000  
POSITION_PORT = 9001
TRIGGER_FILE  = "./triggers.json"
SEQUENCE_FILE = "./sequences.json"
HYDRAULICS_ADDR = "localhost"
WEBSOCKET_PORT = 5000

logging.basicConfig(format='%(asctime)-15s %(levelname)s %(module)s %(lineno)d: %(message)s', level=logging.DEBUG)


if __name__ == '__main__':

    logging.info("Noetica Flame Controller")
    if len(sys.argv) > 1:
        configFile = sys.argv[1]
    else:
        configFile = "../noetica.cfg"
    
    try:
        configParser = ConfigParser.ConfigParser() 
        configParser.read(configFile)
        HTTP_PORT     = int(configParser.get("flames", "httpPort", HTTP_PORT))
        POSITION_PORT = int(configParser.get("hydraulics", "streamPort", POSITION_PORT))
        TRIGGER_FILE  = configParser.get("flames", "triggerFile", TRIGGER_FILE)
        HYDRAULICS_ADDR = configParser.get("hydraulics", "server", HYDRAULICS_ADDR)
        SEQUENCE_FILE = configParser.get("flames", "sequenceFile", SEQUENCE_FILE)
        WEBSOCKET_PORT = configParser.get("flames", "websocketPort", WEBSOCKET_PORT)
    except:
        logging.exception("Problem reading config file {}, defaulting configuration".format(configFile))

    try:
        # initialize pattern manager
        pattern_manager.init(SEQUENCE_FILE)
        
        # create queue for commands
        pooferCommandQueue = Queue.Queue()
                
        # Initialize Poofer board connection
        flames_drv.init(pooferCommandQueue, SEQUENCE_FILE)
        
        # Initialize the Event Manager
        event_manager.init()
        
        # Initialize high level flame interface
        flames_highlevel.init(pooferCommandQueue)
        
        # Initialize trigger system
        triggers.init(TRIGGER_FILE, HYDRAULICS_ADDR, POSITION_PORT)
        
        # Initialize the websocket
        websocket.init(int(WEBSOCKET_PORT))
        
        # Initialize webserver. This runs and runs and runs...
        flame_api.serve_forever(HTTP_PORT)
        
    except KeyboardInterrupt:
        print "Keyboard interrupt detected, terminating"
    except Exception as e:
        logging.exception("Unexpected exception:")
            
    triggers.shutdown()
    flames_drv.shutdown()
    flames_highlevel.shutdown()
    websocket.shutdown()
    event_manager.shutdown()
    pattern_manager.shutdown()
    
