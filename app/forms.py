"""WTForms definitions for KaushalSetu.

These forms are used for authentication, registration, order creation, and
application to workforce requests.
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    TextAreaField,
    IntegerField,
    DateTimeField,
    SelectField,
    BooleanField,
    DecimalField,
)
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange
from .models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')

class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('shg', 'SHG'), ('youth', 'Youth'), ('employer', 'Employer')], validators=[DataRequired()])
    name = StringField('Name / Company', validators=[DataRequired()])
    description = TextAreaField('Description (SHG)')
    skills = StringField('Skills (comma separated)')
    availability = StringField('Availability (Youth)')
    location = StringField('Location', validators=[DataRequired()])
    contact_person = StringField('Contact Person (Employer)')
    submit = SubmitField('Register')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

class OrderForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    deadline = DateTimeField('Deadline (YYYY-MM-DD HH:MM)', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    submit = SubmitField('Create Order')

class ApplicationForm(FlaskForm):
    submit = SubmitField('Apply')

# Form for SHG to create a detailed workforce request
class WorkforceRequestForm(FlaskForm):
    job_title = StringField('Job Title', validators=[DataRequired()])
    required_skills = StringField('Required Skills (comma separated)', validators=[DataRequired()])
    needed_quantity = IntegerField('Number of Workers Needed', validators=[DataRequired(), NumberRange(min=1, message='Must be at least 1')])
    location = StringField('Location', validators=[DataRequired()])
    payment_amount = DecimalField('Payment Amount (total)', validators=[DataRequired(), NumberRange(min=0, message='Must be non‑negative')])
    duration_days = IntegerField('Expected Duration (days)', validators=[DataRequired(), NumberRange(min=1, message='Must be at least 1')])
    description = TextAreaField('Job Description')
    submit = SubmitField('Create Request')
