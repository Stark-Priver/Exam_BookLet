import json
import os
from datetime import datetime, timezone
from flask import current_app

# Path for the scan_status.json file (project root)
# Assuming this util file is in app/utils/, so project root is three levels up.
SCAN_STATUS_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'scan_status.json')

DEFAULT_STATUS = {
    "active_exam_id": None,
    "exam_name": None,
    "expected_input_type": "none",
    "verified_student_id": None,
    "verified_student_name": None,
    "status_timestamp": None # Will be set when written
}

def read_scan_status():
    """Reads the scan_status.json file. Returns default status if not found or error."""
    if not os.path.exists(SCAN_STATUS_FILE_PATH):
        if current_app:
            current_app.logger.warning(f"Status file not found: {SCAN_STATUS_FILE_PATH}. Returning default inactive status.")
        else: # For scanner_listener running outside app context initially
            print(f"Warning: Status file not found: {SCAN_STATUS_FILE_PATH}. Returning default inactive status.")
        default_data = DEFAULT_STATUS.copy()
        default_data["status_timestamp"] = datetime.now(timezone.utc).isoformat()
        # Attempt to create it with default status if it's missing, to help scanner_listener
        try:
            with open(SCAN_STATUS_FILE_PATH, 'w') as f:
                json.dump(default_data, f, indent=4)
            if current_app: current_app.logger.info("Created default status file.")
            else: print("Created default status file.")
        except IOError:
            if current_app: current_app.logger.error("Could not create default status file on read.")
            else: print("Error: Could not create default status file on read.")
        return default_data
    try:
        with open(SCAN_STATUS_FILE_PATH, 'r') as f:
            status_data = json.load(f)
            # Ensure all default keys are present
            for key, value in DEFAULT_STATUS.items():
                if key not in status_data:
                    status_data[key] = value
            return status_data
    except (IOError, json.JSONDecodeError) as e:
        if current_app:
            current_app.logger.error(f"Error reading or parsing status file {SCAN_STATUS_FILE_PATH}: {e}")
        else:
            print(f"Error reading or parsing status file {SCAN_STATUS_FILE_PATH}: {e}")
        default_data = DEFAULT_STATUS.copy()
        default_data["status_timestamp"] = datetime.now(timezone.utc).isoformat()
        return default_data


def write_scan_status(status_data):
    """Writes the given data to the scan_status.json file."""
    try:
        # Ensure all keys from DEFAULT_STATUS are present before writing
        current_status_content = status_data.copy() # Work with a copy
        for key, default_value in DEFAULT_STATUS.items():
            if key not in current_status_content:
                current_status_content[key] = default_value

        current_status_content["status_timestamp"] = datetime.now(timezone.utc).isoformat() # Always update timestamp

        with open(SCAN_STATUS_FILE_PATH, 'w') as f:
            json.dump(current_status_content, f, indent=4)

        log_message = f"Scan status updated: {current_status_content}"
        if current_app:
            current_app.logger.info(log_message)
        else:
            print(log_message) # Fallback for scripts
    except IOError as e:
        log_message_err = f"Error writing scan status file: {e}"
        if current_app:
            current_app.logger.error(log_message_err)
        else:
            print(log_message_err)


def clear_scan_status():
    """Clears the scan status, indicating no active exam for scanning."""
    status_to_write = DEFAULT_STATUS.copy()
    # No need to set timestamp here, write_scan_status will do it.
    write_scan_status(status_to_write)


def initialize_scan_status_file():
    """Initializes the scan status file if it doesn't exist or is invalid."""
    if not os.path.exists(SCAN_STATUS_FILE_PATH):
        if current_app: current_app.logger.info(f"Status file not found at {SCAN_STATUS_FILE_PATH}, initializing.")
        else: print(f"Status file not found at {SCAN_STATUS_FILE_PATH}, initializing.")
        clear_scan_status()
    else:
        # Validate existing file content, clear if malformed
        try:
            with open(SCAN_STATUS_FILE_PATH, 'r') as f:
                data = json.load(f)
                if not all(key in data for key in ["active_exam_id", "expected_input_type"]):
                    if current_app: current_app.logger.warning("Scan status file is malformed. Re-initializing.")
                    else: print("Warning: Scan status file is malformed. Re-initializing.")
                    clear_scan_status()
        except (json.JSONDecodeError, IOError) as e:
            log_message_err = f"Error reading scan status file during init: {e}. Re-initializing."
            if current_app: current_app.logger.error(log_message_err)
            else: print(log_message_err)
            clear_scan_status()

if __name__ == '__main__':
    # Test functions (if run directly, current_app won't be available)
    print("Testing status_utils.py...")
    if os.path.exists(SCAN_STATUS_FILE_PATH):
        os.remove(SCAN_STATUS_FILE_PATH)

    print("\n1. Initializing file (should create with defaults):")
    initialize_scan_status_file() # Relies on print for logging without app context
    print(f"File exists: {os.path.exists(SCAN_STATUS_FILE_PATH)}")
    current_data = read_scan_status()
    print(f"Read data: {current_data}")
    assert current_data["active_exam_id"] is None

    print("\n2. Writing new status:")
    new_data = {
        "active_exam_id": 123,
        "exam_name": "Test Exam",
        "expected_input_type": "student",
        "verified_student_id": None,
        "verified_student_name": None
    }
    write_scan_status(new_data)
    current_data = read_scan_status()
    print(f"Read data: {current_data}")
    assert current_data["active_exam_id"] == 123
    assert current_data["expected_input_type"] == "student"

    print("\n3. Clearing status:")
    clear_scan_status()
    current_data = read_scan_status()
    print(f"Read data: {current_data}")
    assert current_data["active_exam_id"] is None
    assert current_data["expected_input_type"] == "none"

    print("\n4. Testing read_scan_status with missing file (should recreate):")
    if os.path.exists(SCAN_STATUS_FILE_PATH):
        os.remove(SCAN_STATUS_FILE_PATH)
    current_data = read_scan_status()
    print(f"Read data after delete & read: {current_data}")
    assert current_data["active_exam_id"] is None
    assert os.path.exists(SCAN_STATUS_FILE_PATH)

    print("\nTest complete.")
