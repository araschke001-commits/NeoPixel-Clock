from machine import Pin, I2C
from Modules import sh1106
import network, ntptime, time, neopixel, sys, colorsys

### Setup ###

## Variables ##

# Network #
# CHANGE VALUES TO ACTUAL WIFI NAME AND PASSWORD
ssid = "YOUR WIFI NAME"
password = "YOUR WIFI PASSWORD"
WIFI_TIMEOUT = 30 # Seconds before wifi times out

# Time (UTC_OFFSET excluded because it relies on a helper function) #
SYNC_INTERVAL = 60 # Syncs time every minute
lastSync = 0 # Timestamp of last sync
lastWallSecond = None
secondStartTicks = time.ticks_ms()

# Switch #
DEBOUNCE_MS = 25 # Ms to wait to read the button press to prevent incorrect reads
buttonState = 1 # If button is pressed or not. 0 means pressed, 1 means depressed
lastChange = 0 # Timestamp for when the button changed last
mode = 0 # The clock mode, int from 0-1, 0 shows h, m, s. 1 shows h, m, s, ms.

# NeoPixels #
LED_NUM = 60
PIN_NUM = 0
MAX_CURRENT_MA = 1200
QUIESCENT_CURRENT_MA = LED_NUM * 1

# Shuts everything down unless you choose to exclude something
def shutDown(isWifi=True, isDisplay=True):
    # Turn off wifi fully if it exists
    if wlan and isWifi:
        if wlan.isconnected():
            wlan.disconnect()
        wlan.active(False)
    
    # Turn off the screen if it exists
    if display and isDisplay:
        display.poweroff()

## Network ##

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

                # If attempts are reached, flag an error and exit
                if attempt == attempts - 1:
                    wifiFailed = True
                    sys.exit(1)

            except Exception as e:

                print(f"Unknown error: {e}")

                # Show that an unknown error occurred
                centerText("Unknown\nError", 63, 31, True)

                # Wait to show message
                time.sleep(1)

                # If attempts are reached, flag an error and exit
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
                    shutDown()


## DST Functions ##

# Helper function to find the day in the month of the nth sunday
def nthSunday(year, month, n):
    # Get weekday of 1st of month (0 = Monday, 6 = Sunday)
    firstTick = time.mktime((year, month, 1, 0, 0, 0, 0, 0))
    firstWeekday = time.localtime(firstTick)[6]

    # Calculate days until the first sunday
    daysToFirstSunday = (6 - firstWeekday) % 7

    # Return the day of the month
    return 1 + daysToFirstSunday + (n - 1) * 7

# Returns True if the date is in DST and False if it is not (for the US)
# US DST starts 2nd Sunday in March, ends 1st Sunday in November
def isDst(year, month, day, hour):
    # Calculate the transition days for the given year
    startDay = nthSunday(year, 3, 2) # 2nd Sunday in March
    endDay = nthSunday(year, 11, 1) # 1st Sunday in November

    # Check if the date falls on DST
    if month < 3 or month > 11:
        return False
    if month > 3 and month < 11:
        return True
    if month == 3:
        return day > startDay or (day == startDay and hour >= 8)
    if month == 11:
        return day < endDay or (day == endDay and hour < 7)
    return False


## Time ##

# Gets the hour offset from UTC, in either CST or CDT, depending on daylight savings
def getUtcOffset():
    utcTime = time.gmtime()
    year, month, day, hour = utcTime[0], utcTime[1], utcTime[2], utcTime[3]

    if isDst(year, month, day, hour):
        return -5 # CDT
    else:
        return -6 # CST

# Gets the local time based off of the UTC offset in the format (year, month, day, hour, minute, second, weekday, yearday)
def getLocal():
    timestamp = time.time() + UTC_OFFSET * 3600
    return time.localtime(timestamp)

# Gets the current date from the time module in the format (year, month, day)
def getDate():
    timestamp = getLocal()
    year = int(timestamp[0])
    month = int(timestamp[1])
    day = int(timestamp[2])
    return year, month, day

# Gets the local time based off of the UTC offset with only the hour, minute, and second being returned
def getTime():
    current = getLocal()

    # Return current hour, minute, second
    return int(current[3]), int(current[4]), int(current[5])

def timeConnect():
    global lastSync, SYNC_INTERVAL, UTC_OFFSET

    timeFailed = False
    now = time.time()

    if now - lastSync > SYNC_INTERVAL:
        for i in range(3):
            try:
                ntptime.settime()

            except Exception:
                if i < 2:
                    print("Time reset failed, retrying...")
                    centerText("Time Reset\nFailed", 63, 31, True)
                    time.sleep(1)

                else:
                    timeFailed = True
                    print("Time reset failed, quitting...")
                    centerText("Time Reset\nFailed*", 63, 31, True)

                    time.sleep(1)
                    sys.exit(1)
                    
            else:
                lastSync = now

                # Update UTC_OFFSET
                UTC_OFFSET = getUtcOffset()
                
                break

            finally:
                if timeFailed == True:
                    shutDown()


