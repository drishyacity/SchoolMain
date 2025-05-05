from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, TextAreaField, DateField, TimeField, IntegerField, BooleanField, MultipleFileField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class NewsForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Content', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    image = FileField('Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    submit = SubmitField('Save')

class EventForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    time = TimeField('Time', validators=[Optional()])
    location = StringField('Location', validators=[DataRequired(), Length(max=200)])
    image = FileField('Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    submit = SubmitField('Save')

class GalleryUploadForm(FlaskForm):
    title = StringField('Title', validators=[Optional(), Length(max=200)])
    caption = StringField('Caption', validators=[Optional(), Length(max=255)])
    images = MultipleFileField('Images', validators=[
        DataRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    submit = SubmitField('Upload')

class ContactForm(FlaskForm):
    name = StringField('Your Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Your Email', validators=[DataRequired(), Email(), Length(max=120)])
    subject = StringField('Subject', validators=[Optional(), Length(max=200)])
    message = TextAreaField('Your Message', validators=[DataRequired()])
    submit = SubmitField('Send Message')

class AboutSectionForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Content', validators=[DataRequired()])
    order = IntegerField('Display Order', default=0)
    submit = SubmitField('Save')

class AcademicProgramForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[DataRequired()])
    order = IntegerField('Display Order', default=0)
    submit = SubmitField('Save')

class SchoolSettingsForm(FlaskForm):
    school_name = StringField('School Name', validators=[DataRequired(), Length(max=200)])
    school_address = StringField('Address', validators=[DataRequired(), Length(max=255)])
    school_phone = StringField('Phone', validators=[DataRequired(), Length(max=20)])
    school_email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    school_logo = FileField('Logo', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    submit = SubmitField('Save Settings')

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    is_admin = BooleanField('Admin Privileges')
    submit = SubmitField('Save')

class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    current_password = PasswordField('Current Password')
    new_password = PasswordField('New Password', validators=[
        Optional(),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        EqualTo('new_password', message='Passwords must match')
    ])
    submit = SubmitField('Update Profile')

class TeacherForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    position = StringField('Position', validators=[DataRequired(), Length(max=100)])
    qualification = StringField('Qualification', validators=[DataRequired(), Length(max=200)])
    bio = TextAreaField('Biography', validators=[Optional()])
    image = FileField('Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    order = IntegerField('Display Order', default=0)
    submit = SubmitField('Save')

class FacilityForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    image = FileField('Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    order = IntegerField('Display Order', default=0)
    submit = SubmitField('Save')

class SyllabusForm(FlaskForm):
    class_name = StringField('Class Name', validators=[DataRequired(), Length(max=50)])
    subject = StringField('Subject', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    file = FileField('Syllabus File (PDF)', validators=[
        Optional(),
        FileAllowed(['pdf'], 'PDF files only!')
    ])
    order = IntegerField('Display Order', default=0)
    submit = SubmitField('Save')

class AdmissionForm(FlaskForm):
    student_name = StringField('Student Name', validators=[DataRequired(), Length(max=100)])
    parent_name = StringField('Parent/Guardian Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(max=20)])
    address = TextAreaField('Address', validators=[DataRequired()])
    class_applying = StringField('Class Applying For', validators=[DataRequired(), Length(max=50)])
    previous_school = StringField('Previous School (if any)', validators=[Optional(), Length(max=200)])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    submit = SubmitField('Submit Application')

class HomeSliderForm(FlaskForm):
    title = StringField('Title (optional)', validators=[Optional(), Length(max=200)])
    image = FileField('Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    order = IntegerField('Display Order', default=0, validators=[NumberRange(min=0)])
    active = BooleanField('Active', default=True)
    submit = SubmitField('Save')
    
class AdmissionResponseForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected')
    ], validators=[DataRequired()])
    comments = TextAreaField('Comments', validators=[Optional()])
    submit = SubmitField('Update Status')
