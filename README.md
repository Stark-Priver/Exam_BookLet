# Exam Booklet Scanning System (BookletScan Pro)

## Project Overview

BookletScan Pro is a Flask-based web application designed to streamline the management and scanning of exam booklets. It's optimized for use with a Raspberry Pi running in headless mode, using a directly connected USB barcode scanner and an I2C LCD for local feedback. Administrators can manage the system via a web dashboard accessible over the network.

The system aims to improve efficiency and accuracy in tracking exam booklet submissions by providing immediate local feedback on the Pi's LCD and centralized data management.

## Features

*   **Admin Authentication:**
    *   Secure login/logout for administrators.
    *   Admin self-registration.
*   **Data Management (Admin Panel):**
    *   CRUD operations for Students, Venues, Exams, Courses, and Student-Exam Assignments.
*   **Headless Booklet Scanning (Raspberry Pi):**
    *   Utilizes a background Python script (`scanner_listener.py`) on the Raspberry Pi to read directly from a connected USB barcode scanner (using `evdev`).
    *   Scanned data is sent to an internal API in the Flask application.
    *   The Flask app processes the scan (student validation, booklet recording) and provides real-time feedback on an I2C LCD display connected to the Pi.
    *   Admins control the start/stop of scanning sessions for exams via the web dashboard.
    *   The web interface's `/scan` page acts as a status display for remote monitoring.
*   **I2C LCD Display Integration:**
    *   Shows Pi's IP address on startup.
    *   Displays active exam information and instructions when a scanning session is started by an admin.
    *   Provides immediate local feedback for each scan (student eligibility, success/error messages).
*   **Modern User Interface:**
    *   Clean, responsive design using the "Minty" Bootswatch theme for the web dashboard.

## Technology Stack

*   **Backend:** Python, Flask
    *   **Flask-SQLAlchemy:** Database ORM
    *   **Flask-Login:** User session management (for admins)
    *   **Flask-WTF:** Forms creation and validation
    *   **Werkzeug:** Password hashing and utility functions
    *   **evdev:** For direct barcode scanner input on Linux/Raspberry Pi (headless mode).
    *   **requests:** Used by the scanner listener script to communicate with the Flask API.
*   **Frontend (Admin Web Dashboard):**
    *   HTML5, CSS3
    *   **Bootstrap 4 (via Bootswatch "Minty" theme):** Responsive design and UI components
    *   JavaScript (minimal, for UI enhancements)
*   **Hardware (Raspberry Pi):**
    *   I2C LCD Display (e.g., 16x2)
    *   USB Barcode Scanner (HID keyboard emulation type)
*   **Database:** SQLite (default, configurable in `config.py`)

## Setup and Installation

1.  **Prerequisites:**
    *   Python 3.8+
    *   `pip` (Python package installer)
    *   Git (for cloning the repository)
    *   **(For Raspberry Pi deployment with scanner):** System libraries for `evdev`. On Debian-based systems (like Raspberry Pi OS):
        ```bash
        sudo apt update
        sudo apt install python3-dev libudev-dev pkg-config
        # It's also often good to install python3-evdev via apt if available,
        # or pip will compile it using the headers above.
        # sudo apt install python3-evdev
        ```

