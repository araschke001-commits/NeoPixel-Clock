### Setup ###

from machine import Pin
import time

# Variables #
DEBOUNCE_MS = 25 # Ms to wait to read the button press to prevent incorrect reads
buttonState = 1 # If button is pressed or not. 0 means pressed, 1 means depressed
lastChange = 0 # Timestamp for when the button changed last

# Initialize #

# Initialize button at pin 1 as input and pull up
button = Pin(1, Pin.IN, Pin.PULL_UP)

# Functions #

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

### Main loop ###
while True:

    # If button is pressed, reflect that in the console
    if checkButton() == True:
        print("Button Pressed!")

    time.sleep_ms(20)