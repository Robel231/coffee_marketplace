from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, FloatField, SelectField, FileField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('farmer', 'Farmer'), ('buyer', 'Buyer')], validators=[DataRequired()])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired()])
    image = FileField('Product Image')
    submit = SubmitField('Add Product')

class ProfileForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("New Password", validators=[EqualTo("confirm_password", message="Passwords must match")])
    confirm_password = PasswordField("Confirm Password")
    submit = SubmitField("Update Profile")
