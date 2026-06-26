import spidev
import time
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import zlib


class InterfazLCD:
    def __init__(self, rst_pin=27, dc_pin=25, bl_pin=24, cs_pin=8):
        self.width = 240
        self.height = 240
        self.RST_PIN = rst_pin
        self.DC_PIN = dc_pin
        self.BL_PIN = bl_pin
        self.CS_PIN = cs_pin
        self.spi = spidev.SpiDev()
        self.last_image_hash = None
        self.screen_locked = False


        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        for pin in (self.RST_PIN, self.DC_PIN, self.BL_PIN, self.CS_PIN):
            GPIO.setup(pin, GPIO.OUT)

        GPIO.setup(self.BL_PIN, GPIO.OUT)

        # Iniciar PWM en BL_PIN con una frecuencia de 1000 Hz
        self.bl_pwm = GPIO.PWM(self.BL_PIN, 1000)
        self.bl_pwm.start(100)  # Brillo al 100%
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 32000000
        self.spi.mode = 0b00
        self.inicializar_lcd()


#    def __del__(self):
#        self.spi.close()
#        GPIO.cleanup()


    def write_command(self, cmd):
        GPIO.output(self.DC_PIN, GPIO.LOW)
        self.spi.xfer([cmd])


    def write_data(self, data):
        GPIO.output(self.DC_PIN, GPIO.HIGH)
        self.spi.xfer(data)


    def set_window(self, x_start=0, y_start=0, x_end=239, y_end=239):
        self.write_command(0x2A)
        self.write_data([0x00, x_start, 0x00, x_end])
        self.write_command(0x2B)
        self.write_data([0x00, y_start, 0x00, y_end])
        self.write_command(0x2C)


    def inicializar_lcd(self):
        GPIO.output(self.RST_PIN, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(self.RST_PIN, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(self.RST_PIN, GPIO.HIGH)

        comandos = [
            (0x36, [0x00]), (0x3A, [0x05]), (0xB2, [0x0C, 0x0C, 0x00, 0x33, 0x33]),
            (0xB7, [0x35]), (0xBB, [0x1F]), (0xC0, [0x2C]), (0xC2, [0x01]),
            (0xC3, [0x12]), (0xC4, [0x20]), (0xC6, [0x0F]), (0xD0, [0xA4, 0xA1]),
            (0xE0, [0xD0, 0x08, 0x11, 0x08, 0x0C, 0x15, 0x39, 0x33, 0x50, 0x36, 0x13, 0x14, 0x29, 0x2D]),
            (0xE1, [0xD0, 0x08, 0x10, 0x08, 0x06, 0x06, 0x39, 0x44, 0x51, 0x0B, 0x16, 0x14, 0x2F, 0x31])
        ]

        for cmd, data in comandos:
            self.write_command(cmd)
            self.write_data(data)

        self.write_command(0x21)
        self.write_command(0x11)
        self.write_command(0x29)


    def display_image(self, image):
        if self.screen_locked:
            return

        if isinstance(image, str):
            img = Image.open(image)
        else:
            img = image

        img = img.rotate(270, expand=False)  #        /// ROTAR PANTALLA ///
        img = img.resize((240, 240)).convert("RGB")
#        self.current_image = img.copy()
        img_data = np.array(img, dtype=np.uint16)
        # check image hash
        current_hash = zlib.crc32(img.tobytes())
        if current_hash == self.last_image_hash:
            return
        self.last_image_hash = current_hash

        r = (img_data[:, :, 0] >> 3) << 11
        g = (img_data[:, :, 1] >> 2) << 5
        b = (img_data[:, :, 2] >> 3)
        img_rgb565 = (r | g | b).astype(np.uint16).byteswap().tobytes()

        self.set_window()
        for i in range(0, len(img_rgb565), 4096):
            self.write_data(img_rgb565[i:i + 4096])


    def show_black_screen(self):
        img = Image.new("RGB", (self.width, self.height), (0, 0, 0))
        self.display_image(img)


    def display_menu(self, opciones, seleccion_index, titulo=None):

        imagen = Image.new("RGB", (240, 240), "black")
        draw = ImageDraw.Draw(imagen)

        try:
            fuente = ImageFont.truetype("DejaVuSans.ttf", 16)
        except:
            fuente = ImageFont.load_default()

        y = 0

        if titulo:
            draw.text((5, y), titulo, font=fuente, fill="white")
            y += 24

        for i, opcion in enumerate(opciones):

            if i == seleccion_index:

                draw.rectangle(
                    [(0, y), (240, y + 20)],
                    fill="lightgray"
                )

                color = "black"

            else:

                color = "white"

            draw.text(
                (5, y),
                opcion,
                font=fuente,
                fill=color
            )

            y += 20

        self.display_image(imagen)


    def limpiar_lcd(self):
        self.set_window()
        data = b'\x00\x00' * (240 * 240)
        for i in range(0, len(data), 4096):
            self.write_data(data[i:i + 4096])
