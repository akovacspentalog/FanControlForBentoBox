from machine import Pin, I2C, SoftI2C, ADC
from picozero import pico_led
from ssd1306 import SSD1306_I2C
import ssd1306
import time
import framebuf
import freesans20
import writer
import ahtx0
from web_server import WebServer
import bluetooth
from ble_simple_peripheral import BLESimplePeripheral
import asyncio
from os import uname
from display_service import DisplayService

display = DisplayService()
# Check if we have extended network and Bluetooth LE capabilities with Pi Pico W if not we continue with basic capabilities.
if uname()[4] == 'Raspberry Pi Pico W with RP2040':
    print('RPi Pico W')   # True    
    display.displaySplash('Creality')
else:
    print('RPi Pico')     # False
    display.displaySplash('Creality')

ble = bluetooth.BLE()

# Create an instance of the BLESimplePeripheral class with the BLE object
sp = BLESimplePeripheral(ble)

# Set the debounce time to 0. Used for switch debouncing
debounce_time=0

# Create a Pin object for the onboard LED, configure it as an output

# Initialize the LED state to 0 (off)
#     led_state = 0

#GPIO Pin Number Definitions; use whatever pin numbers you want
button_pin = 7 #Pin for button
led_pin = 25 #On-board LED = GPIO25; change if using external LED
voc_sense_pin = 26 #ADC GPIO pin number for VOC sensor
voc_threshold = 1.1 #Threshold to activate system
fan_pin = 22 #GPIO pin of fan relay signal

#set up button (optional)
#button = Pin(button_pin,Pin.IN, Pin.PULL_DOWN)

#Temp and Humidity setup
i2c_temp = I2C(1, sda=Pin(14), scl=Pin(15), freq=400000)

temp_sensor = ahtx0.AHT20(i2c_temp)
#LED Setup
led = Pin(led_pin, Pin.OUT)

#set up OLED

i2c_oled = I2C(0,sda=Pin(0), scl=Pin(1), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c_oled)

#set up VOC sensor
voc_def = ADC(voc_sense_pin)
voc_conv = 5/65535

#set up fan trigger pin
fan_relay = Pin(fan_pin, mode=Pin.OUT)

count = 0
voc_level_avg = 0
voc_level_sum = 0
show_temp = True
seconds = 0
bigText = writer.Writer(oled, freesans20)

