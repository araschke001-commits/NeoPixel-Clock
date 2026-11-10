import network, ntptime, time, sys

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

                # Wait to show message
                time.sleep(1)

                # If attempts are reached, show error and exit
                if attempt == attempts - 1:
                    wifiFailed = True
                    sys.exit(1)

            else:
                # Show connected properly
                print("Connected")

                # Wait to show message
                time.sleep_ms(500)

            finally:
                if wifiFailed:
                    # Turn off wifi fully
                    if wlan.isconnected():
                        wlan.disconnect()
                    wlan.active(False)


# Set up wifi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# Try to connect to wifi
wifiConnect(ssid, password)


## Functions to retrieve the date and time ##

# Sync from NTP
ntptime.settime()

# Gets the hour offset from UTC, in either CST or CDT, depending on daylight savings
def getUtcOffset():
    utcTime = time.gmtime()
    year, month, day, hour = utcTime[0], utcTime[1], utcTime[2], utcTime[3]

    if isDst(year, month, day, hour):
        return -5 # CDT
    else:
        return -6 # CST

UTC_OFFSET = getUtcOffset()

# Gets the local time based off of the UTC offset in the format (year, month, day, hour, minute, second, weekday, yearday)
def getLocal():
    timestamp = time.time() + UTC_OFFSET * 3600
    return time.localtime(timestamp)

# Gets the current date from the time module in the format (year, month, day)
def getDate():
    timestamp = getLocal()
    year = timestamp[0]
    month = timestamp[1]
    day = timestamp[2]
    return year, month, day

# Gets the local time based off of the UTC offset with only the hour, minute, and second being returned
def getTime():
    current = getLocal()

    # Return current hour, minute, second
    return current[3], current[4], current[5]


## Print out date and time ##

date = getDate()
print(f"Date: {date[0]}/{date[1]}/{date[2]}")

timestamp = getLocal()
shortTime = getTime()
print(f"Timestamp: {timestamp[0]}, {timestamp[1]}, {timestamp[2]}; {timestamp[3]}:{timestamp[4]}:{timestamp[5]}; {timestamp[6]}, {timestamp[7]}")
print(f"Time: {shortTime[0]}:{shortTime[1]}:{shortTime[2]}")