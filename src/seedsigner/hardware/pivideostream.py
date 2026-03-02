# import the necessary packages
import logging
from threading import Thread
import time

from picamera2 import Picamera2

logger = logging.getLogger(__name__)


# Modified from: https://github.com/jrosebr1/imutils
class PiVideoStream:
    def __init__(self, resolution=(320, 240), framerate=32, format="bgr", **kwargs):
        self.resolution = resolution
        self.framerate = framerate
        
        self.camera = Picamera2()
        self.frame = None
        self.should_stop = False
        self.is_stopped = True

        config = self.camera.create_preview_configuration(
            main={"size": resolution, "format": "RGB888"},
            buffer_count=4
        )
        self.camera.configure(config)


    def start(self):
        # start the thread to read frames from the video stream
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()

        self.camera.start()
        self.is_stopped = False
        return self

    def update(self):
        while not self.should_stop:
            self.frame = self.camera.capture_array("main")
            time.sleep(1 / self.framerate)

        logger.info("PiVideoStream: closing everything")
        self.camera.stop()
        self.camera.close()
        self.should_stop = False
        self.is_stopped = True


    def read(self):
        # return the frame most recently read
        return self.frame

    def stop(self):
        # indicate that the thread should be stopped
        self.should_stop = True

        # Block in this thread until stopped
        while not self.is_stopped:
            pass