2.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd Booklet_Scan 
    ```
    *(Replace `<repository_url>` with the actual URL of your Git repository)*

3.  **Create and Activate a Virtual Environment:**
    *   **Windows (for development of web panel only, not for Pi scanner listener):**
        ```bash
        python -m venv venv
        venv\Scripts\activate
        ```
    *   **macOS/Linux (and Raspberry Pi):**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

4.  **Install Dependencies:**
    *   Ensure virtual environment is active.
    *   Install Python packages:
        ```bash
        pip install -r requirements.txt
        ```

5.  **Database Initialization:**
    The application uses Flask-SQLAlchemy. The database (`app.db` by default, located in the `Booklet_Scan` directory) will be created automatically if it doesn't exist when the application first tries to access it. 
    The `scan_status.json` file (used for headless scanning coordination) will also be created/initialized automatically in the `Booklet_Scan` directory upon first admin access or when the scanner listener script starts.
    
    To initialize the database manually (e.g., after cloning or if you've deleted `app.db`):
    *   Ensure your virtual environment is activated.
    *   Open a Python REPL in your project's root directory (`Booklet_Scan`):
        ```bash
        flask shell
        ```
    *   Then, in the Flask shell, run:
        ```python
        from app import db
        db.create_all()
        print("Database tables created.")
        exit()
        ```
    *   **Important for schema changes (like adding `exam_status`):** `db.create_all()` will NOT modify existing tables. If you are updating an existing deployment and have modified models, you will need to either use a migration tool (like Flask-Migrate, not currently integrated) or manually alter your database schema (e.g., `ALTER TABLE exam ADD COLUMN exam_status VARCHAR(30) DEFAULT 'Pending' NOT NULL;`). For development, deleting `app.db` will allow it to be recreated with the new schema.

6.  **Create an Initial Admin User (Optional if using self-registration):**
    If you want to create an admin user programmatically before the first run (or if you prefer not to use the self-registration form initially):
    *   In the `flask shell`:
        ```python
        from app import db
        from app.models import AdminUser
        # Replace 'your_admin_username' and 'your_strong_password' with your desired credentials
        username = 'your_admin_username'
        password = 'your_strong_password'
        
        if AdminUser.query.filter_by(username=username).first():
            print(f"Admin user {username} already exists.")
        else:
            u = AdminUser(username=username)
            u.set_password(password)
            db.session.add(u)
            db.session.commit()
            print(f"Admin user {username} created successfully.")
        exit()
        ```

## Running the Application (Flask Web Server on Raspberry Pi)

1.  Ensure your virtual environment is activated from the `Booklet_Scan` directory on the Raspberry Pi.
2.  Run the Flask development server using the `run.py` script:
    ```bash
    python3 run.py
    ```
3.  The application will typically be available at `http://<your_pi_ip_address>:5000/` for access from other devices on the network, or `http://127.0.0.1:5000/` from the Pi itself.

## Headless Raspberry Pi Scanning Setup

This system is designed for a Raspberry Pi to handle barcode scanning directly via a connected USB scanner and display feedback on an I2C LCD, even without a monitor connected to the Pi (headless mode). The Flask web application runs on the Pi, and administrators can control and monitor the scanning process via a web browser on a separate computer on the same network.

### Core Components for Headless Scanning:

1.  **Flask Web Application (`run.py`):**
    *   Runs on the Raspberry Pi.
    *   Serves the admin web dashboard and an internal API.
    *   Controls the I2C LCD display.
    *   Manages the overall state of scanning (active exam, expected input type) via `scan_status.json`.
2.  **Scanner Listener Script (`scanner_listener.py`):**
    *   A separate Python script that runs in the background on the Raspberry Pi.
    *   Directly reads input from the USB barcode scanner using the `evdev` library.
    *   Communicates with the Flask application by POSTing scanned data to an internal API endpoint (`/api/v1/internal_scan`).
    *   Reads `scan_status.json` to know the current context (active exam, student vs. booklet scan).
3.  **I2C LCD Display:**
    *   Connected to the Raspberry Pi.
    *   Provides immediate local feedback for scans (e.g., student eligibility, scan success/failure), IP address, and active exam status.
4.  **`scan_status.json` file:**
    *   Located in the `Booklet_Scan` project root.
    *   Stores the current state of the scanning process (e.g., `active_exam_id`, `expected_input_type`).
    *   Used to coordinate between the Flask app (controlled by admin via web) and `scanner_listener.py`.

### Hardware Setup:

*   **Raspberry Pi:** With Raspberry Pi OS, network connectivity.
*   **I2C LCD Display:** Wired as per standard I2C LCD setup (SDA, SCL, VCC, GND - typically GPIO2 for SDA, GPIO3 for SCL).
*   **USB Barcode Scanner:** Connected to a USB port on the Raspberry Pi. Assumed to operate as a standard HID keyboard device.

### Software and Configuration Steps on Raspberry Pi:

1.  **Clone Repository & Install Dependencies:**
    *   Follow main "Setup and Installation" steps 1-4. This includes installing system dependencies like `python3-dev`, `libudev-dev` (for `evdev`) and then `pip install -r requirements.txt`.

2.  **Enable I2C Interface:**
    *   Done via `sudo raspi-config` (Interface Options > I2C > Enable). Verify with `sudo i2cdetect -y 1` (or `0` for old Pi models).

