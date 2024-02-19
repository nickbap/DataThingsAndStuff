from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from flask_wtf.recaptcha import RecaptchaField
from wtforms import PasswordField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import TextAreaField
from wtforms.validators import DataRequired
from wtforms.validators import Email


class BlogPostForm(FlaskForm):
    title = StringField("Post Title", validators=[DataRequired()])
    slug = StringField("Slug", validators=[DataRequired()])
    description = StringField("Post Description", validators=[DataRequired()])
    source = TextAreaField("Post", validators=[DataRequired()])
    submit = SubmitField("Submit")


class CommentForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    username = StringField("Username", validators=[DataRequired()])
    comment = TextAreaField("Comment", validators=[DataRequired()])
    recaptcha = RecaptchaField()
    submit = SubmitField("Submit")


class ImageUploadForm(FlaskForm):
    file = FileField("Upload an Image")
    submit = SubmitField("Submit")


class LoginForm(FlaskForm):
    email = StringField("email", validators=[DataRequired(), Email()])
    password = PasswordField("password", validators=[DataRequired()])
    login = SubmitField("Login")
