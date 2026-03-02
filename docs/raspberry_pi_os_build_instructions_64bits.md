# Raspberry Pi OS Local Dev Build Instructions


## Development Notes
For this setup to work, I have modified:
- ST7789.py
- camera.py
- pivideostream.py

Current limitations:
- Camera colors are inverted.
- Motion is not as smooth as expected.
- These issues may be related to RGB/BGR ordering in the ST7789.py and pivideostream.py modifications.

This build runs inside a Python virtual environment (`venv`), not the system Python.

Debian 13 enforces PEP 668 (externally managed Python environments), which prevents installing packages globally using `pip`. For this reason, a virtual environment is required.

The virtual environment is created using `--system-site-packages` because some dependencies such as `python3-picamera2` and `libcamera-apps` are installed system-wide via `apt`, not via `pip`. Allowing access to system site packages avoids duplicating or breaking those installations.

Additionally, the Python version shipped with Debian 13 requires updating certain pip packages inside the virtual environment, so some dependencies are installed at their latest compatible versions.


### Flash Raspberry Pi OS Lite
* Use Raspberry Pi Imager.
* Set the **hostname** and **username** to `pi`.
* Choose any password.
* Configure Wi-Fi and enable **SSH** during setup.

### 3. Connect to the Raspberry Pi
Boot the Raspberry Pi and connect via SSH:

```bash
ssh pi@pi.local
```

### System Update
Run:
```bash
sudo apt-get update && sudo apt-get dist-upgrade -y
```

### Configure the Pi
Launch the Raspberry Pi's System Configuration tool using the command:
```bash
sudo raspi-config
```

Set the following:
* `Interface Options`:
    * `SPI`: enable
* `Localisation Options`:
    * `Locale`: arrow up and down through the list and select or deselect languages with the spacebar.
        * Deselect the default language option that is selected
        * Select `en_US.UTF-8 UTF-8` for US English
        * Use the `TAB` button to select `Ok` and press `ENTER`
        * On the next screen select `en_US.UTF-8` for the default locale

Each command should be run individually, unless it's specified as a multi-line command.
### Change the default password
Change the system's default password from the default "raspberry". Run the command:
```bash
passwd
```

You will be prompted to enter the current password ("raspberry") and then to enter a new password twice. In our prepared release image, the password used is `AirG@pped!`.

### Install dependencies
```bash
sudo apt update && sudo apt install -y libzbar0 libbcm2835-dev python3-pip \
   libcap-dev libjpeg-dev libtiff5-dev \
   git python3-picamera2 libcamera-apps qrencode
```

### Download the SeedSigner code:
```bash
git clone -b dev https://github.com/bon3k/seedsigner.git
cd seedsigner
```

### Set Up Python Environment (custom fork):
```bash
python3 -m venv --system-site-packages /home/pi/venv
source /home/pi/venv/bin/activate
cd /home/pi/seedsigner/
pip install -r requirements-64bit.txt
pip install -r requirements-raspi-64bit.txt
```

### Optional: increase spidev buffer size
This allows `ST7789.py` to update the LCD without performing multiple write operations because the default buffer size is 4096 bytes. The default can be changed via the `/boot/firmware/cmdline.txt` file. You will need to add `spidev.bufsiz=131072` to the end of this single lined file command.

Example `cmdline.txt` contents:
```
console=serial0,115200 console=tty1 root=PARTUUID=2fa4ba7e-02 rootfstype=ext4 elevator=deadline fsck.repair=yes rootwait modules-load=dwc2,g_ether spidev.bufsiz=131072
```

### Configure `systemd` to run SeedSigner at boot:

```bash
sudo nano /etc/systemd/system/seedsigner.service
```

Add the following contents to the text file that was created:
If you are not using the username pi, then replace `pi` in the service section below with your username. There are 3 lines to change.
```ini
[Unit]
Description=Seedsigner

[Service]
User=pi
WorkingDirectory=/home/pi/seedsigner/src/
ExecStart=/home/pi/seedsigner/src/run_seedsigner.sh
StandardOutput=null
ErrorOutput=null
Restart=no

[Install]
WantedBy=multi-user.target
```

Use `CTRL-X` and `y` to exit and save changes.

Configure the service to start running (this will restart the seedsigner code automatically at startup):
```bash
sudo systemctl enable seedsigner.service
```

Now reboot the Raspberry Pi:
```bash
sudo reboot
```

After the Raspberry Pi reboots, you should see the SeedSigner splash screen and the SeedSigner menu subsequently appear on the LCD screen (note that it can take up to 60 seconds for the menu to appear).
