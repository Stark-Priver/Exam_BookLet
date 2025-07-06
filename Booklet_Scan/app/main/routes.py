from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import current_user, login_required
from app import db
from app.main import bp
from app.main.forms import ScanForm
from app.models import Exam, Student, ScanRecord, StudentExamAssignment
from app.utils import lcd_display # Import the LCD utility
from wtforms.validators import DataRequired ,Optional


@bp.route('/')
@bp.route('/index')
def index():
    if current_user.is_authenticated and hasattr(current_user, 'username'): # Check if it's an AdminUser
        return redirect(url_for('admin.dashboard'))
    # Redirect non-logged-in users to login, or scan page if they are logged in but not admin
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    return redirect(url_for('main.scan_ui'))


@bp.route('/scan', methods=['GET', 'POST'])
@login_required
def scan_ui():
    form = ScanForm()
    scan_step = request.args.get('scan_step', 'check_student') # Manage UI state
    verified_student_info = request.args.get('student_info', None) # JSON string or similar

    # Initialize LCD if not already active
    if not lcd_display.is_lcd_active(): # Use the new getter function
        lcd_display.init_lcd()

    if not form.exam_id.choices:
        flash("No exams available. Please add exams in Admin Panel.", "warning")
        lcd_display.display_message("Error:", "No Exams Setup", delay_after=3)

    if request.method == 'POST':
        if form.submit_check_student.data:
            scan_step = 'check_student' # Ensure we process this step
            # Temporarily make booklet_code optional for this step's validation
            form.booklet_code.validators = [v for v in form.booklet_code.validators if not isinstance(v, DataRequired)]

            if form.validate_on_submit(): # Validates exam_id and student_identifier
                exam_id = form.exam_id.data
                student_identifier = form.student_identifier.data
                exam = Exam.query.get(exam_id)
                student = Student.query.filter_by(student_id=student_identifier).first()

                if not exam:
                    flash('Selected exam not found.', 'danger')
                    lcd_display.display_message("Error:", "Exam Not Found", delay_after=3)
                elif not student:
                    flash(f'Student ID "{student_identifier}" not found.', 'danger')
                    lcd_display.display_message(f"Stud ID:{student_identifier[:8]}", "Not Found", delay_after=3)
                else:
                    assignment = StudentExamAssignment.query.filter_by(student_id=student.id, exam_id=exam.id).first()
                    if not assignment:
                        flash(f'Student {student.name} ({student.student_id}) is NOT ELIGIBLE for exam {exam.name} (not assigned).', 'danger')
                        lcd_display.display_message(f"{student.name[:16]}", "NOT ELIGIBLE", delay_after=3)
                        # Stay in 'check_student' step, clear student_identifier for next attempt
                        form.student_identifier.data = ""
                    else:
                        # Student is eligible
                        flash(f'Student {student.name} ({student.student_id}) is ELIGIBLE for {exam.name}. Please scan booklet.', 'success')
                        lcd_display.display_message(f"{student.name[:16]}", "ELIGIBLE: Scan_BK", delay_after=2)
                        scan_step = 'scan_booklet'
                        # Pass student info to the next part of the form/view
                        # The form fields for exam and student will be pre-filled and possibly readonly
                        # The actual IDs will be used for booklet submission.
                        verified_student_info = {'id': student.id, 'name': student.name, 'student_id': student.student_id, 'exam_id': exam.id, 'exam_name': exam.name}
                        form.booklet_code.data = "" # Clear booklet code for input
                # Re-render with current form data, messages, and new scan_step/student_info
                return render_template('main/scan_interface.html', title='Scan Booklets', form=form, scan_step=scan_step, student_info=verified_student_info)
            else: # Validation failed for check_student step
                lcd_display.display_message("Error:", "Check Input", delay_after=3)


        elif form.submit_record_scan.data:
            scan_step = 'scan_booklet' # Ensure we process this step
            # Booklet code is now required
            form.booklet_code.validators.append(DataRequired(message="Booklet code cannot be empty."))

            # We need exam_id and student_id from the previous step.
            # These should be submitted, perhaps via hidden fields or by keeping form fields populated.
            # For simplicity, we assume exam_id is still selected correctly.
            # Student ID needs to be retrieved based on the verified student.
            # This part needs careful state management (e.g. session or hidden fields in form)
            # Let's assume student_info (from previous step) is somehow available or passed via hidden fields.
            # The 'verified_student_info' if passed via args would be a string, needs parsing, better use session or POSTed hidden fields.
            # For now, let's simplify and re-query student based on form.student_identifier.data if it's still there.
            # This is NOT ROBUST if student_identifier field was cleared or changed.
            # A hidden field for verified_student_id would be better.

            # For this example, assume form.exam_id.data and form.student_identifier.data are still valid from the previous step if they were made readonly.
            # A more robust way: use hidden fields populated after student check.
            # For now, let's assume they are still in the form correctly.

            if form.validate_on_submit(): # Validates all fields including booklet_code now
                exam_id = form.exam_id.data
                student_identifier = form.student_identifier.data # This might be problematic if user changes it.
                booklet_code = form.booklet_code.data

                exam = Exam.query.get(exam_id)
                student = Student.query.filter_by(student_id=student_identifier).first()

                if not exam or not student: # Should have been caught in step 1, but re-check
                    flash('Error: Exam or Student details lost. Please restart scan.', 'danger')
                    lcd_display.display_message("Error:", "State Lost", delay_after=3)
                    return redirect(url_for('main.scan_ui')) # Reset

                # Re-verify assignment as a safeguard, though student was deemed eligible
                assignment = StudentExamAssignment.query.filter_by(student_id=student.id, exam_id=exam.id).first()
                if not assignment:
                    flash(f'Error: Student {student.name} no longer eligible. Please restart scan.', 'danger')
                    lcd_display.display_message(f"{student.name[:16]}", "ERR:ELIGIBILITY", delay_after=3)
                    return redirect(url_for('main.scan_ui'))


                existing_scan = ScanRecord.query.filter_by(exam_id=exam.id, booklet_code=booklet_code).first()
                if existing_scan:
                    flash(f'Booklet "{booklet_code}" already scanned for this exam (Student: {existing_scan.student.name}).', 'warning')
                    lcd_display.display_message(f"BK:{booklet_code[:10]}", "WARN:DUPLICATE", delay_after=3)
                    # Keep in scan_booklet state to allow re-entry of booklet code
                    verified_student_info = {'id': student.id, 'name': student.name, 'student_id': student.student_id, 'exam_id': exam.id, 'exam_name': exam.name}
                    form.booklet_code.data = ""
                    return render_template('main/scan_interface.html', title='Scan Booklets', form=form, scan_step='scan_booklet', student_info=verified_student_info)

                try:
                    scan_record = ScanRecord(student_id=student.id, exam_id=exam.id, booklet_code=booklet_code)
                    db.session.add(scan_record)
                    db.session.commit()
                    flash(f'Booklet "{booklet_code}" recorded for {student.name} ({exam.name}).', 'success')
                    lcd_display.display_message(f"BK:{booklet_code[:10]} OK", f"{student.name[:16]}", delay_after=3)

                    # Reset for next student scan
                    return redirect(url_for('main.scan_ui', scan_step='check_student', last_exam_id=exam_id))
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f"Error saving scan: {e}")
                    flash('Error saving scan record.', 'danger')
                    lcd_display.display_message("Error:", "Save Failed", delay_after=3)
                    # Stay in scan_booklet step for retry
                    verified_student_info = {'id': student.id, 'name': student.name, 'student_id': student.student_id, 'exam_id': exam.id, 'exam_name': exam.name}
                    return render_template('main/scan_interface.html', title='Scan Booklets', form=form, scan_step='scan_booklet', student_info=verified_student_info)
            else: # Validation failed for record_scan step
                 lcd_display.display_message("Error:", "Check Booklet", delay_after=3)
                 # Need to ensure student_info is passed back if validation fails at booklet stage
                 # This part is tricky because student_info might not be in form object.
                 # A GET param or session would be more robust for student_info persistence here.
                 # For now, if validation fails, it might lose student_info context for re-render.
                 # This needs to be handled by ensuring student_info is correctly repopulated for the template.
                 # A quick fix could be to re-query student if student_identifier is still in form.
                 if form.student_identifier.data:
                     student = Student.query.filter_by(student_id=form.student_identifier.data).first()
                     if student:
                        verified_student_info = {'id': student.id, 'name': student.name, 'student_id': student.student_id, 'exam_id': form.exam_id.data, 'exam_name': Exam.query.get(form.exam_id.data).name if form.exam_id.data else ""}
                 return render_template('main/scan_interface.html', title='Scan Booklets', form=form, scan_step='scan_booklet', student_info=verified_student_info)


    # Initial GET request or after a full redirect
    # Reset booklet_code validators if it was changed for check_student step
    form.booklet_code.validators = [v for v in form.booklet_code.validators if not isinstance(v, DataRequired)]
    form.booklet_code.validators.append(Optional()) # Ensure it's Optional for initial GET

    return render_template('main/scan_interface.html', title='Scan Booklets', form=form, scan_step=scan_step, student_info=verified_student_info)
