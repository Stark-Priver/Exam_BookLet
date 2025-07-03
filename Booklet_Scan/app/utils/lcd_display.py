import time
from RPLCD.i2c import CharLCD
from smbus2 import SMBus # smbus-cffi provides smbus2

# Configuration for the LCD
# Common I2C address for PCF8574 based LCDs. Common alternatives are 0x3f.
# Use `i2cdetect -y 1` on Raspberry Pi to find the address.
DEFAULT_I2C_ADDRESS = 0x27
# Raspberry Pi I2C bus (1 for newer Pis, 0 for older ones)
DEFAULT_I2C_BUS = 1
LCD_COLS = 16 # Common LCD column count (e.g., 16x2 or 20x4)
LCD_ROWS = 2  # Common LCD row count

lcd = None
lcd_active = False

def init_lcd(i2c_address=DEFAULT_I2C_ADDRESS, i2c_bus=DEFAULT_I2C_BUS, cols=LCD_COLS, rows=LCD_ROWS):
    """
    Initializes the LCD display.
    Returns True if successful, False otherwise.
    """
    global lcd, lcd_active
    if lcd_active: # Already initialized
        return True
    try:
        # Initialize SMBus
        bus = SMBus(i2c_bus)
        # Initialize CharLCD
        lcd = CharLCD(i2c_expander='PCF8574',
                      address=i2c_address,
                      port=i2c_bus, # RPLCD uses 'port' for bus number
                      bus=bus, # Pass the initialized bus
                      cols=cols,
                      rows=rows,
                      dotsize=8, # Default dot size
                      charmap='A02', # Common character map
                      auto_linebreaks=True,
                      backlight_enabled=True)
        lcd.clear()
        lcd.write_string("System Ready")
        lcd_active = True
        print("LCD Initialized Successfully.")
        return True
    except Exception as e: # Catch a broader range of exceptions during init
        print(f"Error initializing LCD: {e}")
        print("LCD functionality will be disabled.")
        lcd = None
        lcd_active = False
        return False

def display_message(line1, line2="", clear_first=True, delay_after=None):
    """
    Displays a two-line message on the LCD.
    Clears the display first by default.
    Optionally waits for 'delay_after' seconds.
    """
    global lcd_active # Moved to the top of the function
    if not lcd_active:
        if lcd is None: # Attempt to initialize if not tried before or failed
            print("LCD not active. Attempting to initialize...")
            if not init_lcd(): # If init fails again, just print to console
                print(f"Console LCD: L1: {line1}, L2: {line2}")
                return
        else: # LCD init was tried and failed
            print(f"Console LCD: L1: {line1}, L2: {line2}")
            return

    try:
        if clear_first:
            lcd.clear()

        lcd.cursor_pos = (0, 0)
        lcd.write_string(line1[:LCD_COLS]) # Truncate if too long

        if line2:
            lcd.cursor_pos = (1, 0)
            lcd.write_string(line2[:LCD_COLS]) # Truncate if too long

        if delay_after is not None:
            time.sleep(delay_after)

    except Exception as e: # Catch errors during write (e.g. if LCD disconnects)
        print(f"Error writing to LCD: {e}")
        print("LCD functionality disabled.")
        global lcd_active # Modify global
        lcd_active = False
        # Fallback to console
        print(f"Console LCD: L1: {line1}, L2: {line2}")


def clear_display():
    """Clears the LCD display."""
    global lcd_active # Moved to the top of the function
    if not lcd_active or lcd is None:
        print("Console LCD: Cleared")
        return
    try:
        lcd.clear()
    except Exception as e:
        print(f"Error clearing LCD: {e}")
        print("LCD functionality disabled.")
        global lcd_active # Modify global
        lcd_active = False

# Attempt to initialize LCD when this module is loaded
# This allows the app to try starting the LCD once.
# If it fails, subsequent calls to display_message will use console fallback.
# init_lcd() # Optional: Call init here or let first display_message call it.
# It might be better to call init_lcd() explicitly from the main app startup
# if you want more control or to pass config values.
# For now, display_message will attempt lazy initialization.

if __name__ == '__main__':
    # Example Usage (for testing this module directly)
    print("Testing LCD Module...")
    if init_lcd(): # Try to initialize with default parameters
        display_message("Hello World!", "RPLCD Test")
        time.sleep(3)
        display_message("Line 1 Test", delay_after=2)
        display_message("Line 1 Again", "Line 2 Again", delay_after=3)

        clear_display()
        lcd.write_string("Test Done.")
        print("Test complete. Check LCD.")
    else:
        print("LCD could not be initialized for testing.")
        print("Simulating messages to console via fallback:")
        display_message("Test L1", "Test L2 (fallback)")
        clear_display()

```
