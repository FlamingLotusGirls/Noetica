#!/usr/bin/python


import logging
import os
import sys
import time
import Queue
import ConfigParser

import triggers
import flames_drv
import flames_controller
import flames_webserver
import event_manager
import websocket
import pattern_manager

# default parameters - configuration file overrides
HTTP_PORT     = 5000  
TRIGGER_FILE  = "triggers.json"
SEQUENCE_FILE = "sequences.json"
HYDRAULICS_ADDR = "localhost"
HTTP_PORT_HYDRAULICS = 9000
POSITION_PORT = 9001
WEBSOCKET_PORT = 5001
HOME_DIR = "/home/flaming/Noetica/"

logging.basicConfig(format='%(asctime)-15s %(levelname)s %(module)s %(lineno)d: %(message)s', level=logging.DEBUG)


if __name__ == '__main__':

    logging.warning("Noetica Flame Controller")
    if len(sys.argv) > 1:
        configFile = sys.argv[1]
    else:
        configFile = "../noetica.cfg"
    
    try:
        configParser = ConfigParser.ConfigParser() 
        configParser.read(configFile)
        HTTP_PORT     = int(configParser.get("flames", "httpPort", HTTP_PORT))
        HTTP_PORT_HYDRAULICS = int(configParser.get("hydraulics", "httpPort", HTTP_PORT_HYDRAULICS))
        POSITION_PORT = int(configParser.get("hydraulics", "streamPort", POSITION_PORT))
        TRIGGER_FILE  = configParser.get("flames", "triggerFile", TRIGGER_FILE)
        HYDRAULICS_ADDR = configParser.get("hydraulics", "server", HYDRAULICS_ADDR)
        SEQUENCE_FILE = configParser.get("flames", "sequenceFile", SEQUENCE_FILE)
        WEBSOCKET_PORT = configParser.get("flames", "websocketPort", WEBSOCKET_PORT)
        HOME_DIR = configParser.get("flames", "homeDir", HOME_DIR)
    except:
        logging.exception("Problem reading config file {}, defaulting configuration".format(configFile))

    try:
        # set cwd 
        os.chdir(HOME_DIR)
                
        # initialize pattern manager
        pattern_manager.init(HOME_DIR + SEQUENCE_FILE)
        
        # create queue for commands
        pooferCommandQueue = Queue.Queue()
                
        # Initialize Poofer board connection
        flames_drv.init(pooferCommandQueue, HOME_DIR)
        
        # Initialize the Event Manager
        event_manager.init()
        
        # Initialize high level flame interface
        flames_controller.init(pooferCommandQueue)
        
        # Initialize trigger system
        triggers.init(HOME_DIR + TRIGGER_FILE, HYDRAULICS_ADDR, POSITION_PORT )
        
        # Initialize the websocket
        websocket.init(int(WEBSOCKET_PORT))
        
        # Initialize webserver. This runs and runs and runs...
        flames_webserver.serve_forever(HTTP_PORT, HYDRAULICS_ADDR, HTTP_PORT_HYDRAULICS)
        
    except KeyboardInterrupt:
        print "Keyboard interrupt detected, terminating"
    except Exception as e:
        logging.exception("Unexpected exception:")
            
    triggers.shutdown()
    flames_drv.shutdown()
    flames_controller.shutdown()
    websocket.shutdown()
    event_manager.shutdown()
    pattern_manager.shutdown()
    
