from machine import Pin, I2C
from Modules import sh1106
import network, ntptime, time, neopixel, sys, colorsys

### Setup ###

## Network ##

# Variables #

# Wifi credentials
# CHANGE VALUES TO ACTUAL WIFI NAME AND PASSWORD
ssid = "YOUR WIFI NAME"
password = "YOUR WIFI PASSWORD"
WIFI_TIMEOUT = 30 # Seconds before wifi times out

# Try to connect to wifi with credentials for an amount of attempts, retrying that amount before quitting
def wifiConnect(ssid, password, attempts=3):

    for attempt in range(attempts):

        # If wifi isn't connected try to connect it
        if not wlan.isconnected():

            # Show it is trying to connect
            print("Connecting...")
            centerText("Connecting...", 63, 31, True)

            wifiFailed = False

            # Wait for a second each time until connected or timeout
            try:
                wlan.connect(ssid, password)
                seconds = 0
                while not wlan.isconnected():
                    if seconds >= WIFI_TIMEOUT:
                        raise RuntimeError("Wi-Fi Timed Out")

                    time.sleep(1)

                    seconds += 1

            except RuntimeError as e:

                print(f"Error: {e}")

                # Show that wifi failed to connect
                centerText("Wi-Fi\nTimed Out", 63, 31, True)

                # Wait to show message
                time.sleep(1)

                # If attempts are reached, show error and exit
                if attempt == attempts - 1:
                    wifiFailed = True
                    sys.exit(1)

            else:
                # Show connected properly
                print("Connected")
                centerText("Connected", 63, 31, True)

                # Wait to show message
                time.sleep_ms(500)

            finally:
                if wifiFailed:
                    # Turn off the screen
                    display.poweroff()

                    # Turn off wifi fully
                    if wlan.isconnected():
                        wlan.disconnect()
                    wlan.active(False)


# Set up wifi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# Try to connect to wifi
wifiConnect(ssid, password)


## Time ##

UTC_OFFSET = -6 # CST

# Sync from NTP
ntptime.settime()

# Gets the local time based off of the UTC offset
def getLocal():
    timestamp = time.time() + UTC_OFFSET * 3600
    return time.localtime(timestamp)

## NeoPixels ##

# Variables #
LED_NUM = 60
PIN_NUM = 0
MAX_CURRENT_MA = 1200
QUIESCENT_CURRENT_MA = LED_NUM * 1

# Initialize LEDs
leds = neopixel.NeoPixel(Pin(PIN_NUM), LED_NUM)

target_buffer = [(0, 0, 0)] * LED_NUM

# Turns a hsv color in the format (int 0-360, int 0-100, int 0-100) into an rgb color in the format (int 0-255, int 0-255, int 0-255)
def hsvToRgb(hue, saturation, brightness):
    ## Validate values
    # If any of the arguments aren't integers, throw an error
    if not (isinstance(hue, int) and isinstance(saturation, int) and isinstance(brightness, int)):
        raise TypeError("Incorrect argument value types")

    # Normalize hsv values so they are from 0-1
    norms = (hue/360, saturation/100, brightness/100)

    # Convert normalized hsv values into normalized rgb values
    norms = colorsys.hsv_to_rgb(norms[0], norms[1], norms[2])

    # Scale normalized rgb values so they are from 0-255 again
    rgb = (round(norms[0] * 255), round(norms[1] * 255), round(norms[2] * 255)) # type: ignore

    return rgb

# Sets a pixel with hsv instead of rgb
def setPixelHsv(index, h, s, v):
    r, g, b = hsvToRgb(h, s, v)
    setPixel(index, r, g, b)

# Saves colors to a virtual buffer first to check total power later
def setPixel(index, r, g, b):
    target_buffer[index] = (r, g, b)

# Calculates power requirements and pushes to LEDs
def showSafe():
    channelSum = 0

    # Calculate total potential color values
    for r, g, b in target_buffer:
        channelSum += (r + g + b)

    # Convert color channel values to estimated mA
    # 255 intensity for 1 channel = 20mA. Coefficient: 20/255 = 0.07843
    ledCurrent = channelSum * 0.07843
    totalCurrent = ledCurrent + QUIESCENT_CURRENT_MA

    # Get scale factor if it exceeds safe mA
    scale = 1.0
    if totalCurrent > MAX_CURRENT_MA:
        # Isolate current allowable for light, then find scale
        allowedLedCurrent = MAX_CURRENT_MA - QUIESCENT_CURRENT_MA
        scale = allowedLedCurrent / ledCurrent

    # Apply scaling factor and push to leds
    for i, (r, g, b) in enumerate(target_buffer):
        scaled = (
            int(r * scale),
            int(g * scale),
            int(b * scale)
        )

        leds[i] = (scaled[0], scaled[1], scaled[2])

    leds.write()


## OLED ##

# Makes text centered at a point
def centerText(text, x, y, clearScreen=False):
    if clearScreen:
        display.fill(0) # Clear screen

    # Find length of longest line
    length = 0
    rows = len(text.split("\n"))
    for i in range(rows):
        line = text.split("\n")[i]
        
        if len(line) > length:
            length = len(line)

    display.text(text, centerX(length, x), centerY(rows, y))
    display.show()

# Returns the x of the text centered at a point from the amount of letters
def centerX(letterNum, x):
    return int(x - ((letterNum / 2) * 8))

# Returns the y of the text centered at a point from the amount of rows
def centerY(rowNum, y):
    return int(y - ((rowNum / 2) * 8))

# Set up i2c
i2c = I2C(
    0,
    sda=Pin(9),
    scl=Pin(7),
    freq=400000
)

# Scan i2c to show it is working properly & output to console
# Expected output - [60] or [0x3C] (occasionally [61] or [0x3D])
print(i2c.scan())

# Create display object
display = sh1106.SH1106_I2C(
    128,
    64,
    i2c
)

# Display that it is intitiated properly on both console and screen
print("Display Initiated")
centerText("Screen\nInitiated", 63, 31, True)

# Wait 0.5 seconds to show confirmation
time.sleep_ms(500)


### Main Loop ###

while True:
    ## Perform Functions ##

    time.sleep_ms(100)