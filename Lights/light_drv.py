from threading import Thread
import logging

logger = logging.getLogger("light_drv")

DMX_RED_CHANNEL = 2
DMX_GREEN_CHANNEL = 3
DMX_BLUE_CHANNEL = 4
DMX_WHITE_CHANNEL = 5
DMX_CHANNEL_COUNT = 6 # Did we decide on another number

def init(lightQueue):
    global lightThread
    lightThread = LightThread(lightQueue)
    lightThread.start()

def shutdown():
    global lightThread
    logger.info("Light driver shutdown()")
    if lightThread != None:
        logger.info("...Joining flame driver thread")
        lightThread.shutdown()
        lightThread.join()
        lightThread = None

class LightThread(Thread):

    def __init__(self, lightQueue):
        Thread.__init__(self)
        self.lightQueue = lightQueue
        self.running = False
        self.isConstantLightModeOn = False # Might not even need this if we only want to keep light constant when Noetica isn't moving.
        self.initSerial()
        self.lightEvents = list()

    def start(self):
        self.running = True

    def shutdown(self):
        self.running = False
        # either turn lights off, or turn to default

    def initSerial(self):
        # TODO: Actually get this to work with entec code
        self.ser = serial.Serial()
        self.ser.baudrate = BAUDRATE
        port = False
        for filename in os.listdir("/dev"):
            if filename.startswith("tty.usbserial"):  # this is the ftdi usb cable on the Mac
                port = "/dev/" + filename
                logger.info("Found usb serial at " + port)
                break;
            elif filename.startswith("ttyUSB0"):      # this is the ftdi usb cable on the Pi (Linux Debian)
                port = "/dev/" + filename
                logger.info("Found usb serial at " + port)
                break;

        if not port:
            logger.exception("No usb serial connected")
            return None

        self.ser.port = port
        self.ser.timeout = 0
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.bytesize = 8
        self.ser.parity   = serial.PARITY_NONE
        self.ser.rtscts   = 0
        self.ser.open()


    def run(self):
        self.running = True
        while(self.running):
            if not self.isConstantLightModeOn:
                if len(self.lightEvents) > 0: # there are poofer events
                    # pop events off of the list. If the current time is greater than
                    # the time associated with the event, set up for serial

                    event = self.lightEvents.pop(0)
                    currentTime = time.time()
                    firingTime = event["time"]
                    if firingTime < currentTime:
                        if not currentTime - firingTime > 2000: #If it's more than two seconds in the past, ignore it
                            self.firePoofers(event["bangCommandList"])
                    else:
                        self.lightEvents.insert(0, event)

                if len(self.lightEvents) > 0: # there are poofer events in the future
                    waitTime = self.lightEvents[0]["time"] - time.time()

                else:
                    waitTime = PooferFiringThread.TIMEOUT

            try:
                cmd = self.lightQueue.get(True, waitTime)
                logger.debug("Received Message on cmd queue!")
                # parse message. If this is a request to do a flame sequence,
                # set up poofer events, ordered by time. Event["time"] attribute
                # should be current time (time.time()) plus the relative time from
                # the start of the sequence
                msgObj = json.loads(cmd)
                type = msgObj["cmdType"]
                logger.debug("message is {}".format(msgObj))
                if type == "stop":
                    self.stopAll()

                elif type == "resume":
                    self.resumeAll()

                elif type == "setToConstant":
                    self.isConstantLightModeOn = True
                    self.setConstantLight(msgObj)

                elif type == "stopConstant":
                    self.isConstantLightModeOn = False

                elif type == "setColorPattern":
                    self.setColorPattern(msgObj)


            except Queue.Empty:
                # this is just a timeout - completely expected. Run the loop
                pass
            except Exception:
                logger.exception("Unexpected exception processing command queue!")

        def setConstantLight(self, msgObj):
            # TODO: set constant light
            pass

        def setColorPattern(self, msgObj):
            # gets passed a color pattern {red:<int>, green:<int>, blue:<int> }
            # and does something with it.
