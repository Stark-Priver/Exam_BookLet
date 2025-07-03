from flask import render_template, redirect, url_for
from flask_login import current_user
from app.main import bp

@bp.route('/')
@bp.route('/index')
def index():
    if current_user.is_authenticated and hasattr(current_user, 'username'): # Check if it's an AdminUser
        return redirect(url_for('admin.dashboard'))
    # For now, non-admin users or anonymous users can see a simple page or be redirected to login/scan page.
    # Later, this could redirect to a student scan page if we differentiate user types more.
    return render_template('main/index.html', title='Welcome')

# Placeholder for the scan UI route, to be developed in a later step
@bp.route('/scan')
def scan_ui():
    # This will eventually be the interface for barcode scanning
    return render_template('main/scan_interface.html', title='Scan Booklets')