#bootup splash screen Bento Box
#splash = bytearray(b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xfe\x7f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xf8\x1f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xf0\x0f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xc0\x03\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xfc\x00\x00?\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xf0\x01\x80\x0f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xe0\x03\xc0\x07\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x80\x0f\xf0\x01\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xfe\x00?\xfc\x00\x7f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xf8\x00\xff\xff\x00\x1f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xf0\x03\xff\xff\xc0\x0f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xc0\x07\xff\xff\xe0\x03\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x80?\xff\xff\xfc\x01\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x7f\xff\xff\xfe\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x7f\xff\xff\xfe\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00?\xff\xff\xfc\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x0f\xff\xff\xf0\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x01\xff\xff\x80\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\xff\xff\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x02\x00?\xfc\x00@\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x03\x80\x1f\xf8\x01\xc0\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x03\xe0\x03\xc0\x07\xc0\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x03\xf8\x00\x00\x1f\xc0\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x03\xfc\x00\x00?\xc0\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x03\xff\x00\x00\xff\xc0\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x03\xff\xc0\x03\xff\xc0\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x03\xff\xf0\x0f\xff\xc0\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x03\xff\xf8\x1f\xff\xc0\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x03\xff\xf8\x1f\xff\xc0\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x03\xff\xf8\x1f\xff\xc0\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x03\xff\xf8\x1f\xff\xc0\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x03\xff\xf8\x1f\xff\xc0\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x03\xff\xf8\x1f\xff\xc0\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x03\xff\xf8\x1f\xff\xc0\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x03\xff\xf8\x1f\xff\xc0\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x03\xff\xf8\x1f\xff\xc0\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x03\xff\xf8\x1f\xff\xc0\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x01\xff\xf8\x1f\xff\x80\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x7f\xf8\x1f\xfe\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x80?\xf8\x1f\xfc\x01\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xc0\x07\xf8\x1f\xe0\x03\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xf0\x03\xf8\x1f\xc0\x0f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xf8\x00\xf8\x1f\x00\x1f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xfe\x008\x1c\x00\x7f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x80\x08\x10\x01\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xe0\x00\x00\x07\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xf0\x00\x00\x0f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xfc\x00\x00?\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xc0\x03\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xf0\x0f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xf8\x1f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xfe\x7f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff')
#bootup splash screen Creality
splash = bytearray(b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xf1\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xe1\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xe4\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xca\x7f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xc0\x7f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x91\x3f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x85\x3f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x2e\x1f\xff\xc0\x20\x0f\xc0\x7f\xfe\x7f\x20\x03\xf9\xff\xff\xff\x0e\x9f\xff\x80\x20\x07\x00\x7e\x7e\x7f\x20\x01\xf3\xff\xff\xfe\x1f\x0f\xff\x1f\xe7\xe2\x3f\xfe\x7e\x7f\x3e\x78\xe7\xff\xff\xfe\x5f\x0f\xff\x3f\xe7\xf2\x7f\xfc\x3e\x7f\x3e\x7c\x47\xff\xff\xfc\x3f\x87\xfe\x7f\xe4\x06\x00\x78\x1e\x7f\x3e\x7e\x0f\xff\xff\xf8\xff\xa3\xfe\x7f\xe6\x06\x00\x79\x9e\x7f\x3e\x7f\x1f\xff\xff\xf8\x7f\xc3\xfe\x7f\xe7\x3e\x7f\xf1\x8e\x7f\x3e\x7f\x3f\xff\xff\xf0\xe4\xe1\xff\x3f\xe7\x9e\x3f\xf3\xce\x7f\x3e\x7f\x3f\xff\xff\xf1\x51\x51\xff\x80\x27\xcf\x00\x66\x06\x01\x3e\x7f\x3f\xff\xff\xe0\x60\xc0\xff\xc0\x27\xe7\x80\x46\x06\x01\x3e\x7f\x3f\xff\xff\xc0\x80\x20\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xc0\x1f\x10\x7f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x84\x7f\xc4\x3f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x93\xff\xf9\x3f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x8f\xff\xfe\x3f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff')
#bootup splash screen Bambulab
#splash = bytearray(b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xf0\x20\xfb\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xf0\x20\xfc\x7f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xf0\x20\xff\x9f\xff\xfc\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xf0\x20\xf3\x98\x10\x04\x0d\xef\xff\xff\xff\xff\xff\xff\xff\xff\xf0\x20\xf0\x1f\xd3\x75\xed\xcf\xff\xff\xff\xff\xff\xff\xff\xff\xf0\x30\xf3\xd8\x13\x75\xed\xcf\xff\xff\xff\xff\xff\xff\xff\xff\xf0\x2e\xf3\xd3\xd3\x74\xed\xcf\xff\xff\xff\xff\xff\xff\xff\xff\xf0\x63\xf0\x38\x1b\x74\x0c\x1f\xff\xff\xff\xff\xff\xff\xff\xff\xf1\xe0\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x60\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xfc\x20\xf3\xff\xcf\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xf0\x20\xf3\xe0\xc0\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xf0\x20\xf3\xff\x4e\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xf0\x20\xf3\xe0\x4e\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xf0\x20\xf3\xdf\x4e\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xf0\x60\xf0\x60\x40\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff')
#bootup splash screen Voron Design
#splash = bytearray(b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xef\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x83\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xfe\x01\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xfc\x00\x7f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xf0\x00\x1f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xc0\x00\x0f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\x03\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xfe\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xf8\x03\xe1\xf0\x3f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xe0\x03\xe1\xf0\x1c\x7f\xf3\xe0\x0f\xe0\x07\xfc\x01\xfc\x7f\xcf\xe0\x07\xc3\xe0\x1e\x7f\xe3\x83\x83\xe0\x03\xf0\x70\xfc\x3f\xcf\xe0\x0f\xc7\xe0\x1e\x3f\xe7\x8f\xe3\xe7\xf1\xf3\xfc\x7c\x3f\xcf\xe0\x0f\x87\xc0\x1e\x3f\xe7\x1f\xf1\xe7\xf1\xe3\xfe\x7c\x1f\xcf\xe0\x1f\x0f\x80\x1f\x3f\xc7\x1f\xf1\xe7\xf1\xe3\xfe\x3c\x8f\xcf\xe0\x3f\x1f\x80\x1f\x1f\xcf\x1f\xf1\xe7\xf1\xe3\xfe\x3c\xcf\xcf\xe0\x3e\x1f\x00\x1f\x1f\x8f\x1f\xf1\xe7\xf1\xe3\xfe\x3c\xc7\xcf\xe0\x7c\x3e\x00\x1f\x9f\x9f\x1f\xf1\xe7\xf3\xe3\xfe\x3c\xe3\xcf\xe0\xfc\x7e\x00\x1f\x8f\x9f\x1f\xf1\xe0\x03\xe3\xfe\x3c\xf3\xcf\xe0\xf8\x7c\x3e\x1f\xcf\x1f\x1f\xf1\xe0\x1f\xe3\xfe\x3c\xf1\xcf\xe0\x00\xf8\x7c\x1f\xc7\x3f\x1f\xf1\xe7\x1f\xe3\xfe\x3c\xf8\xcf\xe0\x01\xf8\xfc\x1f\xc7\x3f\x1f\xf1\xe7\x8f\xe3\xfe\x3c\xf8\xcf\xe0\x01\xf0\xf8\x1f\xe6\x7f\x1f\xf1\xe7\xcf\xe3\xfe\x3c\xfc\x4f\xe0\x03\xe1\xf0\x1f\xe2\x7f\x1f\xf1\xe7\xc7\xe3\xfe\x3c\xfe\x0f\xe0\x07\xe3\xf0\x1f\xf0\x7f\x9f\xf3\xe7\xe3\xf3\xfc\x7c\xfe\x0f\xe0\x07\xc3\xe0\x1f\xf0\xff\x87\xc3\xe7\xf1\xf0\xf8\x7c\xff\x0f\xe0\x0f\x87\xc0\x1f\xf0\xff\xc0\x0f\xe7\xf1\xf8\x01\xfc\xff\x8f\xe0\x1f\x8f\xc0\x1f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xe0\x1f\x0f\x80\x1f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xf8\x3e\x1f\x00\x3f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xfe\x00\x00\x00\xfe\x1f\xfe\x0f\xff\x0f\xff\xbf\xfe\x0f\xfd\xef\xff\x00\x00\x03\xfe\xef\xfe\xff\xfe\xff\xff\x9f\xfd\xff\xfc\xef\xff\xc0\x00\x0f\xfe\xf7\xfe\xff\xfe\xff\xff\x9f\xfd\xff\xfd\x6f\xff\xf0\x00\x1f\xfe\xf7\xfe\x1f\xfe\x1f\xff\x9f\xfd\xcf\xfd\x6f\xff\xfc\x00\x7f\xfe\xf7\xfe\xff\xff\xef\xff\x9f\xfd\xef\xfd\xaf\xff\xfe\x01\xff\xfe\xf7\xfe\xff\xff\xef\xff\x9f\xfd\xef\xfd\xcf\xff\xff\x83\xff\xfe\xe7\xfe\xff\xff\xef\xff\x9f\xfd\xef\xfd\xcf\xff\xff\xef\xff\xfe\x1f\xfe\x0f\xfe\x1f\xff\xbf\xfe\x0f\xfd\xef\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff')
#bootup splash screen Prusa
#splash = bytearray(b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x80\x0f\xf0\x01\xfe\x1f\xf0\xfe\x03\xff\xe1\xff\xff\xff\xff\xff\x80\x03\xe0\x00\x3e\x0f\xf0\xf8\x00\xff\xc0\xff\xff\xff\xff\xff\x80\x01\xe0\x00\x1e\x0f\xf0\xf0\x00\x7f\xc0\xff\xff\xff\xff\xff\x80\x00\xe0\x00\x1e\x0f\xf0\xf0\x70\x3f\xc0\xff\xff\xff\xff\xff\x83\xf0\x60\xfe\x0e\x0f\xf0\xe0\xf8\x3f\x80\x7f\xff\xff\xff\xff\x83\xf0\x60\xfe\x0e\x0f\xf0\xe1\xfc\x3f\x80\x7f\xff\xff\xff\xff\x83\xf8\x60\xfe\x0e\x0f\xf0\xe0\xff\xff\x80\x7f\xff\xff\xff\xff\x83\xf8\x60\xfe\x0e\x0f\xf0\xe0\x7f\xff\x0c\x3f\xff\xff\xff\xff\x83\xf0\x60\xfe\x1e\x0f\xf0\xf0\x07\xff\x0c\x3f\xff\xff\xff\xff\x83\xe0\xe0\x00\x1e\x0f\xf0\xf8\x00\xfe\x1c\x1f\xff\xff\xff\xff\x80\x00\xe0\x00\x7e\x0f\xf0\xfc\x00\x7e\x1e\x1f\xff\xff\xff\xff\x80\x01\xe0\x00\x3e\x0f\xf0\xff\x80\x3e\x1e\x1f\xff\xff\xff\xff\x80\x07\xe0\xf8\x1e\x0f\xf0\xff\xf8\x1c\x00\x0f\xff\xff\xff\xff\x83\xff\xe0\xfe\x1e\x0f\xf0\xff\xfc\x1c\x00\x0f\xff\xff\xff\xff\x83\xff\xe0\xfe\x1e\x0f\xe0\xc1\xfe\x18\x00\x07\xff\xff\xff\xff\x83\xff\xe0\xfe\x0f\x0f\xe0\xe1\xfe\x18\x00\x07\xff\xff\xff\xff\x83\xff\xe0\xff\x0f\x03\xc1\xe0\xfc\x38\x7f\x87\xff\xff\xff\xff\x83\xff\xe0\xff\x0f\x00\x01\xf0\x00\x30\x7f\x83\xff\xff\xff\xff\x83\xff\xe0\xff\x0f\x80\x03\xf0\x00\x70\xff\xc3\xff\xff\xff\xff\x83\xff\xe0\xff\x0f\xe0\x0f\xfc\x00\xf0\xff\xc3\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\xff\xff\xff\xff\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\xff\xff\xff\xff\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\xff\xff\xff\xff\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\xff\xff\xff\xff\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\xff\xff\xff\xff\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\xff\xff\xff\xff\x83\xfc\x7f\x8f\xc7\xf8\x38\x3f\x81\xf8\xe1\xc3\xff\xff\xff\xff\x83\xfe\x7f\x9f\xe7\xf8\x38\x3f\xc3\xfc\xe1\xc3\xff\xff\xff\xff\x83\x0e\x70\x18\x67\x00\x7c\x30\xe7\x1c\xe1\xc3\xff\xff\xff\xff\x83\x06\x70\x18\x07\x00\x6c\x30\xe6\x0c\xe1\xc3\xff\xff\xff\xff\x83\x06\x7f\x1f\x07\xf8\xec\x30\xee\x00\xff\xc3\xff\xff\xff\xff\x83\xfc\x7f\x8f\xe7\xf8\xce\x3f\xce\x00\xff\xc3\xff\xff\xff\xff\x83\xfc\x70\x03\xe7\x00\xc6\x3f\xce\x00\xe1\xc3\xff\xff\xff\xff\x83\x0e\x70\x00\x77\x01\xfe\x30\xe6\x0e\xe1\xc3\xff\xff\xff\xff\x83\x06\x70\x18\x77\x01\xff\x30\xe7\x0c\xe1\xc3\xff\xff\xff\xff\x83\x06\x7f\xdf\xe7\xf9\x83\x30\x63\xfc\xe1\xc3\xff\xff\xff\xff\x83\x06\x7f\xcf\xc7\xff\x83\x30\x61\xf8\xe1\xc3\xff\xff\xff\xff\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\xff\xff\xff\xff\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\xff\xff\xff\xff\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\xff\xff\xff\xff\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\xff\xff\xff\xff\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\xff\xff\xff\xff\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xfe\x70\x78\x70\x30\x7c\x1c\x1c\xe6\x0f\x9f\xff\xff\xff\xff\xff\xfe\x62\x32\x30\x20\x7c\x0c\x0c\xe4\x47\x1f\xff\xff\xff\xff\xff\xfe\x67\x37\xb3\xe7\xfc\xcd\xec\xe4\xe7\x0f\xff\xff\xff\xff\xbf\xfe\x4f\xb1\xf0\x63\xfc\xcd\xcc\xe4\x3f\x4f\xff\xff\xff\xff\xbf\xfe\x4f\x98\x30\x20\x7c\x0c\x0c\xe6\x0e\x4f\xff\xff\xff\xff\x81\x76\x6f\xbf\x33\xe7\xfc\x1c\xcc\xe7\xe6\x07\xff\xff\xff\xff\xb4\x76\x67\x27\xb7\xe7\xfc\xfd\xcc\xe4\xe4\x07\xff\xff\xff\xff\xa4\xf0\x60\x30\x30\x27\xfc\xfd\xce\x0e\x04\xe7\xff\xff\xff\xff\x8c\xf8\xf8\xf8\x70\x37\xfd\xfd\xef\x1f\x0d\xf7\xff\xff\xff\xff\xfd\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff')
frame = framebuf.FrameBuffer(splash,128,64, framebuf.MONO_HLSB)
oled.invert(1)
oled.fill(0)
oled.blit(frame,0,0)
oled.show()
time.sleep(5)
oled.fill(0)
oled.show()
oled.invert(0)

# Initialize the LED state to 0 (off)
led_state = 0
# Define a callback function to handle received data
def on_rx(data):
    print("Data received: ", data)  # Print the received data
    global led_state  # Access the global variable led_state
    if data == b'toggle\r\n':  # Check if the received data is "toggle"
        print("data is what we want", led_state, led, led.value)
        led_state = 1 - led_state  # Update the LED state
        pico_led.on() if led_state == 1 else pico_led.off() # Toggle the LED state (on/off)
        
    
async def main():
    global count, seconds, voc_level_avg, voc_level_sum, voc_def, show_temp, debounce_time, led_state, display
    
    temperature = temp_sensor.temperature
    # Create a Bluetooth Low Energy (BLE) object
    webInterface = WebServer(temperature, pico_led, led_state, 'iPhone 13 Pro Max', 'zakarias', display)
    
    def serveWrapper(reader, writer):
        return webInterface.serve(reader, writer, led_state)
    
    asyncio.create_task(asyncio.start_server(serveWrapper, "0.0.0.0", 80))
    
 
    # Main Loop
    while True:
#         if not webInterface.isConnected:  # If not connected to Wi-Fi
#             webInterface.disconnect()       # Disconnect from current Wi-Fi network
#             webInterface.connect()    # Reconnect to Wi-Fi network
###################### VOC SENSING ########################  
        if count <= 49:
            if led_state != pico_led.value:
                led_state = pico_led.value
                webInterface.setLedStatus(led_state)
            count += 1
            voc_level_new = voc_def.read_u16() * voc_conv
            voc_level_sum += voc_level_new
            voc_level_avg = voc_level_sum/count
            bigText = writer.Writer(oled, freesans20)
            bigText.set_textpos(0,0)
            if voc_level_avg > 1:
                bigText.printstring("VOC: {}  T^T".format(round(voc_level_avg,1)))
                oled.show()
            else:
                bigText.printstring("VOC: {}  ^_^".format(round(voc_level_avg,1)))
                oled.show()
###################### TEMPERATURE ########################
            temp = temp_sensor.temperature
            humidity = temp_sensor.relative_humidity
            webInterface.setTemperature(temp)
            #adc_voltage = temp.read_u16() * 3.3 / 65535
            #cpu_temp = 27 - (adc_voltage - 0.706)/0.001721
            if seconds <= 5:
                if show_temp:
                    bigText.set_textpos(0,21)
                    bigText.printstring("TEMP: {}C".format(round(temp,1)))
                    oled.show()
                    time.sleep(0.5)
                    seconds += 1
                else:
                    bigText.set_textpos(0,21)
                    bigText.printstring("%RH: {}%".format(round(humidity,2)))
                    oled.show()
                    time.sleep(1)
                    seconds += 1
            else:
                seconds = 0
                show_temp = not show_temp
                oled.fill(0) #clear screen of any artifacts
                oled.show()
        else:
            count = 1  #reset counter
            voc_level_sum = voc_level_avg #reset running sum of VOC readings
            oled.fill(0) #clear screen of any artifacts
            oled.show()

    ##################### RELAY CONTROL ######################
        if voc_level_avg >= voc_threshold:
            fan_relay.on() #relay pin high
            bigText.set_textpos(0,42)
            bigText.printstring("FAN: ON")
            led.value(1)
        else:
            fan_relay.off() #relay pin low
            bigText.set_textpos(0,42) 
            bigText.printstring("FAN: OFF")
            led.value(0)
        if (time.ticks_ms() - debounce_time) > 300:
            if sp.is_connected():  # Check if a BLE connection is established
                sp.on_write(on_rx)  # Set the callback function for data reception
                ledStatus = "On" if led_state == 1 else "Off"
                # Create a message string
                msg="LED State:"+ledStatus+" TEMP: {}C".format(round(temp,1))+" %RH: {}%\r\n".format(round(humidity,2))
                # Send the message via BLE
                sp.send(msg)
                # Update the debounce time    
                debounce_time=time.ticks_ms()

        await asyncio.sleep(0.1)
        print('This message will be printed every 1 seconds')

try:
    asyncio.run(main())  # Run the main asynchronous function
finally:
    asyncio.new_event_loop() #Create a new event loopexcept Exception as e: