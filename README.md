# Exam Booklet Scanning System (BookletScan Pro)

## Project Overview

BookletScan Pro is a Flask-based web application designed to streamline the management and scanning of exam booklets. It provides administrators with tools to manage students, examination venues, and exam schedules, and assign students to specific exams. The core functionality includes a scanning interface for recording exam booklet codes against students for selected exams, supporting both manual input and USB barcode scanner integration.

The system aims to improve efficiency and accuracy in tracking exam booklet submissions.

## Features

*   **Admin Authentication:**
    *   Secure login/logout for administrators.
    *   Admin self-registration.
*   **Data Management (Admin Panel):**
    *   **Students:** Create, Read, Update, Delete (CRUD) student records (Name, Student ID, Course).
    *   **Venues:** CRUD operations for examination venues (Name, Location, Capacity).
    *   **Exams:** CRUD operations for exams (Name, Course, Venue, Date, Start/End Times).
    *   **Student-Exam Assignments:** Assign students to specific exams and manage these assignments.
*   **Booklet Scanning & On-Demand Printing (New):**
    *   User-friendly interface to select an active exam and input student identifier.
    *   **Automatic Booklet Generation & Printing:** If a student is confirmed eligible for the selected exam:
        *   A new PDF booklet with a unique barcode is generated.
        *   The generated PDF is automatically sent to a connected printer (requires printer setup on the Raspberry Pi).
        *   The new booklet's barcode is recorded against the student for the exam.
    *   Validation:
        *   Checks for valid student ID and eligibility for the exam.
        *   Prevents duplicate booklet code recordings for the same exam.
    *   Real-time feedback on eligibility, PDF generation, printing status, and recording success/failure, shown on both the web UI and I2C LCD (if connected).
*   **Modern User Interface:**
    *   Clean, responsive design using the "Minty" Bootswatch theme.
    *   Card-based layouts for dashboards and forms.
    *   Improved table styling and user action buttons with icons.

## Technology Stack

*   **Backend:** Python, Flask
    *   **Flask-SQLAlchemy:** Database ORM
    *   **Flask-Login:** User session management (for admins)
    *   **Flask-WTF:** Forms creation and validation
    *   **Werkzeug:** Password hashing and utility functions
*   **Frontend:**
    *   HTML5, CSS3
    *   **Bootstrap 4 (via Bootswatch "Minty" theme):** Responsive design and UI components
    *   JavaScript (minimal, for UI enhancements like feedback on scan page)
*   **Database:** SQLite (default, configurable in `config.py`)

## Setup and Installation

1.  **Prerequisites:**
    *   Python 3.8+
    *   `pip` (Python package installer)
    *   Git (for cloning the repository)

2.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd Booklet_Scan 
    ```
    *(Replace `<repository_url>` with the actual URL of your Git repository)*

3.  **Create and Activate a Virtual Environment:**
    *   **Windows:**
        ```bash
        python -m venv venv
        venv\Scripts\activate
        ```
    *   **macOS/Linux:**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Database Initialization:**
    The application uses Flask-SQLAlchemy. The database (`app.db` by default, located in the `Booklet_Scan` directory) will be created automatically if it doesn't exist when the application first tries to access it. 
    
    To initialize it manually (e.g., after cloning or if you've deleted `app.db`):
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
    *   **(Note:** For more complex database schema changes in a production environment, consider integrating `Flask-Migrate`.)*

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

## Running the Application

1.  Ensure your virtual environment is activated from the `Booklet_Scan` directory.
2.  Run the Flask development server using the `run.py` script:
    ```bash
    python run.py
    ```
3.  The application will typically be available at `http://127.0.0.1:5000/`.

## Usage

1.  **Admin Registration/Login:**
    *   Navigate to the application URL (e.g., `http://127.0.0.1:5000/`). You should be redirected to the login page.
    *   If you are a new admin and haven't created an account via `flask shell`, click the "New User? Click to Register!" link on the login page and create an account.
    *   Log in with your admin credentials.

