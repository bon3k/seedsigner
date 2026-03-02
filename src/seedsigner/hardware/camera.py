import io

from gettext import gettext as _
from PIL import Image

from seedsigner.models.settings import Settings, SettingsConstants
from seedsigner.models.singleton import Singleton
from seedsigner.hardware.pivideostream import PiVideoStream

from picamera2 import Picamera2

class CameraConnectionError(Exception):
    pass



class Camera(Singleton):
    _video_stream = None
    _picamera = None
    _camera_rotation = None

    @classmethod
    def get_instance(cls):
        # This is the only way to access the one and only Controller
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
        cls._instance._camera_rotation = int(Settings.get_instance().get_value(SettingsConstants.SETTING__CAMERA_ROTATION))
        return cls._instance


    def start_video_stream_mode(self, resolution=(512, 384), framerate=12, format="bgr"):
#        from picamera import PiCameraError
#        from seedsigner.hardware.pivideostream import PiVideoStream
        if self._video_stream is not None:
            self.stop_video_stream_mode()

        try:
            self._video_stream = PiVideoStream(resolution=resolution,framerate=framerate, format=format)
            self._video_stream.start()
        except Exception:
            raise CameraConnectionError()


    def read_video_stream(self, as_image=False):
        if not self._video_stream:
            raise Exception("Must call start_video_stream first.")
        frame = self._video_stream.read()
        if not as_image:
            return frame
        
        if frame is not None:
            img = Image.fromarray(frame)
            if img.mode != "RGB":
                img = img.convert("RGB")
            return img.rotate(90 + self._camera_rotation)
        return None    


    def stop_video_stream_mode(self):
        if self._video_stream is not None:
            self._video_stream.stop()
            self._video_stream = None


    def start_single_frame_mode(self, resolution=(720, 480)):
#        from picamera import PiCamera, PiCameraError
        if self._video_stream is not None:
            self.stop_video_stream_mode()
        if self._picamera is not None:
            self._picamera.close()

        try:
            self._picamera2 = Picamera2()
            config = self._picamera2.create_still_configuration(main={"size": resolution, "format": "RGB888"})
            self._picamera2.configure(config)
            self._picamera2.start()
        except Exception:
            raise CameraConnectionError()



    def capture_frame(self):
        if self._picamera2 is None:
            raise Exception("Must call start_single_frame_mode first.")

        frame = self._picamera2.capture_array("main")
        img = Image.fromarray(frame)

        if img.mode != "RGB":
            img = img.convert("RGB")

        return img.rotate(90 + self._camera_rotation)




    def stop_single_frame_mode(self):
        if self._picamera2 is not None:
            self._picamera2.stop()
            self._picamera2.close()
            self._picamera2 = None

