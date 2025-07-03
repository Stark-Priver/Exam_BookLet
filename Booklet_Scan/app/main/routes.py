from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from app import db
from app.main import bp
from app.main.forms import ScanForm
from app.models import Exam, Student, ScanRecord, StudentExamAssignment

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
@login_required # Ensure user is logged in to access scanning
def scan_ui():
    form = ScanForm()

    # Check if exams are available and flash a message if not
    if not form.exam_id.choices:
        flash("No exams are currently available for scanning. Please add exams via the admin panel.", "warning")

    # Keep selected exam_id if form is re-rendered due to error or successful scan
    if request.method == 'GET' and request.args.get('last_exam_id'):
        try:
            # Ensure last_exam_id is a valid integer before assigning
            form.exam_id.data = int(request.args.get('last_exam_id'))
        except (ValueError, TypeError):
            pass # Ignore if last_exam_id is not a valid int

    if form.validate_on_submit():
        exam_id = form.exam_id.data
        booklet_code = form.booklet_code.data
        student_identifier = form.student_identifier.data # This is the Student.student_id

        exam = Exam.query.get(exam_id)
        if not exam:
            flash('Selected exam not found. Please select a valid exam.', 'danger')
            return redirect(url_for('main.scan_ui', last_exam_id=exam_id))

        # Find student by student_id (student_identifier from form)
        student = Student.query.filter_by(student_id=student_identifier).first()
        if not student:
            flash(f'Student with ID "{student_identifier}" not found.', 'danger')
            return redirect(url_for('main.scan_ui', last_exam_id=exam_id, booklet_code=booklet_code, student_identifier=student_identifier))

        # Optional: Check if student is assigned to this exam
        assignment = StudentExamAssignment.query.filter_by(student_id=student.id, exam_id=exam.id).first()
        if not assignment:
            flash(f'Student {student.name} ({student.student_id}) is not assigned to the exam: {exam.name}.', 'warning')
            # Depending on policy, you might still allow the scan or prevent it.
            # For now, we'll flash a warning but still allow the scan.
            # If strict assignment is required, uncomment the line below and adjust logic:
            # return redirect(url_for('main.scan_ui', last_exam_id=exam_id, booklet_code=booklet_code, student_identifier=student_identifier))


        # Check for duplicate booklet code for this exam
        existing_scan = ScanRecord.query.filter_by(exam_id=exam.id, booklet_code=booklet_code).first()
        if existing_scan:
            flash(f'Booklet code "{booklet_code}" has already been scanned for exam "{exam.name}" for student {existing_scan.student.name} ({existing_scan.student.student_id}).', 'warning')
            return redirect(url_for('main.scan_ui', last_exam_id=exam_id, booklet_code=booklet_code, student_identifier=student_identifier))

        try:
            scan_record = ScanRecord(student_id=student.id, exam_id=exam.id, booklet_code=booklet_code)
            db.session.add(scan_record)
            db.session.commit()

            # Prepare data for "Last Scan Details"
            last_scan_data = {
                'student_name': student.name,
                'student_id': student.student_id,
                'exam_name': f"{exam.name} ({exam.course})",
                'booklet_code': scan_record.booklet_code,
                'timestamp': scan_record.timestamp.isoformat()
            }
            flash(f'Successfully scanned booklet "{booklet_code}" for student {student.name} ({student.student_id}) for exam "{exam.name}".', 'success')

            # Use session to pass last scan data to the template after redirect
            # Or pass as query parameters if preferred and not too much data
            return render_template('main/scan_interface.html', title='Scan Booklets', form=form, last_scan_data=last_scan_data)

        except Exception as e:
            db.session.rollback()
            flash(f'Error saving scan record: {str(e)}', 'danger')
            return redirect(url_for('main.scan_ui', last_exam_id=exam_id, booklet_code=booklet_code, student_identifier=student_identifier))

    # For GET request or if form validation fails
    return render_template('main/scan_interface.html', title='Scan Booklets', form=form)
