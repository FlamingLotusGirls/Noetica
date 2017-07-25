#!/usr/bin/python

import BaseHTTPServer
import ConfigParser
import logging
import sys


import hydraulics_drv
import hydraulics_playback
import hydraulics_frontend
import hydraulics_stream

# default parameters - configuration file overrides
HTTP_PORT = 9000 
POSITION_PORT = 9001
HYDRAULICS_POLL_INTERVAL = 200  # hardware poll interval, in ms
PLAYBACK_DIR = "/home/flaming/Noetica/Hydraulics/playbacks/"


logging.basicConfig(format='%(asctime)-15s %(levelname)s %(message)s', level=logging.DEBUG)
#logging.basicConfig(format='%(asctime)-15s', level=logging.DEBUG)
#logging.basicConfig(format=level=logging.DEBUG)
if __name__ == '__main__':

    logging.info("Noetica Hydraulics")
    print "STARTING NOETICA"
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
    except Exception:
        logging.exception("Problem reading config file {}, defaulting configuration".format(configFile))

    try:
        # setup position streamer - XXX should be in own process
        hydraulics_stream.init(POSITION_PORT)

        # setup driver  - XXX own process?
        hydraulics_drv.init(HYDRAULICS_POLL_INTERVAL)

        # setup playback - NB - this is a set of utility functions, not own thread
        hydraulics_playback.init()        

        # initialize httpserver 
        httpd = BaseHTTPServer.HTTPServer(("", HTTP_PORT), hydraulics_frontend.HydraulicsHandler)
        httpd.serve_forever()
    except KeyboardInterrupt:
        print "Keyboard interrupt detected, terminating"
    except Exception as e:
        logging.exception("Unexpected exception:")
    
    if httpd != None:
        httpd.server_close()

    hydraulics_drv.shutdown()
    hydraulics_stream.shutdown()
