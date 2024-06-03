from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField, TextAreaField, BooleanField, RadioField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, NumberRange, Optional, Length
from flask_login import current_user
from flask_wtf.file import FileAllowed
from app.models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class StoryForm(FlaskForm):
    image = FileField('Upload Story', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Post')

class UploadForm(FlaskForm):
    image = FileField('Upload Image', validators=[FileAllowed(['jpg', 'png', 'jpeg']), DataRequired()])
    upload_type = RadioField('Upload Type', choices=[('post', 'Post'), ('story', 'Story')], default='post', validators=[DataRequired()])
    hashtags = StringField('Hashtags', validators=[Length(max=100)], render_kw={"placeholder": "Enter hashtags separated by spaces"})
    rotate = IntegerField('Rotate (degrees)', validators=[Optional(), NumberRange(min=0, max=360)], default=0)
    resize_width = IntegerField('Resize Width (pixels)', validators=[Optional(), NumberRange(min=1)], default=500)
    resize_height = IntegerField('Resize Height (pixels)', validators=[Optional(), NumberRange(min=1)], default=500)
    submit = SubmitField('Upload')


class CommentForm(FlaskForm):
    text = TextAreaField('Comment', validators=[DataRequired()])
    submit = SubmitField('Add Comment')

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update Profile')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is taken. Please choose a different one.')
            
class SearchForm(FlaskForm):
    query = StringField('Search', validators=[DataRequired()])
    submit = SubmitField('Search')

class MessageForm(FlaskForm):
    recipient = StringField('Recipient', validators=[DataRequired()])
    body = TextAreaField('Message', validators=[DataRequired(), Length(min=1, max=500)])
    submit = SubmitField('Send')