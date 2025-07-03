from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.admin import bp
from app.models import Student, Venue, Exam, StudentExamAssignment
from app.admin.forms import StudentForm, VenueForm, ExamForm, StudentExamAssignmentForm

# Utility to check if current user is an admin (adjust as needed if more roles are added)
def is_admin():
    return hasattr(current_user, 'username')

@bp.before_request
@login_required # Ensures user is logged in for all admin routes
def before_request():
    if not is_admin():
        flash('You do not have permission to access the admin area.')
        return redirect(url_for('main.index'))

@bp.route('/dashboard')
def dashboard():
    return render_template('admin/dashboard.html', title='Admin Dashboard')

# --- Student CRUD ---
@bp.route('/students')
def list_students():
    page = request.args.get('page', 1, type=int)
    students = Student.query.order_by(Student.name).paginate(page=page, per_page=10)
    return render_template('admin/students_list.html', students=students, title='Manage Students')

@bp.route('/students/new', methods=['GET', 'POST'])
def add_student():
    form = StudentForm()
    if form.validate_on_submit():
        existing_student = Student.query.filter_by(student_id=form.student_id.data).first()
        if existing_student:
            flash('Student ID already exists.', 'warning')
        else:
            student = Student(name=form.name.data, student_id=form.student_id.data, course=form.course.data)
            db.session.add(student)
            db.session.commit()
            flash('Student added successfully!', 'success')
            return redirect(url_for('admin.list_students'))
    return render_template('admin/student_form.html', form=form, title='Add Student')

@bp.route('/students/<int:id>/edit', methods=['GET', 'POST'])
def edit_student(id):
    student = Student.query.get_or_404(id)
    form = StudentForm(obj=student)
    if form.validate_on_submit():
        # Check if student_id is being changed and if the new one already exists for another student
        if student.student_id != form.student_id.data:
            existing_student = Student.query.filter(Student.id != student.id, Student.student_id == form.student_id.data).first()
            if existing_student:
                flash('That Student ID is already in use by another student.', 'warning')
                return render_template('admin/student_form.html', form=form, title='Edit Student', student=student)

        student.name = form.name.data
        student.student_id = form.student_id.data
        student.course = form.course.data
        db.session.commit()
        flash('Student updated successfully!', 'success')
        return redirect(url_for('admin.list_students'))
    return render_template('admin/student_form.html', form=form, title='Edit Student', student=student)

@bp.route('/students/<int:id>/delete', methods=['POST'])
def delete_student(id):
    student = Student.query.get_or_404(id)
    # Consider implications: what if student is assigned to exams or has scan records?
    # For now, simple delete. Add cascading deletes or checks as needed.
    try:
        db.session.delete(student)
        db.session.commit()
        flash('Student deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting student: {str(e)}. They might be linked to other records.', 'danger')
    return redirect(url_for('admin.list_students'))

# --- Venue CRUD ---
@bp.route('/venues')
def list_venues():
    page = request.args.get('page', 1, type=int)
    venues = Venue.query.order_by(Venue.name).paginate(page=page, per_page=10)
    return render_template('admin/venues_list.html', venues=venues, title='Manage Venues')

@bp.route('/venues/new', methods=['GET', 'POST'])
def add_venue():
    form = VenueForm()
    if form.validate_on_submit():
        existing_venue = Venue.query.filter_by(name=form.name.data).first()
        if existing_venue:
            flash('Venue name already exists.', 'warning')
        else:
            venue = Venue(name=form.name.data, location=form.location.data, capacity=form.capacity.data)
            db.session.add(venue)
            db.session.commit()
            flash('Venue added successfully!', 'success')
            return redirect(url_for('admin.list_venues'))
    return render_template('admin/venue_form.html', form=form, title='Add Venue')

@bp.route('/venues/<int:id>/edit', methods=['GET', 'POST'])
def edit_venue(id):
    venue = Venue.query.get_or_404(id)
    form = VenueForm(obj=venue)
    if form.validate_on_submit():
        if venue.name != form.name.data:
            existing_venue = Venue.query.filter(Venue.id != venue.id, Venue.name == form.name.data).first()
            if existing_venue:
                flash('That Venue Name is already in use.', 'warning')
                return render_template('admin/venue_form.html', form=form, title='Edit Venue', venue=venue)

        venue.name = form.name.data
        venue.location = form.location.data
        venue.capacity = form.capacity.data
        db.session.commit()
        flash('Venue updated successfully!', 'success')
        return redirect(url_for('admin.list_venues'))
    return render_template('admin/venue_form.html', form=form, title='Edit Venue', venue=venue)

@bp.route('/venues/<int:id>/delete', methods=['POST'])
def delete_venue(id):
    venue = Venue.query.get_or_404(id)
    if venue.exams.count() > 0:
        flash('Cannot delete venue: It is associated with one or more exams.', 'danger')
        return redirect(url_for('admin.list_venues'))
    try:
        db.session.delete(venue)
        db.session.commit()
        flash('Venue deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting venue: {str(e)}', 'danger')
    return redirect(url_for('admin.list_venues'))


