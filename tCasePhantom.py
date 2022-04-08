
import array
from rainbowio import colorwheel
import board
import neopixel
from analogio import AnalogIn
import touchio
import digitalio
import time

led_pin = board.NEOPIXEL  # NeoPixel LED strand is connected to GPIO #0 / D0
n_pixels = 12  # Number of pixels you are using
dc_offset = 0  # DC offset in mic signal - if unusure, leave 0
noise = 100  # Noise/hum/interference in mic signal
samples = 60  # Length of buffer for dynamic level adjustment
top = n_pixels + 1  # Allow dot to go slightly off scale

# Collection of prior volume samples
vol = array.array('H', [0] * samples)
mic_pin = AnalogIn(board.A5)

redUp = touchio.TouchIn(board.A1)
greenUp = touchio.TouchIn(board.A2)
blueUp = touchio.TouchIn(board.A3)
redDown = touchio.TouchIn(board.A4)
greenDown = touchio.TouchIn(board.A6)
blueDown = touchio.TouchIn(board.TX)
strip = neopixel.NeoPixel(led_pin, n_pixels, brightness=.1, auto_write=True)

from adafruit_bluefruit_connect.packet import Packet
from adafruit_bluefruit_connect.color_packet import ColorPacket

from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

try:
    from audiocore import WaveFile
except ImportError:
    from audioio import WaveFile

from audiopwmio import PWMAudioOut as AudioOut

ble = BLERadio()
uart_service = UARTService()
advertisement = ProvideServicesAdvertisement(uart_service)

spkrenable = digitalio.DigitalInOut(board.SPEAKER_ENABLE)
spkrenable.direction = digitalio.Direction.OUTPUT
spkrenable.value = True

pcolor=(200,0,0)
r=200
g=0
b=0
start=40000
wait=0
ble.start_advertising(advertisement)

def play_file(filename):
    print("Playing file: " + filename)
    wave_file = open(filename, "rb")
    with WaveFile(wave_file) as wave:
        with AudioOut(board.SPEAKER) as audio:
            audio.play(wave)
            #while audio.playing:
            #    pass


while True:
    if not ble.connected:
        if redUp.value:
            r=r+2
            if r>255:
                r=255
        if blueUp.value:
            b=b+2
            if b>255:
                b=255
        if greenUp.value:
            g=g+2
            if g>255:
                g=255
        if redDown.value:
            r=r-2
            if r<0:
                r=0
        if greenDown.value:
            g=g-2
            if g<0:
                g=0
        if blueDown.value:
            b=b-2
            if b<0:
                b=0
        pcolor=(r,g,b)
        strip.fill(pcolor)
    else:
        if uart_service.in_waiting:
            packet = Packet.from_stream(uart_service)
            if isinstance(packet, ColorPacket):
                pcolor=packet.color
        strip.fill(pcolor)

    n = int((mic_pin.value / 65536) * 1000)  # 10-bit ADC format
    n = abs(n - 512 - dc_offset)  # Center on zero

    if n >= noise:  # Remove noise/hum
        n = n - noise

    # Color pixels based on color given by user
    if n>30:
        start=time.monotonic()
        if start-wait>20:
            play_file("Phantom.wav")
            wait = time.monotonic()

    uart_service.write("{}\n".format(start-wait))
