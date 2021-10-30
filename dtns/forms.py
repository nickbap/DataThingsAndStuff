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
    title = StringField("Post Title", validators=[DataRequired()])
    slug = StringField("Slug", validators=[DataRequired()])
    description = StringField("Post Description", validators=[DataRequired()])
    source = TextAreaField("Post", validators=[DataRequired()])
    submit = SubmitField("Submit")
