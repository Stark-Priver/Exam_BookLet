from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length
from app.models import Exam, Venue

class ScanForm(FlaskForm):
    exam_id = SelectField('Select Exam', coerce=int, validators=[DataRequired(message="Please select an exam.")])
    student_identifier = StringField('Student ID', validators=[DataRequired(message="Student ID cannot be empty."), Length(min=1, max=64)])
    booklet_code = StringField('Booklet Code', validators=[Optional(), Length(min=3, max=50)]) # Optional initially, DataRequired if submitting booklet

    submit_check_student = SubmitField('Find Student / Check Eligibility')
    submit_record_scan = SubmitField('Record Booklet Scan')
    # Hidden fields to carry over verified data if needed, though managing state in route might be better
    # verified_student_id = HiddenField()
    # verified_exam_id = HiddenField()


    def __init__(self, *args, **kwargs):
        super(ScanForm, self).__init__(*args, **kwargs)
        # Populate exam choices dynamically
        # Populate exam choices dynamically
        # No explicit placeholder with ('', 'Text') is added here.
        # The browser will default to the first actual option or show nothing if the list is empty.
        # DataRequired validator will ensure an actual exam is selected on submit.
        self.exam_id.choices = [
            (e.id, f"{e.name} - {e.course} (on {e.date.strftime('%Y-%m-%d')} at {e.venue.name if e.venue else 'N/A'})")
            for e in Exam.query.join(Venue).order_by(Exam.date.desc(), Exam.name).all()
        ]
        # An empty list of choices is fine; DataRequired will handle validation.
        # The route will flash a message if no exams are available.
