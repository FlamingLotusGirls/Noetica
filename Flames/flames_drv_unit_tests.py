import Queue
import flames_drv
import unittest
import json


class TestFlamesDrvMethods(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFlamesDrvMethods, self).__init__(*args, **kwargs)
        self.cmdQueue = Queue.Queue()
        self.pooferFiringThread = flames_drv.PooferFiringThread(self.cmdQueue, 'test_poofer_mappings.json')
        self.correctDisablePooferMapping = "!0100~10~40.!0200~10~60.!0300~30~40~50.!0400~50."

    def test_init(self):
        self.assertEqual(self.pooferFiringThread.pooferEvents, list())
        self.assertFalse(self.pooferFiringThread.isFiringDisabled)
        self.assertEqual(self.pooferFiringThread.disabled_poofers, set())
        self.assertEqual(self.pooferFiringThread.disableAllPoofersCommand, self.pooferFiringThread.generateDisableAllString())
        # self.assertEqual(pooferFiringThread.ser.baudrate, 19200)  NEED TO LOOK AT PORTS AND ALL OF THAT
        # self.assertEqual(pooferFiringThread.ser.port, 19200)


    def test_check_sequence(self):
        try:
            addresses = ["010","011","014","020","021","026","030","033","034","035","040","045"]
            test = self.pooferFiringThread.makeBangCommandList(addresses)
            print test

        except Exception:
            print "failed :("
            self.assertTrue(False)

        self.assertFalse(test == 1)

    def test_setUpEvent(self):
        with open('sequences.json') as data_file:
            events = json.load(data_file)
        eventOne = next((x for x in events if x["name"] == "North South And Top"), None)

        pooferEventBefore = self.pooferFiringThread.pooferEvents
        self.pooferFiringThread.setUpEvent(eventOne)

        pooferEventAfter= self.pooferFiringThread.pooferEvents


if __name__ == '__main__':
    unittest.main()
