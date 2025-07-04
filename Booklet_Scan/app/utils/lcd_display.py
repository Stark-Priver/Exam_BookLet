import time
from .network_utils import get_ip_address  # Import for fetching IP

I2C_HARDWARE_AVAILABLE = False
CharLCD = None
SMBus = None

try:
    from RPLCD.i2c import CharLCD
    from smbus2 import SMBus
    I2C_HARDWARE_AVAILABLE = True
    print("I2C libraries loaded successfully.")
except ImportError:
    print("Warning: I2C libraries (RPLCD or smbus2) not found. LCD will be disabled.")
    pass

DEFAULT_I2C_ADDRESS = 0x27
DEFAULT_I2C_BUS = 1
LCD_COLS = 16
LCD_ROWS = 2

lcd = None
lcd_active = False
current_display_mode = "default"
scroll_thread = None
stop_scroll_event = None


def is_lcd_active():
    return lcd_active


def init_lcd(i2c_address=DEFAULT_I2C_ADDRESS, i2c_bus=DEFAULT_I2C_BUS, cols=LCD_COLS, rows=LCD_ROWS):
    global lcd, lcd_active

    if lcd_active:
        print("LCD already initialized.")
        return True

    if not I2C_HARDWARE_AVAILABLE:
        print("LCD disabled: I2C libraries not available.")
        lcd_active = False
        lcd = None
        return False

    try:
        bus = SMBus(i2c_bus)

        lcd = CharLCD(i2c_expander='PCF8574',
                      address=i2c_address,
                      bus=bus,
                      cols=cols,
                      rows=rows,
                      dotsize=8,
                      charmap='A02',
                      auto_linebreaks=True,
                      backlight_enabled=True)

        lcd.clear()
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
    global current_display_mode
    stop_scrolling_message_if_active()

    ip = get_ip_address()
    if not is_lcd_active():
        if not init_lcd():
            print(f"Console LCD: IP: {ip}")
            print(f"Console LCD: Line 2: System Online")
            return

    display_message("IP Address:", ip, clear_first=True)
    current_display_mode = "ip"
    print(f"LCD: Displaying IP Address - {ip}")


def display_message(line1, line2="", clear_first=True, delay_after=None):
    global lcd, lcd_active

    if not lcd_active:
        if not init_lcd():
            print(f"Console LCD: L1: {line1}, L2: {line2}")
            return

    try:
        if clear_first:
            lcd.clear()

        lcd.cursor_pos = (0, 0)
        lcd.write_string(line1[:LCD_COLS])

        if line2:
            lcd.cursor_pos = (1, 0)
            lcd.write_string(line2[:LCD_COLS])

        if delay_after:
            time.sleep(delay_after)

    except Exception as e:
        print(f"Error writing to LCD: {e}")
        print(f"Console LCD: L1: {line1}, L2: {line2}")


def clear_display():
    global lcd, lcd_active
    if not lcd_active or lcd is None:
        print("Console LCD: Cleared")
        return
    try:
        lcd.clear()
    except Exception as e:
        print(f"Error clearing LCD: {e}")


def _scroll_text(line_number, text, delay):
    global lcd, lcd_active, stop_scroll_event, LCD_COLS

    if not lcd_active or lcd is None:
        print(f"LCD not active, cannot scroll: {text}")
        return

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
                lcd_active = False
                stop_scroll_event.set()
                break
            time.sleep(delay)


def display_scrolling_message(line1_text, line2_text, scroll_delay=0.3):
    global lcd, lcd_active, scroll_thread, stop_scroll_event, current_display_mode
    import threading

    stop_scrolling_message_if_active()

    if not lcd_active:
        if not init_lcd():
            print(f"Console Scroll L1: {line1_text}")
            print(f"Console Scroll L2: {line2_text}")
            return

    lcd.clear()
    current_display_mode = "scrolling_message"
    stop_scroll_event = threading.Event()

    if len(line1_text) > LCD_COLS:
        scroll_thread_l1 = threading.Thread(target=_scroll_text, args=(0, line1_text, scroll_delay), daemon=True)
        scroll_thread_l1.start()
        scroll_thread = scroll_thread_l1
    else:
        display_message(line1_text, "", clear_first=False)

    if len(line2_text) > LCD_COLS:
        scroll_thread_l2 = threading.Thread(target=_scroll_text, args=(1, line2_text, scroll_delay), daemon=True)
        scroll_thread_l2.start()
        if scroll_thread is None:
            scroll_thread = scroll_thread_l2
    else:
        if line1_text:
            lcd.cursor_pos = (1, 0)
            lcd.write_string(line2_text[:LCD_COLS])
        else:
            display_message(line2_text, "", clear_first=False)


def stop_scrolling_message_if_active():
    global scroll_thread, stop_scroll_event, current_display_mode

    if stop_scroll_event and not stop_scroll_event.is_set():
        print("Stopping active scroll...")
        stop_scroll_event.set()

    if scroll_thread and scroll_thread.is_alive():
        scroll_thread.join(timeout=1.0)
        if scroll_thread.is_alive():
            print("Warning: Scroll thread did not terminate cleanly.")

    scroll_thread = None

    if current_display_mode == "scrolling_message":
        current_display_mode = "default"


if __name__ == '__main__':
    print("Testing LCD Module...")

    if init_lcd():
        display_ip_address()
        time.sleep(5)

        print("Testing static message...")
        display_message("Static Line 1", "Static Line 2", delay_after=3)

        print("Testing scrolling message...")
        exam_link = "go.exam/p123"
        instructions = "Scan ID, then Booklet. Be quick!"
        display_scrolling_message(f"Link: {exam_link}", instructions, scroll_delay=0.3)

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
        display_ip_address()
        display_message("Test L1", "Test L2 (fallback)")
        exam_link = "go.exam/p123"
        instructions = "Scan ID, then Booklet. Be quick!"
        print(f"Console Scroll L1: Link: {exam_link}")
        print(f"Console Scroll L2: {instructions}")
        clear_display()
