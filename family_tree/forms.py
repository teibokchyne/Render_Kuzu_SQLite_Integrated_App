from flask_wtf import FlaskForm

from flask_wtf.file import FileField, FileAllowed, FileRequired

from wtforms.validators import (
    DataRequired,
    Email,
    Optional
)
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    EmailField,
    BooleanField,
    SelectField,
    DateField,
    IntegerField
)


class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me', default=False)
    submit = SubmitField('Login')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')


class UpsertProfilePictureForm(FlaskForm):
    picture_filename = FileField('Update Profile Picture', validators=[
                                 FileRequired(), FileAllowed(['jpg', 'jpeg', 'png'])])
    submit = SubmitField('Submit')


class UpsertPersonForm(FlaskForm):
    gender = SelectField('Gender', choices=[
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('OTHER', 'Other')
    ], validators=[DataRequired()])
    first_name = StringField('First Name', validators=[DataRequired()])
    middle_name = StringField('Middle Name')
    last_name = StringField('Last Name', validators=[DataRequired()])
    submit = SubmitField('Add/Edit Person')


class UpsertAddressForm(FlaskForm):
    is_permanent = BooleanField('Permanent Address')
    first_line = StringField('Address Line 1', validators=[DataRequired()])
    second_line = StringField('Address Line 2')
    pin_code = StringField('Pin Code', validators=[DataRequired()])
    state = StringField('State', default='Meghalaya',
                        validators=[DataRequired()])
    country = StringField('Country', default='India',
                          validators=[DataRequired()])
    landmark = StringField('Landmark')
    submit = SubmitField('Submit')


class UpsertImportantDateForm(FlaskForm):
    date_type = SelectField('Event', choices=[], validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    submit = SubmitField('Submit')


class UpsertContactDetailsForm(FlaskForm):
    country_code = IntegerField(
        'Country Code', default=91, validators=[Optional()])
    mobile_no = IntegerField('Mobile Number', validators=[Optional()])
    email = EmailField('Email', validators=[Optional(), Email()])
    submit = SubmitField('Submit')

    def validate_mobile_no(self, mobile_no):
        if mobile_no.data and not self.country_code.data:
            raise ValueError(
                'Country code is required if mobile number is provided.')

    def validate(self, extra_validators=None):
        rv = super().validate()
        if not rv:
            return False
        if not (self.mobile_no.data or self.email.data):
            self.mobile_no.errors.append(
                'At least one contact detail (mobile number or email) must be provided.')
            self.email.errors.append(
                'At least one contact detail (mobile number or email) must be provided.')
            return False
        return True


class UpsertRelativeForm(FlaskForm):
    relative_user_id = SelectField(
        'Relative', choices=[], coerce=int, validators=[DataRequired()])
    relation_type = SelectField(
        'Relation Type', choices=[], validators=[DataRequired()])
    submit = SubmitField('Add Relative')
