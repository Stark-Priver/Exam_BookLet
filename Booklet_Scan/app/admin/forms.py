from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, DateField, TimeField, SelectField
from wtforms.validators import DataRequired, Optional, ValidationError, Length
from app.models import Venue, Course # For Venue selection in ExamForm and Course model

# Form for Course
class CourseForm(FlaskForm):
    name = StringField('Course Name', validators=[DataRequired(), Length(max=128)])
    code = StringField('Course Code (Optional)', validators=[Optional(), Length(max=20)])
    submit = SubmitField('Save Course')

# Form for Student
class StudentForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    student_id = StringField('Student ID', validators=[DataRequired()])
    # Course will be a SelectField, populated in routes
    course = SelectField('Course', validators=[DataRequired(message="Please select a course.")])
    submit = SubmitField('Save Student')

    def __init__(self, *args, **kwargs):
        super(StudentForm, self).__init__(*args, **kwargs)
        # Populate course choices dynamically. This will be overridden in the route
        # to ensure fresh data, but good to have a default.
        self.course.choices = [(c.name, c.name) for c in Course.query.order_by(Course.name).all()]
        if not self.course.choices:
            self.course.choices.insert(0, ('', 'No courses available - Add courses first'))
        # else: # No need for "Select a course" here if DataRequired and no default choice value
            # self.course.choices.insert(0, ('', '--- Select a Course ---'))


# Form for Venue
class VenueForm(FlaskForm):
    name = StringField('Venue Name', validators=[DataRequired()])
    location = StringField('Location', validators=[Optional()])
    capacity = IntegerField('Capacity', validators=[Optional()])
    submit = SubmitField('Save Venue')

# Form for Exam
class ExamForm(FlaskForm):
    name = StringField('Exam Name', validators=[DataRequired()])
    course = StringField('Course Code/Name', validators=[DataRequired()])
    venue_id = SelectField('Venue', coerce=int, validators=[DataRequired()])
    date = DateField('Date (YYYY-MM-DD)', validators=[DataRequired()], format='%Y-%m-%d')
    start_time = TimeField('Start Time (HH:MM)', validators=[DataRequired()], format='%H:%M')
    end_time = TimeField('End Time (HH:MM)', validators=[DataRequired()], format='%H:%M')
    submit = SubmitField('Save Exam')

    def __init__(self, *args, **kwargs):
        super(ExamForm, self).__init__(*args, **kwargs)
        self.venue_id.choices = [(v.id, v.name) for v in Venue.query.order_by(Venue.name).all()]
        # Add a default blank choice if desired
        # self.venue_id.choices.insert(0, ('', 'Select a Venue'))


# Form for Student-Exam Assignment
class StudentExamAssignmentForm(FlaskForm):
    student_id = SelectField('Student (by ID)', coerce=int, validators=[DataRequired()])
    exam_id = SelectField('Exam', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Assign Student to Exam')

    # Note: Populating choices for student_id and exam_id will be done in the route
    # as it might involve a large number of students.
    # A better UX for student selection might involve a search or autocomplete.
    # For now, we'll assume selection by ID or a dropdown populated in the route.

    def __init__(self, *args, **kwargs):
        super(StudentExamAssignmentForm, self).__init__(*args, **kwargs)
        # Choices will be populated in the route handler
        self.student_id.choices = []
        self.exam_id.choices = []
