from app import create_app, db
from app import create_app, db
# Import models here to ensure they are known to SQLAlchemy before creating tables
from app.models import AdminUser, Student, Exam, Venue, StudentExamAssignment, ScanRecord

app = create_app()

@app.shell_context_processor
def make_shell_context():
    """
    Allows you to work with database and models in Flask shell without explicit imports.
    Run `flask shell` in the terminal.
    """
    # Add your models to the shell context for easy access
    return {
        'db': db,
        'AdminUser': AdminUser, 'Student': Student, 'Exam': Exam,
        'Venue': Venue, 'StudentExamAssignment': StudentExamAssignment,
        'ScanRecord': ScanRecord
    }

if __name__ == '__main__':
    with app.app_context():
        # Create database tables if they don't exist
        db.create_all() # This will be moved to a proper migration setup later if needed
        # pass # Commented out pass as db.create_all() is now active
    # Make the app accessible on the network for Raspberry Pi deployment
    # Also attempt to initialize LCD at startup
    from app.utils import lcd_display # Import here to avoid circular if utils imports app components
    with app.app_context():
        print("Attempting to initialize LCD and display IP from run.py...")
        # init_lcd is called by display_ip_address if needed, or can be called explicitly first
        # if lcd_display.init_lcd():
        #    lcd_display.display_ip_address()
        # else:
        #    print("LCD could not be initialized from run.py. IP will not be displayed on LCD.")
        # Simpler: display_ip_address will attempt init if LCD is not active.
        lcd_display.display_ip_address()


    app.run(debug=True, host='0.0.0.0', port=5000)