3.  **Configure `scanner_listener.py`:**
    *   Open `Booklet_Scan/scanner_listener.py` in an editor.
    *   **Identify Scanner Device Path:** You need to find the event device path for your USB barcode scanner.
        *   Connect your scanner.
        *   Try running `sudo libinput list-devices`. Look for your scanner. Note its `/dev/input/eventX` path.
        *   Alternatively, check `/dev/input/by-id/`. Often USB HID devices have descriptive names here (e.g., `usb-SYMBEYE_Barcode_Scanner_...-event-kbd`). Using a path from `/dev/input/by-id/` is more stable across reboots than `/dev/input/eventX`.
    *   **Update `SCANNER_DEVICE_PATH`:** In `scanner_listener.py`, change the line:
        ```python
        SCANNER_DEVICE_PATH = None
        ```
        to your scanner's actual path, e.g.:
        ```python
        SCANNER_DEVICE_PATH = "/dev/input/by-id/usb-Your_Scanner_Name-event-kbd"
        # or SCANNER_DEVICE_PATH = "/dev/input/event3"
        ```
    *   Review `KEYCODE_MAP` in the script if your scanner outputs non-standard characters or keycodes, or doesn't automatically send an 'Enter' keystroke.

4.  **Test `scanner_listener.py` (Optional but Recommended):**
    *   You can try running it directly first to see if it detects your scanner and reads barcodes.
    *   You might need to run it with `sudo` due to permissions for `/dev/input/` devices:
        ```bash
        cd Booklet_Scan
        sudo python3 scanner_listener.py
        ```
    *   Scan some barcodes. It will attempt to POST to the Flask API (which might not be running yet for this test, so expect connection errors in the listener log, but it should log the scanned string). Press Ctrl+C to stop.

5.  **Set Up `scanner_listener.py` to Run as a Background Service (using `systemd`):**
    *   Create a service file, e.g., `/etc/systemd/system/scanner_listener.service`:
        ```ini
        [Unit]
        Description=Booklet Scan Scanner Listener Service
        After=network.target multi-user.target # Ensure network is up, and Flask app service if separate

        [Service]
        ExecStart=/home/pi/Exam_BookLet/Booklet_Scan/venv/bin/python3 /home/pi/Exam_BookLet/Booklet_Scan/scanner_listener.py
        WorkingDirectory=/home/pi/Exam_BookLet/Booklet_Scan/
        StandardOutput=append:/var/log/scanner_listener.log # Log to a file
        StandardError=append:/var/log/scanner_listener.error.log # Log errors to a file
        Restart=always
        User=pi # Or the user you run the app as. Ensure this user has permissions for scanner device.
        # Environment="PYTHONUNBUFFERED=1" # Useful for immediate logging

        [Install]
        WantedBy=multi-user.target
        ```
        *   **Adjust paths** (`ExecStart`, `WorkingDirectory`) to match your project location and virtual environment.
        *   **Permissions for Scanner:** The `User=pi` might not have direct access to `/dev/input/eventX`. You have a few options:
            *   Run as `User=root` (simpler, but less secure).
            *   **Recommended:** Create a `udev` rule to grant your user (e.g., `pi`) access to the scanner device. Create a file like `/etc/udev/rules.d/99-scanner.rules`:
                ```
                SUBSYSTEM=="input", KERNEL=="event[0-9]*", ATTRS{name}=="*Your Scanner Device Name*", MODE="0660", GROUP="input", TAG+="uaccess"
                ```
                Replace `"Your Scanner Device Name"` (get from `libinput list-devices` or `cat /proc/bus/input/devices`). Ensure user `pi` is part of the `input` group (`sudo usermod -a -G input pi`). Then run `sudo udevadm control --reload-rules && sudo udevadm trigger`.
    *   Enable and start the service:
        ```bash
        sudo systemctl daemon-reload
        sudo systemctl enable scanner_listener.service
        sudo systemctl start scanner_listener.service
        ```
    *   Check its status: `sudo systemctl status scanner_listener.service`
        View logs: `journalctl -u scanner_listener.service -f` or check `/var/log/scanner_listener.log`.

