import time
from .network_utils import get_ip_address # Import for fetching IP

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

# Configuration for the LCD
DEFAULT_I2C_ADDRESS = 0x27
DEFAULT_I2C_BUS = 1
LCD_COLS = 16
LCD_ROWS = 2

lcd = None
lcd_active = False # Ensure this is defined at module level
current_display_mode = "default" # To track what's being displayed (e.g., "ip", "scrolling_message")
scroll_thread = None
stop_scroll_event = None

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
        print("LCD already initialized.")
        return True

    if not I2C_HARDWARE_AVAILABLE:
        print("LCD disabled: I2C libraries not available (e.g., running on Windows).")
        lcd_active = False
        lcd = None
        return False

    try:
        bus = SMBus(i2c_bus)
        if CharLCD is None:
            raise ImportError("CharLCD class not loaded due to missing I2C libraries.")

        lcd = CharLCD(i2c_expander='PCF8574',
                      address=i2c_address,
                      port=i2c_bus,
                      bus=bus,
                      cols=cols,
                      rows=rows,
                      dotsize=8,
                      charmap='A02',
                      auto_linebreaks=True,
                      backlight_enabled=True)
        lcd.clear()
        # Initial message, will be quickly overwritten by IP or other specific messages
        lcd.write_string("Initializing...")
        lcd_active = True
        print("LCD Initialized Successfully.")
        return True
    except Exception as e:
        print(f"Error initializing LCD: {e}")
        print("LCD functionality will be disabled.")
        lcd = None
        lcd_active = False
        return False

def display_ip_address():
    """Displays the IP address on the LCD."""
    global current_display_mode
    stop_scrolling_message_if_active() # Stop any ongoing scrolling

    ip = get_ip_address()
    if not is_lcd_active(): # Try to init if not active
        if not init_lcd():
            print(f"Console LCD: IP: {ip}")
            print(f"Console LCD: Line 2: System Online")
            return

    display_message("IP Address:", ip, clear_first=True)
    current_display_mode = "ip"
    print(f"LCD: Displaying IP Address - {ip}")

def display_message(line1, line2="", clear_first=True, delay_after=None):
    """
    Displays a two-line message on the LCD.
    Clears the display first by default.
    Optionally waits for 'delay_after' seconds.
    """
    global lcd, lcd_active # Added lcd here
    # Ensure this function doesn't interfere if a scroll is active
    # and this is just a simple status update not meant to change mode.
    # However, most calls to display_message will imply stopping scrolls.
    # The caller should manage this, e.g. call stop_scrolling_message_if_active() if needed.

    if not lcd_active:
        # Attempt to initialize if not tried before or failed (e.g. during startup)
        # print("LCD not active in display_message. Attempting to initialize...")
        if not init_lcd(): # If init fails again, just print to console
            print(f"Console LCD: L1: {line1}, L2: {line2}")
            return
        # else:
            # print("LCD initialized successfully from display_message.")

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

    except Exception as e:
        print(f"Error writing to LCD: {e}")
        print("LCD functionality may be disabled.")
        # Don't set lcd_active to False here necessarily,
        # as it might be a transient issue. init_lcd checks hardware.
        # Fallback to console
        print(f"Console LCD: L1: {line1}, L2: {line2}")


def clear_display():
    """Clears the LCD display."""
    global lcd, lcd_active # Added lcd here
    if not lcd_active or lcd is None:
        print("Console LCD: Cleared")
        return
    try:
        lcd.clear()
    except Exception as e:
        print(f"Error clearing LCD: {e}")
        # print("LCD functionality may be disabled.") # Avoid repetitive message

def _scroll_text(line_number, text, delay):
    """
    Internal function to scroll text on a given line.
    This function is intended to be run in a separate thread.
    """
    global lcd, lcd_active, stop_scroll_event, LCD_COLS
    if not lcd_active or lcd is None:
        print(f"LCD not active, cannot scroll: {text}")
        return

    # Pad the text to create a scrolling effect off-screen
    padded_text = " " * LCD_COLS + text + " " * LCD_COLS

    while not stop_scroll_event.is_set():
        for i in range(len(padded_text) - LCD_COLS + 1):
            if stop_scroll_event.is_set():
                break
            frame = padded_text[i:i+LCD_COLS]
            try:
                lcd.cursor_pos = (line_number, 0)
                lcd.write_string(frame)
            except Exception as e:
                print(f"Error during LCD scroll: {e}")
                # Consider stopping the scroll or LCD if errors persist
                # For now, just print and continue trying
                lcd_active = False # Assume LCD is lost
                stop_scroll_event.set() # Stop trying to scroll
                break
            time.sleep(delay)
    # try: # Clear the line after scrolling stops
    #     lcd.cursor_pos = (line_number, 0)
    #     lcd.write_string(" " * LCD_COLS)
    # except: pass


