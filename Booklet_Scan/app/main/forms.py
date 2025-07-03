from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length
from app.models import Exam, Venue

class ScanForm(FlaskForm):
    exam_id = SelectField('Select Exam', coerce=int, validators=[DataRequired(message="Please select an exam.")])
    booklet_code = StringField('Booklet Code', validators=[DataRequired(message="Booklet code cannot be empty."), Length(min=3, max=50)])
    student_identifier = StringField('Student ID', validators=[DataRequired(message="Student ID cannot be empty."), Length(min=1, max=64)]) # Student ID from booklet or manual entry
    submit = SubmitField('Record Scan')

    def __init__(self, *args, **kwargs):
        super(ScanForm, self).__init__(*args, **kwargs)
        # Populate exam choices dynamically
        self.exam_id.choices = [
            (e.id, f"{e.name} - {e.course} (on {e.date.strftime('%Y-%m-%d')} at {e.venue.name if e.venue else 'N/A'})")
            for e in Exam.query.join(Venue).order_by(Exam.date.desc(), Exam.name).all()
        ]
        if not self.exam_id.choices:
            self.exam_id.choices.insert(0, ('', 'No exams available - Please add exams in Admin Panel'))
        else:
            self.exam_id.choices.insert(0, ('', '--- Select an Exam ---'))
