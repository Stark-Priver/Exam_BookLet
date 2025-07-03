import time


DEFAULT_I2C_ADDRESS = 0x27  # Example: Common I2C address for 16x2 LCD with PCF8574
DEFAULT_I2C_BUS = 1         # For Raspberry Pi, usually bus 1
LCD_COLS = 16               # For 16x2 LCD: 16 columns
LCD_ROWS = 2                # For 16x2 LCD: 2 rows

I2C_HARDWARE_AVAILABLE = False
CharLCD = None
SMBus = None

try:
    from RPLCD.i2c import CharLCD
    from smbus2 import SMBus # smbus-cffi provides smbus2
    I2C_HARDWARE_AVAILABLE = True
    print("I2C libraries loaded successfully.")
except ImportError:
    print("Warning: I2C libraries (RPLCD or smbus2) not found. LCD will be disabled. This is expected on non-Pi systems.")
    pass # Continue without I2C specific libraries

# # Configuration for the LCD
# # Common I2C address for PCF8574 based LCDs. Common alternatives are 0x3f.
# # Use `i2cdetect -y 1` on Raspberry Pi to find the address.
# DEFAULT_I2C_ADDRESS = 0x27
# # Raspberry Pi I2C bus (1 for newer Pis, 0 for older ones)
# DEFAULT_I2C_BUS = 1
# LCD_COLS = 16 # Common LCD column count (e.g., 16x2 or 20x4)
# LCD_ROWS = 2  # Common LCD row count

lcd = None
lcd_active = False # Ensure this is defined at module level

def is_lcd_active():
    """Returns the current status of lcd_active."""
    return lcd_active

def init_lcd(i2c_address=DEFAULT_I2C_ADDRESS, i2c_bus=DEFAULT_I2C_BUS, cols=LCD_COLS, rows=LCD_ROWS):
    """
    Initializes the LCD display.
    Returns True if successful, False otherwise.
    """
    global lcd, lcd_active
    if lcd_active: # Already initialized
        return True

    if not I2C_HARDWARE_AVAILABLE:
        print("LCD disabled: I2C libraries not available (e.g., running on Windows).")
        lcd_active = False
        lcd = None
        return False

    try:
        # Initialize SMBus
        bus = SMBus(i2c_bus)
        # Initialize CharLCD
        # Ensure CharLCD is not None before calling it
        if CharLCD is None:
            raise ImportError("CharLCD class not loaded due to missing I2C libraries.")

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
    if not is_lcd_active(): # Use the getter
        # Check if lcd object itself is None which means init was never even attempted or failed early
        # or if I2C_HARDWARE_AVAILABLE is false from the start
        if lcd is None or not I2C_HARDWARE_AVAILABLE:
            print("LCD not available or not initialized. Attempting to initialize...")
            if not init_lcd(): # If init fails again, just print to console
                print(f"Console LCD: L1: {line1}, L2: {line2}")
                return
            # If init_lcd somehow succeeded but lcd_active is still false (should not happen with current init_lcd logic)
            # or if init_lcd succeeded and lcd_active is true now
            if not is_lcd_active():
                 print(f"Console LCD: L1: {line1}, L2: {line2}")
                 return
        else: # lcd object exists but lcd_active is False (e.g. a write error occurred previously)
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

    except Exception as e:  # Catch errors during write (e.g. if LCD disconnects)
        # global lcd_active # Already declared at function top
        print(f"Error writing to LCD: {e}")
        print("LCD functionality disabled.")
        lcd_active = False # Corrected from True to False
        # Fallback to console
        print(f"Console LCD: L1: {line1}, L2: {line2}")



def clear_display():
    """Clears the LCD display."""
    global lcd_active # Moved to the top of the function
    if not is_lcd_active(): # Use the getter
        print("Console LCD: Cleared")
        return
    try:
        lcd.clear()
    except Exception as e:
        print(f"Error clearing LCD: {e}")
        print("LCD functionality disabled.")
        # global lcd_active # Already declared at function top
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
        if lcd: # Check if lcd object exists before writing
            lcd.write_string("Test Done.")
        print("Test complete. Check LCD.")
    else:
        print("LCD could not be initialized for testing.")
        print("Simulating messages to console via fallback:")
        display_message("Test L1", "Test L2 (fallback)")
        clear_display()
```
