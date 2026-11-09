# Might have to upload a neopixel library manually if this doesn't work
import neopixel, time, colorsys

from machine import Pin

leds = neopixel.NeoPixel(Pin(0), 60)

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

i = 0
while True:
    # Make the leds go around in a circle
    leds.fill((0, 0, 0)) # Clear all of the neopixels
    leds[i] = (255, 255, 255) # Make the current led turn white
    leds.write() # Write the values to the leds

    # Wait to make it go around once every 6 seconds
    time.sleep_ms(100)