#!/usr/bin/python

import BaseHTTPServer
import ConfigParser
import logging
import os
import sys


import hydraulics_drv
import hydraulics_playback
import hydraulics_webserver
import hydraulics_stream
import event_manager
import attract_manager

# default parameters - configuration file overrides
HTTP_PORT = 9000 
POSITION_PORT = 9001
HYDRAULICS_POLL_INTERVAL = 200  # hardware poll interval, in ms
PLAYBACK_DIR = "playbacks/"
HOME_DIR = "/home/flaming/Noetica/"
INACTIVITY_TIMEOUT = 30 #in seconds


logging.basicConfig(format='%(asctime)-15s %(levelname)s %(module)s %(lineno)d:  %(message)s', level=logging.DEBUG)

if __name__ == '__main__':

    logging.info("Noetica Hydraulics")
    if len(sys.argv) > 1:
        configFile = sys.argv[1]
    else:
        configFile = "../noetica.cfg"
        
    httpd = None
    
    try:
        configParser = ConfigParser.ConfigParser() 
        configParser.read(configFile)
        HTTP_PORT     = int(configParser.get("hydraulics", "httpPort", HTTP_PORT))
        POSITION_PORT = int(configParser.get("hydraulics", "streamPort", POSITION_PORT))
        HYDRAULICS_POLL_INTERVAL = int(configParser.get("hydraulics", "pollInterval", HYDRAULICS_POLL_INTERVAL))
        PLAYBACK_DIR = configParser.get("hydraulics", "playbackDir", PLAYBACK_DIR)
        INACTIVITY_TIMEOUT = configParser.get("hydraulics", "inactivityTimeout", INACTIVITY_TIMEOUT)
        HOME_DIR = configParser.get("hydraulics", "homeDir", HOME_DIR)
    except Exception:
        logging.exception("Problem reading config file {}, defaulting configuration".format(configFile))

    try:
        # set cwd 
        os.chdir(HOME_DIR)
        
        # set debug level
        
        # initialize event manager
        event_manager.init()
        
        # setup position streamer 
        hydraulics_stream.init(POSITION_PORT)

        # setup driver 
        hydraulics_drv.init(HYDRAULICS_POLL_INTERVAL)

        # setup playback - NB - this is a set of utility functions, not own thread
        hydraulics_playback.init(HOME_DIR + PLAYBACK_DIR)    
        
        # set up attract mode
        attract_manager.init(int(INACTIVITY_TIMEOUT))    

        # initialize httpserver 
        httpd = BaseHTTPServer.HTTPServer(("", HTTP_PORT), hydraulics_webserver.HydraulicsHandler)
        httpd.serve_forever()
    except KeyboardInterrupt:
        print "Keyboard interrupt detected, terminating"
    except Exception as e:
        logging.exception("Unexpected exception:")
    
    if httpd != None:
        httpd.server_close()

    hydraulics_drv.shutdown()
    hydraulics_stream.shutdown()
    attract_manager.shutdown()
    event_manager.shutdown()
