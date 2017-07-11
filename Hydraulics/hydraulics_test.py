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


logging.basicConfig(format='%(asctime)-15s')

if __name__ == '__main__':

    log.info("Noetica Hydraulics")
    if len(sys.argv > 1):
        configFile = sys.argv[1]
    else:
        configFile = "./hydraulics.cfg"
    
    try:
        configParser = ConfigParser.ConfigParser()   
        configParser.read(configFile)
        HTTP_PORT     = configParser.get("main", "httpPort", HTTP_PORT)
        POSITION_PORT = configParser.get("main", "streamPort", POSITION_PORT)
        HYDRAULICS_POLL_INTERVAL = configParser.get("main", "pollInterval", HYDRAULICS_POLL_INTERVAL)
    except:
        logging.error("Problem reading config file {}, defaulting configuration".format(configFile)

    try:
        # setup driver  - XXX own process?
        hydraulics_drv.init(HYDRAULICS_POLL_INTERVAL)

        # setup playback - NB - this is a set of utility functions, not own thread
        hydraulics_playback.init()
        
        # setup position streamer - XXX should be in own process
        hydraulics_stream.init(POSITION_PORT)

        # initialize httpserver 
        httpd = BaseHTTPServer.HTTPServer(("", HTTP_PORT), hydraulics_frontend.HydraulicsHandler)
        httpd.serve_forever()
    except KeyboardInterrupt:
        print "Keyboard interrupt detected, terminating"
    except Exception as e:
        logging.exception("Unexpected exception:")
    
    try: 
        httpd.server_close()
    except NameError:
        print("Could not find httpd") # XXX wtf is this for?
        
    hydraulics_drv.shutdown()
    hydraulics_stream.shutdown()
