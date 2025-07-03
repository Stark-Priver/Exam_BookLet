from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager

class AdminUser(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<AdminUser {self.username}>'

@login_manager.user_loader
def load_user(id):
    return AdminUser.query.get(int(id))

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    student_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    course = db.Column(db.String(128))

    assignments = db.relationship('StudentExamAssignment', backref='student', lazy='dynamic')
    scans = db.relationship('ScanRecord', backref='student', lazy='dynamic')

    def __repr__(self):
        return f'<Student {self.student_id} - {self.name}>'

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=True) # E.g., CS101

    def __repr__(self):
        return f'<Course {self.name}{(" (" + self.code + ")") if self.code else ""}>'

class Venue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    location = db.Column(db.String(256))
    capacity = db.Column(db.Integer)

    exams = db.relationship('Exam', backref='venue', lazy='dynamic')

    def __repr__(self):
        return f'<Venue {self.name}>'

class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    course = db.Column(db.String(128)) # Course for which the exam is being held
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    assignments = db.relationship('StudentExamAssignment', backref='exam', lazy='dynamic')
    scans = db.relationship('ScanRecord', backref='exam', lazy='dynamic')

    def __repr__(self):
        return f'<Exam {self.name} on {self.date} at {self.venue.name if self.venue else "N/A"}>'

class StudentExamAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)

    # Unique constraint to prevent assigning a student to the same exam multiple times
    __table_args__ = (db.UniqueConstraint('student_id', 'exam_id', name='_student_exam_uc'),)

    def __repr__(self):
        return f'<StudentExamAssignment Student: {self.student.student_id if self.student else "N/A"} to Exam: {self.exam.name if self.exam else "N/A"}>'

class ScanRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    booklet_code = db.Column(db.String(128), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow, nullable=False)

    # Unique constraint for booklet_code per exam to prevent duplicate booklet scans for the same exam
    __table_args__ = (db.UniqueConstraint('exam_id', 'booklet_code', name='_exam_booklet_uc'),)

    def __repr__(self):
        return f'<ScanRecord Student: {self.student.student_id if self.student else "N/A"} - Exam: {self.exam.name if self.exam else "N/A"} - Booklet: {self.booklet_code}>'