2.  **Admin Dashboard:**
    *   After successful login, you'll be directed to the Admin Dashboard.
    *   This dashboard provides quick links to manage Students, Venues, Exams, and Student-Exam Assignments.

3.  **Managing Entities (Students, Venues, Exams, Assignments):**
    *   Click on the respective "Manage" button on the dashboard (e.g., "Manage Students").
    *   Each management section provides a list view of existing records.
    *   You can add new entities using the "Add New..." button.
    *   Edit existing records using the "Edit" button next to each entry.
    *   Delete records using the "Delete" button (a confirmation will be required).

4.  **Booklet Scanning Interface:**
    *   Access the scanning interface via the "Scan Booklets" link in the top navigation bar or the large green button on the Admin Dashboard.
    *   **Select the Exam:** Choose the current exam from the "Select Exam" dropdown list.
    *   **Enter Student ID:** Type the Student's ID or scan it if it's barcoded/QR coded and press Enter or click "Check Student & Print Booklet".
    *   **Automatic Processing:** If the student is eligible:
        *   The system will automatically generate a new booklet PDF with a unique barcode.
        *   This PDF will be sent to the configured printer.
        *   The booklet's information (barcode, student, exam) will be recorded in the database.
    *   **Feedback:** The system provides immediate feedback on the web page and on the LCD (if connected) regarding:
        *   Student eligibility.
        *   Booklet generation status.
        *   Printing status (success/failure).
        *   Record saving status.
    *   After successful printing and recording, the interface will reset for the next student, typically keeping the selected exam.

## Future Considerations/Improvements

*   **Flask-Migrate:** Implement database migrations for robust schema updates, especially in production.
*   **Advanced Scan Record Viewing/Reporting:** Create a dedicated page for administrators to view, filter, search, and possibly export scan records (e.g., as CSV).
*   **Student-Specific View:** Potentially a view for students to check their registered exams or confirm their scan status (this would require implementing student authentication and user roles beyond just admins).
*   **Enhanced Barcode Logic/Parsing:** If booklet codes or student IDs are embedded within a single more complex barcode, add parsing logic to extract the necessary information.
*   **API Endpoints:** Develop API endpoints for programmatic interaction, e.g., bulk data import or integration with other institutional systems.
*   **Comprehensive Testing:** Expand unit and integration tests to ensure reliability.
*   **Configuration for Production:** Detail steps for deploying to a production environment (e.g., using Gunicorn/Waitress, different database).

## Raspberry Pi Deployment with I2C LCD

This application can be run on a Raspberry Pi with an I2C LCD display to show scan status.

### Hardware Setup:

1.  **I2C LCD Display:** A standard I2C LCD, typically 16x2 or 20x4 characters, often using a PCF8574 I2C backpack.
2.  **Wiring:**
    *   **SDA (Serial Data):** Connect to Raspberry Pi GPIO2 (Pin 3).
    *   **SCL (Serial Clock):** Connect to Raspberry Pi GPIO3 (Pin 5).
    *   **VCC:** Connect to Raspberry Pi 5V (Pin 2 or 4).
    *   **GND:** Connect to Raspberry Pi Ground (Pin 6, 9, 14, 20, 25, 30, 34, or 39).
    *   *Always double-check your Raspberry Pi pinout and LCD datasheet.*

### Raspberry Pi Software Configuration:

1.  **Operating System:**
    *   Install Raspberry Pi OS (formerly Raspbian), either Lite (headless) or Desktop version. Flash it to an SD card.

2.  **Initial Setup:**
    *   Boot the Raspberry Pi and perform initial setup (locale, keyboard, network).
    *   Ensure your Pi is connected to the internet.

3.  **Enable I2C Interface:**
    *   Open a terminal on the Raspberry Pi.
    *   Run `sudo raspi-config`.
    *   Navigate to `Interface Options` (or `Interfacing Options`).
    *   Select `I2C` and enable it.
    *   Reboot the Raspberry Pi if prompted.

