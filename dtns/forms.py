from flask_wtf import FlaskForm
from wtforms import PasswordField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import TextAreaField
from wtforms.validators import DataRequired
from wtforms.validators import Email


class LoginForm(FlaskForm):
    email = StringField("email", validators=[DataRequired(), Email()])
    password = PasswordField("password", validators=[DataRequired()])
    login = SubmitField("Login")


class BlogPostForm(FlaskForm):
    source = TextAreaField("What would you like to share?", validators=[DataRequired()])
    submit = SubmitField("Submit")
