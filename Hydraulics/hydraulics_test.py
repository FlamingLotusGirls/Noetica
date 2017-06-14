#!/usr/bin/python

from time import sleep
import BaseHTTPServer
import hydraulics_drv
import hydraulics_playback
import hydraulics_frontend

PORT = 9000

if __name__ == '__main__':

    print "Hydraulics Test program"
    print "Press CTRL C to exit" 

    try:
        # setup driver
        hydraulics_drv.init()

        # setup playback
        hydraulics_playback.init()

        # initialize httpserver
        httpd = BaseHTTPServer.HTTPServer(("", PORT), hydraulics_frontend.HydraulicsHandler)
        httpd.serve_forever()
    except KeyboardInterrupt:
        print "Keyboard interrupt detected, terminating"
    except Exception as e:
        print "Unexpected exception:", e
    
    try: 
        httpd.server_close()
    except NameError:
        print("Could not find httpd")
    hydraulics_drv.shutdown()