4.  **Install System Dependencies:**
    *   Update package lists: `sudo apt update && sudo apt upgrade -y`
    *   Install necessary tools and libraries:
        ```bash
        sudo apt install -y python3-dev python3-pip i2c-tools libffi-dev git cups cups-client
        ```
        *   `i2c-tools`: Allows you to detect I2C devices.
        *   `libffi-dev`: May be needed for `cffi`, a dependency of `smbus-cffi`.
        *   `cups` & `cups-client`: Common UNIX Printing System, for managing printers.

5.  **Configure Printer (CUPS):**
    *   Ensure your printer is connected to the Raspberry Pi (USB or network) and powered on.
    *   Install printer drivers if necessary. Many printers are supported out-of-the-box or have drivers available through `apt`.
    *   Add the printer to CUPS:
        *   Open a web browser on a device connected to the same network as your Raspberry Pi and navigate to `http://<RaspberryPi_IP_Address>:631`. (You might need to enable remote access to CUPS first: `sudo cupsctl --remote-any` and `sudo /etc/init.d/cups restart` or `sudo systemctl restart cups`).
        *   Go to "Administration" -> "Add Printer". You may be prompted for a username/password (use your Pi's user credentials, e.g., `pi` and your password. The user `pi` might need to be added to the `lpadmin` group: `sudo usermod -a -G lpadmin pi`).
        *   Follow the on-screen instructions to add your printer. Note the printer's "Queue Name" as this will be its identifier.
    *   You can set the printer as the default printer in CUPS or specify its name in the application's configuration if needed (though the current script uses the default or a name passed to `print_pdf`).
    *   Test printing a test page from the CUPS interface to ensure it's working.

6.  **Verify I2C Connection:**
    *   With the LCD wired up and Pi powered on, run:
        ```bash
        sudo i2cdetect -y 1
        ```
        (Use `i2cdetect -y 0` if you have a very old Model B Rev 1 Pi).
    *   You should see a grid. The address of your LCD (e.g., `27` or `3F`) should appear. Note this address. The default in `app/utils/lcd_display.py` is `0x27`. If yours is different, you might need to adjust the `DEFAULT_I2C_ADDRESS` in that file or modify the `init_lcd` call.

### Application Setup on Raspberry Pi:

1.  **Clone the Repository:**
    ```bash
    git clone <your_repository_url>
    cd Booklet_Scan # Or your project's root directory
    ```

2.  **Create and Activate Virtual Environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Python Dependencies:**
    ```bash
    pip3 install -r requirements.txt
    ```
    This will install Flask, RPLCD, smbus-cffi, and other necessary packages.

4.  **Database Setup:**
    *   Follow the database initialization steps outlined in the main "Setup and Installation" section (using `flask shell` and `db.create_all()`).

5.  **Run the Application for Network Access:**
    *   To make the Flask app accessible from other devices on your network, run it on host `0.0.0.0`:
        ```bash
        python3 run.py
        ```
        (Ensure `run.py` is configured to run on `host='0.0.0.0'`, or use `flask run --host=0.0.0.0`).
    *   The application will be available at `http://<RaspberryPi_IP_Address>:5000`. Find your Pi's IP address using `hostname -I`.

### LCD Functionality:

*   The `app/utils/lcd_display.py` module handles LCD interaction.
*   It attempts to initialize the LCD when the scan page (`/scan`) is first accessed or when a message needs to be displayed.
*   If the LCD is not detected or an error occurs, messages will be printed to the console/Flask log instead, and the web application will continue to function.
*   The scan route (`app/main/routes.py`) will send status messages to the LCD:
    *   "System Ready" on initialization.
    *   "Error: No Exams Setup" if no exams are configured.
    *   Eligibility status (e.g., "Student Eligible", "Not Eligible").
    *   Booklet generation status (e.g., "Generating PDF...", "PDF Gen Failed").
    *   Printing status (e.g., "Printing...", "Print Failed", "Printed OK").
    *   Recording status (e.g., "Saving...", "Save Failed", "Saved OK").
    *   Error messages like "Student Not Found", "Exam Not Found".
```
