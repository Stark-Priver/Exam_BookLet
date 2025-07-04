import os
import time
import json
import logging
import requests
from evdev import InputDevice, categorize, ecodes, list_devices

# --- Configuration ---
# Placeholder: User needs to replace this with the actual event device path for their scanner
# Example: '/dev/input/event3'. Find yours with `sudo libinput list-devices` or check /dev/input/by-id/
SCANNER_DEVICE_PATH = None # OR "/dev/input/by-id/usb-SYMBEYE_Barcode_Scanner_SYMBEYE_Barcode_Scanner-event-kbd"

# Flask API endpoint for submitting scans
FLASK_API_ENDPOINT = "http://127.0.0.1:5000/api/v1/internal_scan"

# Path to the scan_status.json file (relative to this script, assuming it's in Booklet_Scan/)
STATUS_FILE_PATH = os.path.join(os.path.dirname(__file__), 'scan_status.json')

# Logging setup
LOG_FILE = os.path.join(os.path.dirname(__file__), 'scanner_listener.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler() # Also print to console
    ]
)

# --- Key Mapping (Simplified US QWERTY layout) ---
# Does not handle Shift, CapsLock, etc. for simplicity, as barcodes usually use simple chars/digits.
# Customize if your barcodes use other characters or your scanner has a different layout.
KEYCODE_MAP = {
    ecodes.KEY_1: '1', ecodes.KEY_2: '2', ecodes.KEY_3: '3', ecodes.KEY_4: '4', ecodes.KEY_5: '5',
    ecodes.KEY_6: '6', ecodes.KEY_7: '7', ecodes.KEY_8: '8', ecodes.KEY_9: '9', ecodes.KEY_0: '0',
    ecodes.KEY_A: 'A', ecodes.KEY_B: 'B', ecodes.KEY_C: 'C', ecodes.KEY_D: 'D', ecodes.KEY_E: 'E',
    ecodes.KEY_F: 'F', ecodes.KEY_G: 'G', ecodes.KEY_H: 'H', ecodes.KEY_I: 'I', ecodes.KEY_J: 'J',
    ecodes.KEY_K: 'K', ecodes.KEY_L: 'L', ecodes.KEY_M: 'M', ecodes.KEY_N: 'N', ecodes.KEY_O: 'O',
    ecodes.KEY_P: 'P', ecodes.KEY_Q: 'Q', ecodes.KEY_R: 'R', ecodes.KEY_S: 'S', ecodes.KEY_T: 'T',
    ecodes.KEY_U: 'U', ecodes.KEY_V: 'V', ecodes.KEY_W: 'W', ecodes.KEY_X: 'X', ecodes.KEY_Y: 'Y',
    ecodes.KEY_Z: 'Z',
    ecodes.KEY_MINUS: '-', ecodes.KEY_EQUAL: '=', ecodes.KEY_SLASH: '/', ecodes.KEY_BACKSLASH: '\\',
    ecodes.KEY_SPACE: ' ', ecodes.KEY_DOT: '.', ecodes.KEY_COMMA: ',',
    # Add more mappings as needed based on typical barcode content
    # Numeric keypad keys might also be relevant depending on scanner config
    ecodes.KEY_KP1: '1', ecodes.KEY_KP2: '2', ecodes.KEY_KP3: '3', ecodes.KEY_KP4: '4',
    ecodes.KEY_KP5: '5', ecodes.KEY_KP6: '6', ecodes.KEY_KP7: '7', ecodes.KEY_KP8: '8',
    ecodes.KEY_KP9: '9', ecodes.KEY_KP0: '0', ecodes.KEY_KPDOT: '.',
    ecodes.KEY_KPSLASH: '/', ecodes.KEY_KPASTERISK: '*', ecodes.KEY_KPMINUS: '-',
    ecodes.KEY_KPPLUS: '+', ecodes.KEY_KPENTER: '\n', # Assuming KPEnter means end of scan
    ecodes.KEY_ENTER: '\n' # Assuming Enter means end of scan
}

def find_scanner_device():
    """Attempts to find a suitable scanner device automatically or guides the user."""
    global SCANNER_DEVICE_PATH
    if SCANNER_DEVICE_PATH and os.path.exists(SCANNER_DEVICE_PATH):
        logging.info(f"Using pre-configured scanner path: {SCANNER_DEVICE_PATH}")
        return SCANNER_DEVICE_PATH

    devices = [InputDevice(path) for path in list_devices()]
    scanners = []
    for device in devices:
        # Heuristic: scanners often have "scan" or "hid" in name and EV_KEY capability
        # This is very basic and might need refinement for specific hardware
        name_lower = device.name.lower()
        if ("scan" in name_lower or "barcod" in name_lower or "hid" in name_lower or "keyboard" in name_lower):
            capabilities = device.capabilities(verbose=False)
            if ecodes.EV_KEY in capabilities:
                scanners.append({'path': device.path, 'name': device.name})

    if not scanners:
        logging.error("No potential scanner devices found automatically.")
        logging.info("Please manually identify your scanner's event device path (e.g., /dev/input/eventX).")
        logging.info("You can try tools like 'sudo libinput list-devices' or check '/dev/input/by-id/'.")
        logging.info("Then, set SCANNER_DEVICE_PATH at the top of this script.")
        return None

    if len(scanners) == 1:
        SCANNER_DEVICE_PATH = scanners[0]['path']
        logging.info(f"Automatically selected scanner: {scanners[0]['name']} on {SCANNER_DEVICE_PATH}")
        return SCANNER_DEVICE_PATH
    else:
        logging.warning("Multiple potential scanner devices found:")
        for i, s in enumerate(scanners):
            logging.warning(f"  {i}: {s['name']} ({s['path']})")
        logging.info("Please choose one and set SCANNER_DEVICE_PATH at the top of this script.")
        # You could add interactive selection here if running interactively,
        # but for a background script, pre-configuration is better.
        return None