## Switch ##

# Initialize #

# Initialize button at pin 1 as input and pull up
button = Pin(1, Pin.IN, Pin.PULL_UP)

# Function(s) #

# Returns True if the button is pressed and False otherwise, accounting for debouncing
def checkButton():
    global buttonState, lastChange

    now = time.ticks_ms()
    val = button.value()

    # Check if time difference exceeds debouncing time
    if time.ticks_diff(now, lastChange) >= DEBOUNCE_MS:

        # Check if the button changed since last time
        if val != buttonState:

            lastChange = now
            buttonState = val

            if val == 0:
                return True

    return False


## NeoPixels ##

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

# Sets pixels just before specified led (going a certain length) in the color specified but dimmer
def makeTrail(index, length, rgb):
    rgbVals = rgb

    for i in range(index - 1, index - (1 + length), -1):
        # Half all of the values in rgbVals
        rgbVals = (round(rgbVals[0]/1.5), round(rgbVals[1]/1.5), round(rgbVals[2]/1.5))
        
        setPixel(i, rgbVals[0], rgbVals[1], rgbVals[2])


## OLED ##

# Makes text centered at a point
def centerText(text, x, y, clearScreen=False):
    if clearScreen:
        display.fill(0) # Clear screen

    # Find how many rows there are
    rows = len(text.split("\n"))

    # Display each row individually, each centered horizontally and spaced evenly vertically
    for i in range(rows):
        length = len(text.split("\n")[i])

        display.text(text.split("\n")[i], centerX(length, x), centerY(1, y + (i - (rows -1) / 2) * 10))

    display.show()

    return None

# Returns the x of the text centered at a point from the amount of letters
def centerX(letterNum, x):
    return int(x - ((letterNum / 2) * 8))

# Returns the y of the text centered at a point from the amount of rows
def centerY(rowNum, y):
    return int(y - ((rowNum / 2) * 8))

# Set up i2c
i2c = I2C(
    0,
    sda=Pin(8),
    scl=Pin(9),
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


## Initialize ##

# Set up wifi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# Try to connect to wifi initially
wifiConnect(ssid, password)


### Main Loop ###

while True:

    # The time at the start of the frame to be able to keep a steady fps
    frameStart = time.ticks_ms()

    ## Network ##

    # Try to reconnect to wifi if disconnected
    wifiConnect(ssid, password)


    ## Time ##

    # Reconnect to the time if it has been too long since last reconnect
    timeConnect()

    date = getDate()
    shortTime = getTime()

    nowTicks = time.ticks_ms()
    wallSecond = int(time.time())

    if wallSecond != lastWallSecond:
        lastWallSecond = wallSecond
        secondStartTicks = nowTicks


    ## Switch ##

    # If the button is pressed, switch the mode 0 <-> 1
    if checkButton() == True:
        mode = (mode + 1) % 2


    ## NeoPixels ##

    # Clear all of the leds to start so the colors don't stay forever
    target_buffer = [(0, 0, 0)] * LED_NUM

    # Display hour led in yellowish white
    hourLed = int(((shortTime[0] % 12) * 5) + ((shortTime[1] / 60) * 5)) # Gets which led will light up based on a 12 hr clock face
    setPixel(hourLed, 85, 73, 56)

    # Display minute led in white
    setPixel(shortTime[1], 75, 75, 75)
    # Make a short trail behind the minute led for 1 led in white
    makeTrail(shortTime[1], 1, (75, 75, 75))

    # Display second led in whitish blue
    setPixel(shortTime[2], 65, 76, 87)
    # Make a trail behind the second led for 3 leds in whitish blue
    makeTrail(shortTime[2], 3, (65, 76, 87))

    # Mode 1 (out of 0-1): include fractions of a second (1/60) in a dim red color
    if mode == 1:
        fractionMs = time.ticks_diff(nowTicks, secondStartTicks) % 1000 # Decimal for the #/60 fraction (not rounded yet)
        fractionLed = fractionMs * LED_NUM // 1000 # Round the fraction into the clean number for the LED updated

        # Set the correct pixel to a dim red
        setPixel(fractionLed, 25, 0, 0)
        # Make a longer trail out from the led in dim red for a length of 9
        makeTrail(fractionLed, 9, (25, 0, 0))

    # Write the changes to the LEDs while staying under max brightness
    showSafe()


    ## OLED ##

    # Get the date in format (year, month, day), all as integers
    date = getDate()

    # Components of date, formatted as strings with 2 (or 4) digits
    year = str(date[0]).zfill(4)
    month = str(date[1]).zfill(2)
    day = str(date[2]).zfill(2)

    # Display the date on the screen (MM/DD/YYYY), centered
    centerText(f"{month}/{day}/{year}", 63, 31, True)


    ## Calculate Delay ##

    current = getTime()

    # Loop 60 times a second for fraction leds, keeping it consistent
    elapsed = time.ticks_diff(time.ticks_ms(), frameStart)

    if elapsed < 17:
        time.sleep_ms(17 - elapsed)