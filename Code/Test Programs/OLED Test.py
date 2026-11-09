from machine import Pin, I2C
from Modules import sh1106

i2c = I2C(
    0,
    sda=Pin(6),
    scl=Pin(7),
    freq=400000
)

# Scan i2c to show it is working properly & output to console
# Expected output - [60] or [0x3C] (occasionally [61] or [0x3D])
print(i2c.scan())

# Create display object and show a confirmation on the screen
display = sh1106.SH1106_I2C(
    128,
    64,
    i2c
)

display.fill(0) # Clear screen
display.text("Display\nWorking", 20, 20) # Make text at (20, 20)
display.show() # Display text on screen