def read_scan_status():
    """Reads the scan_status.json file."""
    try:
        if not os.path.exists(STATUS_FILE_PATH):
            # logging.warning(f"Status file not found: {STATUS_FILE_PATH}. Assuming no active scan.")
            return None # Or a default "inactive" status
        with open(STATUS_FILE_PATH, 'r') as f:
            status_data = json.load(f)
            return status_data
    except (IOError, json.JSONDecodeError) as e:
        logging.error(f"Error reading or parsing status file {STATUS_FILE_PATH}: {e}")
        return None

def post_scan_data(payload):
    """Posts the scanned data to the Flask API."""
    try:
        response = requests.post(FLASK_API_ENDPOINT, json=payload, timeout=5)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        logging.info(f"Data posted successfully: {payload}. Response: {response.json()}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error posting data to Flask API: {e}")
        return None

def main_loop():
    """Main loop to listen for scanner input and process it."""
    effective_scanner_path = find_scanner_device()
    if not effective_scanner_path:
        logging.error("Scanner device not configured or found. Exiting.")
        return

    try:
        device = InputDevice(effective_scanner_path)
        device.grab() # Grab device to prevent other applications (like X server) from getting events
        logging.info(f"Listening for barcode scans on {device.name} ({effective_scanner_path})...")
    except Exception as e:
        logging.error(f"Failed to open or grab scanner device {effective_scanner_path}: {e}")
        logging.error("Ensure this script has permissions (e.g., run with sudo or set udev rules).")
        return

    barcode_buffer = []
    try:
        for event in device.read_loop():
            if event.type == ecodes.EV_KEY:
                key_event = categorize(event)
                if key_event.keystate == key_event.key_down: # Process on key press
                    keycode = key_event.scancode # or key_event.keycode for a more abstract representation

                    char = KEYCODE_MAP.get(keycode)

                    if char == '\n': # End of barcode (Enter key)
                        if barcode_buffer:
                            scanned_string = "".join(barcode_buffer)
                            logging.info(f"Barcode scanned: {scanned_string}")

                            status = read_scan_status()
                            if status and status.get("active_exam_id") and status.get("expected_input_type") != "none":
                                api_payload = {
                                    "scanned_data": scanned_string,
                                    "data_type": status["expected_input_type"],
                                    "active_exam_id": status["active_exam_id"]
                                }
                                if status["expected_input_type"] == "booklet" and status.get("verified_student_id"):
                                    api_payload["verified_student_id"] = status["verified_student_id"]

                                post_scan_data(api_payload)
                            else:
                                logging.warning(f"Scan '{scanned_string}' received, but no active exam or invalid status. Ignoring.")

                            barcode_buffer = [] # Clear buffer for next scan
                        else:
                            logging.debug("Enter pressed with empty buffer, ignoring.")
                    elif char: # Regular character
                        barcode_buffer.append(char)
                    else:
                        logging.debug(f"Unknown keycode pressed: {keycode}")
    except KeyboardInterrupt:
        logging.info("Scanner listener stopped by user.")
    except Exception as e:
        logging.error(f"An error occurred in the main loop: {e}")
    finally:
        if 'device' in locals() and device:
            try:
                device.ungrab()
                device.close()
                logging.info("Scanner device ungrabbed and closed.")
            except Exception as e_close:
                logging.error(f"Error closing device: {e_close}")


if __name__ == "__main__":
    logging.info("Starting scanner listener script...")
    # Small delay to allow Flask app to start if both are launched together
    # time.sleep(5) # Uncomment if needed, but status file check should handle races

    # Initialize status file from listener side if it's missing, so it doesn't crash on first read
    # This is mostly for dev. In prod, Flask app should manage this.
    if not os.path.exists(STATUS_FILE_PATH):
        logging.info(f"Status file {STATUS_FILE_PATH} not found. Creating a default inactive one.")
        # Create a default inactive status file
        default_status = {
            "active_exam_id": None, "exam_name": None, "expected_input_type": "none",
            "verified_student_id": None, "verified_student_name": None,
            "status_timestamp": datetime.now(timezone.utc).isoformat()
        }
        try:
            with open(STATUS_FILE_PATH, 'w') as f_status:
                json.dump(default_status, f_status, indent=4)
        except IOError as e_io:
            logging.error(f"Could not create initial status file: {e_io}")

    main_loop()
    logging.info("Scanner listener script finished.")

```