6.  **Run the Flask Web Application:**
    *   This can also be run as a systemd service for robustness. Example `/etc/systemd/system/booklet_scan_web.service`:
        ```ini
        [Unit]
        Description=BookletScan Pro Flask Web Application
        After=network.target

        [Service]
        User=pi
        WorkingDirectory=/home/pi/Exam_BookLet/Booklet_Scan
        ExecStart=/home/pi/Exam_BookLet/Booklet_Scan/venv/bin/gunicorn --workers 2 --bind 0.0.0.0:5000 "run:app"
        Restart=always
        # StandardOutput=append:/var/log/booklet_scan_web.log
        # StandardError=append:/var/log/booklet_scan_web.error.log

        [Install]
        WantedBy=multi-user.target
        ```
        * Install Gunicorn: `pip install gunicorn` (add to `requirements.txt`).
        * Adjust paths and user. Then enable and start this service.
    *   Alternatively, for simpler setup, run manually in a `screen` or `tmux` session:
        ```bash
        cd Booklet_Scan
        source venv/bin/activate
        python3 run.py
        ```
    *   The Flask app will run on `http://<Your_Pi_IP>:5000`.

### Usage Workflow with Headless Setup:

1.  **Admin (Remote Web Browser):**
    *   Accesses `http://<Pi_IP_Address>:5000`.
    *   Logs in to the admin dashboard.
    *   Navigates to "Manage Exams".
    *   Clicks "Start Auth" for the desired exam.
        *   This updates `scan_status.json` on the Pi.
        *   The I2C LCD on the Pi updates to show exam info and "Scan Student ID".
        *   The `scanner_listener.py` script (reading `scan_status.json`) now knows an exam is active and what to expect.

2.  **Scanning (at the Pi, via USB Scanner):**
    *   The person at the Pi scans a **Student ID barcode**.
        *   `scanner_listener.py` captures it, sends it to the Flask API.
        *   Flask API processes it:
            *   If valid & eligible: LCD shows "OK: Scan Booklet". `scan_status.json` updated to expect "booklet" and stores verified student.
            *   If invalid/ineligible: LCD shows error/warning. `scan_status.json` might be updated to show student was checked but not proceed, or remain expecting "student".
    *   If student was eligible, the person at the Pi scans a **Booklet Code barcode**.
        *   `scanner_listener.py` captures it, sends it to Flask API.
        *   Flask API processes it:
            *   If valid: Scan recorded in DB. LCD shows success. `scan_status.json` updated to expect "student" again for next scan.
            *   If duplicate/error: LCD shows error/warning.

3.  **Monitoring (Remote Web Browser):**
    *   Admin can navigate to the `/scan` page (now a status display page) to see the current active exam and expected input type. This page includes a refresh button.
    *   Admin can view the "Scan Records" page to see a list of all successful scans.

4.  **Ending Scanning Session (Admin):**
    *   Admin clicks "Stop Auth" for the active exam on the "Manage Exams" page.
        *   Flask app updates `scan_status.json` (no active exam).
        *   LCD reverts to showing IP address.
        *   `scanner_listener.py` sees no active exam and idles.

## Original Usage (Manual/Browser-Based Scanning - Now Superseded by Headless Mode)
The previous method of scanning involved using the web browser's input fields on the `/scan` page. With the introduction of the headless `scanner_listener.py`, this direct browser input method for scanning is no longer the primary mechanism for Raspberry Pi deployments. The `/scan` page now serves as a status display.

## Future Considerations/Improvements
*   **Flask-Migrate:** Implement database migrations for robust schema updates.
*   **Real-time Web UI for `/scan`:** Use WebSockets or Server-Sent Events to update the `/scan` status page instantly when scans occur, instead of relying on refresh.
*   **More Robust Scanner Discovery in `scanner_listener.py`:** Improve heuristics or allow selection if multiple devices are found (e.g., via a config file).
*   **Configuration File:** Move settings like `SCANNER_DEVICE_PATH`, API endpoint, log paths, etc., from script constants to a dedicated configuration file (e.g., `config_listener.ini`).
*   **Advanced Scan Record Viewing/Reporting:** Enhance the "Scan Records" page with filtering, searching, and export options.
*   **Comprehensive Testing:** Expand unit and integration tests, especially for the new listener script and API interaction.

*(Old "Raspberry Pi Deployment with I2C LCD" subsections have been removed or integrated into the new "Headless Raspberry Pi Scanning Setup" section.)*
```