# --- Exam CRUD ---
@bp.route('/exams')
def list_exams():
    page = request.args.get('page', 1, type=int)
    exams = Exam.query.order_by(Exam.date.desc(), Exam.start_time.desc()).paginate(page=page, per_page=10)
    return render_template('admin/exams_list.html', exams=exams, title='Manage Exams')

@bp.route('/exams/new', methods=['GET', 'POST'])
def add_exam():
    form = ExamForm()
    form.venue_id.choices = [(v.id, v.name) for v in Venue.query.order_by(Venue.name).all()]
    if not form.venue_id.choices:
        flash('No venues available. Please add a venue first.', 'warning')
        # Optionally redirect to add venue page or disable form

    if form.validate_on_submit():
        exam = Exam(name=form.name.data, course=form.course.data, venue_id=form.venue_id.data,
                    date=form.date.data, start_time=form.start_time.data, end_time=form.end_time.data)
        db.session.add(exam)
        db.session.commit()
        flash('Exam added successfully!', 'success')
        return redirect(url_for('admin.list_exams'))
    return render_template('admin/exam_form.html', form=form, title='Add Exam')

@bp.route('/exams/<int:id>/edit', methods=['GET', 'POST'])
def edit_exam(id):
    exam = Exam.query.get_or_404(id)
    form = ExamForm(obj=exam)
    form.venue_id.choices = [(v.id, v.name) for v in Venue.query.order_by(Venue.name).all()]
    if form.validate_on_submit():
        exam.name = form.name.data
        exam.course = form.course.data
        exam.venue_id = form.venue_id.data
        exam.date = form.date.data
        exam.start_time = form.start_time.data
        exam.end_time = form.end_time.data
        db.session.commit()
        flash('Exam updated successfully!', 'success')
        return redirect(url_for('admin.list_exams'))
    return render_template('admin/exam_form.html', form=form, title='Edit Exam', exam=exam)

@bp.route('/exams/<int:id>/delete', methods=['POST'])
def delete_exam(id):
    exam = Exam.query.get_or_404(id)
    # Consider implications: assignments, scan records
    try:
        # Add checks for related assignments or scans if strict deletion is not desired
        if exam.assignments.count() > 0 or exam.scans.count() > 0:
             flash('Cannot delete exam: It has student assignments or scan records. Please remove them first.', 'danger')
             return redirect(url_for('admin.list_exams'))
        db.session.delete(exam)
        db.session.commit()
        flash('Exam deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting exam: {str(e)}', 'danger')
    return redirect(url_for('admin.list_exams'))


# --- Student-Exam Assignment CRUD ---
@bp.route('/assignments')
def list_assignments():
    page = request.args.get('page', 1, type=int)
    # Join with Student and Exam to allow sorting/filtering by their fields if needed later
    assignments = StudentExamAssignment.query.join(Student).join(Exam)\
        .order_by(Exam.date.desc(), Exam.name, Student.name)\
        .paginate(page=page, per_page=10)
    return render_template('admin/assignments_list.html', assignments=assignments, title='Manage Student Assignments')

@bp.route('/assignments/new', methods=['GET', 'POST'])
def add_assignment():
    form = StudentExamAssignmentForm()
    # Populate choices for students and exams
    form.student_id.choices = [(s.id, f"{s.name} ({s.student_id})") for s in Student.query.order_by(Student.name).all()]
    form.exam_id.choices = [(e.id, f"{e.name} on {e.date.strftime('%Y-%m-%d')} at {e.venue.name}") for e in Exam.query.join(Venue).order_by(Exam.date.desc(), Exam.name).all()]

    if not form.student_id.choices:
        flash('No students available. Please add students first.', 'warning')
    if not form.exam_id.choices:
        flash('No exams available. Please add exams first.', 'warning')

    if form.validate_on_submit():
        existing_assignment = StudentExamAssignment.query.filter_by(
            student_id=form.student_id.data,
            exam_id=form.exam_id.data
        ).first()
        if existing_assignment:
            flash('This student is already assigned to this exam.', 'warning')
        else:
            assignment = StudentExamAssignment(student_id=form.student_id.data, exam_id=form.exam_id.data)
            db.session.add(assignment)
            db.session.commit()
            flash('Student assigned to exam successfully!', 'success')
            return redirect(url_for('admin.list_assignments'))
    return render_template('admin/assignment_form.html', form=form, title='Assign Student to Exam')

@bp.route('/assignments/<int:id>/delete', methods=['POST'])
def delete_assignment(id):
    assignment = StudentExamAssignment.query.get_or_404(id)
    try:
        db.session.delete(assignment)
        db.session.commit()
        flash('Student assignment deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting assignment: {str(e)}', 'danger')
    return redirect(url_for('admin.list_assignments'))