def display_scrolling_message(line1_text, line2_text, scroll_delay=0.3):
    """
    Displays potentially scrolling messages on the LCD.
    If text is longer than LCD_COLS, it will scroll.
    Otherwise, it's displayed statically.
    Manages a thread for scrolling.
    """
    global lcd, lcd_active, scroll_thread, stop_scroll_event, current_display_mode
    import threading

    stop_scrolling_message_if_active() # Stop any previous scrolling

    if not lcd_active:
        if not init_lcd():
            print(f"Console Scroll L1: {line1_text}")
            print(f"Console Scroll L2: {line2_text}")
            return

    lcd.clear()
    current_display_mode = "scrolling_message"
    stop_scroll_event = threading.Event()

    # For line 1
    if len(line1_text) > LCD_COLS:
        # Create and start a new thread for scrolling line 1
        # Making it a daemon thread so it exits when the main program exits
        scroll_thread_l1 = threading.Thread(target=_scroll_text, args=(0, line1_text, scroll_delay), daemon=True)
        scroll_thread_l1.start()
        # We store the first thread, assuming line 1 is primary for scrolling control
        # This simplistic model only handles one primary scroll_thread for now.
        # A more complex system might manage multiple threads.
        scroll_thread = scroll_thread_l1
    else:
        display_message(line1_text, "", clear_first=False) # Display statically on line 1

    # For line 2
    if len(line2_text) > LCD_COLS:
        # If line 1 wasn't scrolling, this becomes the main scroll_thread
        scroll_thread_l2 = threading.Thread(target=_scroll_text, args=(1, line2_text, scroll_delay), daemon=True)
        scroll_thread_l2.start()
        if scroll_thread is None: # If line 1 was static
             scroll_thread = scroll_thread_l2
        # Note: If both lines scroll, 'scroll_thread' will refer to line 1's thread.
        # stop_scrolling_message_if_active will signal the event, stopping both.
    else:
        if line1_text: # Only move cursor if line1 had content
            lcd.cursor_pos = (1,0)
            lcd.write_string(line2_text[:LCD_COLS])
        else: # If line1 was empty, display line2 on line1's position (effectively line 0)
             display_message(line2_text, "", clear_first=False)


def stop_scrolling_message_if_active():
    """Stops the scrolling message thread if it's running."""
    global scroll_thread, stop_scroll_event, current_display_mode
    if stop_scroll_event and not stop_scroll_event.is_set():
        print("Stopping active scroll...")
        stop_scroll_event.set()

    if scroll_thread and scroll_thread.is_alive():
        scroll_thread.join(timeout=1.0) # Wait for thread to finish
        if scroll_thread.is_alive():
            print("Warning: Scroll thread did not terminate cleanly.")

    scroll_thread = None
    # stop_scroll_event = None # Re-created when new scroll starts
    if current_display_mode == "scrolling_message":
        current_display_mode = "default" # Reset mode if scrolling was stopped

if __name__ == '__main__':
    print("Testing LCD Module...")
    if init_lcd():
        display_ip_address()
        time.sleep(5)

        print("Testing static message...")
        display_message("Static Line 1", "Static Line 2", delay_after=3)

        print("Testing scrolling message...")
        # Example link and instructions
        exam_link_placeholder = "go.exam/p123"
        instructions_placeholder = "Scan ID, then Booklet. Be quick!"
        display_scrolling_message(f"Link: {exam_link_placeholder}", instructions_placeholder, scroll_delay=0.3)

        # Let it scroll for a while
        time.sleep(15)

        print("Stopping scroll and displaying IP again...")
        stop_scrolling_message_if_active()
        display_ip_address()
        time.sleep(5)

        clear_display()
        lcd.write_string("Test Done.")
        print("Test complete. Check LCD.")
    else:
        print("LCD could not be initialized for testing.")
        print("Simulating messages to console via fallback:")
        display_ip_address() # Will print to console
        display_message("Test L1", "Test L2 (fallback)")
        # Simulate scrolling for console
        exam_link_placeholder = "go.exam/p123"
        instructions_placeholder = "Scan ID, then Booklet. Be quick!"
        print(f"Console Scroll L1: Link: {exam_link_placeholder}")
        print(f"Console Scroll L2: {instructions_placeholder}")
        clear_display()

