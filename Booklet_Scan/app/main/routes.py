from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import current_user, login_required
from app import db
from app.main import bp
from app.main.forms import ScanForm
from app.models import Exam, Student, ScanRecord, StudentExamAssignment
from app.utils import lcd_display # Import the LCD utility
from app.utils.booklet_generator import generate_single_booklet
from app.utils.printer_utils import print_pdf
from wtforms.validators import DataRequired ,Optional
import datetime
import os # For joining paths for booklet output


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
                    # No change in scan_step or verified_student_info, stay on check_student
                else:
                    assignment = StudentExamAssignment.query.filter_by(student_id=student.id, exam_id=exam.id).first()
                    if not assignment:
                        flash(f'Student {student.name} ({student.student_id}) is NOT ELIGIBLE for exam {exam.name} (not assigned).', 'danger')
                        lcd_display.display_message(f"{student.name[:16]}", "NOT ELIGIBLE", delay_after=3)
                        form.student_identifier.data = "" # Clear student ID for next attempt
                        # No change in scan_step or verified_student_info, stay on check_student
                    else:
                        # Student is eligible - Proceed to generate, print, and record booklet
                        flash(f'Student {student.name} ({student.student_id}) is ELIGIBLE for {exam.name}. Printing booklet...', 'info')
                        lcd_display.display_message(f"{student.name[:8]} ELIGIBLE", "Printing...", delay_after=1)

                        # 1. Generate unique ID for the booklet
                        # Using a combination of student ID, exam ID, and timestamp for uniqueness
                        timestamp_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
                        unique_booklet_id = f"S{student.id}E{exam.id}T{timestamp_str}"

                        # Define output directory for booklets relative to app instance path or a configured static path
                        # For simplicity, using 'output_barcodes' in the instance path or project root.
                        # Using os.path.join(current_app.instance_path, 'printed_booklets') might be better for instance-specific files.
                        # For now, using the existing 'output_barcodes' at project root.
                        booklet_output_dir = os.path.join(current_app.root_path, '..', 'output_barcodes')
                        # Ensure this path is correct relative to where `run.py` is.
                        # If run.py is in Booklet_Scan, then `current_app.root_path` is `Booklet_Scan/app`.
                        # So `../output_barcodes` would be `Booklet_Scan/output_barcodes`.
                        # This matches the structure of `booklet_generator.py`'s default.

                        # 2. Generate the booklet PDF
                        pdf_file_path, barcode_value = generate_single_booklet(
                            unique_id=unique_booklet_id,
                            output_folder=booklet_output_dir, # Make sure this path is writable
                            student_name=student.name,
                            exam_name=exam.name
                        )

                        if not pdf_file_path or not barcode_value:
                            flash('Failed to generate booklet PDF.', 'danger')
                            lcd_display.display_message("Error:", "PDF Gen Failed", delay_after=3)
                            # Stay in 'check_student' step, allow retry
                            form.student_identifier.data = "" # Clear student for next attempt
                            return render_template('main/scan_interface.html', title='Scan Booklets', form=form, scan_step='check_student', student_info=None)

                        # 3. Print the PDF
                        # Consider adding printer name from config: current_app.config.get('PRINTER_NAME')
                        print_success = print_pdf(pdf_file_path, printer_name=current_app.config.get('DEFAULT_PRINTER_NAME'))

                        if not print_success:
                            flash(f'Booklet generated ({barcode_value}) but FAILED to print. Please check printer. Record not saved.', 'warning')
                            lcd_display.display_message(f"BK:{barcode_value[:7]} GenOK", "PRINT FAILED", delay_after=3)
                            # Stay in 'check_student' step, allow retry for the student (perhaps after fixing printer)
                            # Or, decide if we should record it anyway. For now, we don't.
                            form.student_identifier.data = student_identifier # Keep student ID for retry
                            return render_template('main/scan_interface.html', title='Scan Booklets', form=form, scan_step='check_student', student_info=None)

                        flash(f'Booklet {barcode_value} printed successfully for {student.name}. Recording...', 'success')
                        lcd_display.display_message(f"BK:{barcode_value[:7]} OK", f"{student.name[:8]} Printed", delay_after=2)

                        # 4. Record the scan
                        # Check for duplicates before saving (though unique ID should prevent this if barcode is unique)
                        existing_scan = ScanRecord.query.filter_by(exam_id=exam.id, booklet_code=barcode_value).first()
                        if existing_scan:
                            # This case should be rare if unique_id generation is robust
                            flash(f'Error: Booklet "{barcode_value}" already exists for this exam. Printing aborted.', 'danger')
                            lcd_display.display_message(f"ERR:BK DUPLICATE", f"{barcode_value[:10]}", delay_after=3)
                            # Reset for next student scan
                            return redirect(url_for('main.scan_ui', scan_step='check_student', last_exam_id=exam_id))

                        try:
                            scan_record = ScanRecord(student_id=student.id, exam_id=exam.id, booklet_code=barcode_value)
                            db.session.add(scan_record)
                            db.session.commit()
                            flash(f'Booklet "{barcode_value}" recorded for {student.name} ({exam.name}).', 'success')
                            lcd_display.display_message(f"BK:{barcode_value[:7]} Saved", f"{student.name[:8]} Done", delay_after=3)

                            # Reset for next student scan, pass last exam_id to pre-select it
                            return redirect(url_for('main.scan_ui', scan_step='check_student', last_exam_id=exam_id))
                        except Exception as e:
                            db.session.rollback()
                            current_app.logger.error(f"Error saving scan record after printing: {e}")
                            flash(f'Booklet "{barcode_value}" printed, but failed to save record. Please record manually.', 'danger')
                            lcd_display.display_message("Error:", "Save Failed", delay_after=3)
                            # Reset for next student scan
                            return redirect(url_for('main.scan_ui', scan_step='check_student', last_exam_id=exam_id))

                # If any of the above conditions (no exam, no student, not eligible) led to an error message,
                # we re-render the template.
                # The successful print-and-record path redirects.
                return render_template('main/scan_interface.html', title='Scan Booklets', form=form, scan_step='check_student', student_info=None)
            else: # Validation failed for check_student step (e.g. exam_id not provided)
                lcd_display.display_message("Error:", "Check Input", delay_after=3)
                # scan_step remains 'check_student', verified_student_info is None


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
