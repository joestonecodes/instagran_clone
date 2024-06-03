
import re
import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from PIL import Image
from . import db
from .models import Post, User, Comment, Like, Notification, Story, Hashtag
from .forms import UploadForm, CommentForm, EditProfileForm, SearchForm, StoryForm


main = Blueprint('main', __name__)

def save_picture(form_picture, folder, rotate, resize_width, resize_height):
    random_hex = os.urandom(8).hex()
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, folder, picture_fn)
    
    # Create directory if it does not exist
    os.makedirs(os.path.dirname(picture_path), exist_ok=True)
    
    img = Image.open(form_picture)
    
    # Rotate image
    if rotate:
        img = img.rotate(rotate)
    
    # Resize image
    if resize_width and resize_height:
        img = img.resize((resize_width, resize_height))
    
    img.save(picture_path)
    
    return picture_fn

def create_notification(user, name, data):
    notification = Notification(name=name, data=data, user_id=user.id)
    db.session.add(notification)
    db.session.commit()

@main.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    search_form = SearchForm()
    if form.validate_on_submit():
        if form.image.data:
            rotate = form.rotate.data
            resize_width = form.resize_width.data
            resize_height = form.resize_height.data
            if form.upload_type.data == 'post':
                picture_file = save_picture(form.image.data, folder='uploads', rotate=rotate, resize_width=resize_width, resize_height=resize_height)
                post = Post(image_file=picture_file, author=current_user)
                db.session.add(post)
                
                # Process hashtags
                hashtags_text = form.hashtags.data
                hashtags_list = extract_hashtags(hashtags_text)
                for tag in hashtags_list:
                    hashtag = Hashtag.query.filter_by(name=tag).first()
                    if not hashtag:
                        hashtag = Hashtag(name=tag)
                        db.session.add(hashtag)
                    post.hashtags.append(hashtag)
                
                create_notification(current_user, 'new_post', f'User {current_user.username} created a new post')
                flash('Your post has been uploaded!', 'success')
            elif form.upload_type.data == 'story':
                picture_file = save_picture(form.image.data, folder='static/story_pics', rotate=rotate, resize_width=resize_width, resize_height=resize_height)
                story = Story(image_file=picture_file, user_id=current_user.id)
                db.session.add(story)
                create_notification(current_user, 'new_story', f'User {current_user.username} created a new story')
                flash('Your story has been uploaded!', 'success')
            db.session.commit()
            return redirect(url_for('main.index'))
    return render_template('upload.html', form=form, search_form=search_form)

def extract_hashtags(text):
    return re.findall(r'#(\w+)', text)

@main.route('/')
def index():
    form = SearchForm()
    story_form = StoryForm()
    if current_user.is_authenticated:
        return redirect(url_for('main.feed'))
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    comment_form = CommentForm()
    return render_template('index.html', posts=posts, comment_form=comment_form, form=form, story_form=story_form)


@main.route('/feed')
@login_required
def feed():
    form = SearchForm()
    story_form = StoryForm()
    posts = current_user.followed_posts().all()
    stories = Story.query.order_by(Story.timestamp.asc()).all()
    comment_form = CommentForm()
    return render_template('feed.html', posts=posts, stories=stories, comment_form=comment_form, form=form, story_form=story_form)

@main.route('/explore')
def explore():
    form = SearchForm()
    posts = Post.query.order_by(Post.timestamp.asc()).all()
    comment_form = CommentForm()
    return render_template('explore.html', posts=posts, comment_form=comment_form, form=form)

@main.route('/upload_story', methods=['GET', 'POST'])
@login_required
def upload_story():
    form = StoryForm()
    if form.validate_on_submit():
        if form.image.data:
            picture_file = save_picture(form.image.data, folder='static/story_pics')
            story = Story(image_file=picture_file, user_id=current_user.id)
            db.session.add(story)
            db.session.commit()
            flash('Your story has been posted!', 'success')
            return redirect(url_for('main.feed'))
    return render_template('upload_story.html', form=form)

@main.route('/stories/<int:story_id>')
@login_required
def view_story(story_id):
    story = Story.query.get_or_404(story_id)
    form = SearchForm()  # Ensure form is instantiated
    return render_template('view_story.html', story=story, form=form)

@main.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(os.path.join(current_app.root_path, 'uploads'), filename)

@main.route('/profile/<username>')
@login_required
def profile(username):
    form = SearchForm()
    story_form = StoryForm()
    user = User.query.filter_by(username=username).first_or_404()
    stories = Story.query.filter_by(user_id=user.id).order_by(Story.timestamp.desc()).all()
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.timestamp.desc()).all()
    comment_form = CommentForm()
    is_following = current_user.is_following(user)
    return render_template('profile.html', user=user, posts=posts, comment_form=comment_form, is_following=is_following, form=form, stories=stories, story_form=story_form)

@main.route('/comment/<int:post_id>', methods=['POST'])
@login_required
def comment(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(text=form.text.data, author=current_user, post=post)
        db.session.add(comment)
        db.session.commit()
        create_notification(post.author, 'comment', f'{current_user.username} commented on your post.')
        flash('Your comment has been added.', 'success')
    return redirect(url_for('main.index'))

@main.route('/like/<int:post_id>', methods=['POST'])
@login_required
def like(post_id):
    post = Post.query.get_or_404(post_id)
    like = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first()
    if like:
        db.session.delete(like)
        message = f'{current_user.username} unliked your post.'
    else:
        new_like = Like(user_id=current_user.id, post_id=post.id)
        db.session.add(new_like)
        message = f'{current_user.username} liked your post.'
    db.session.commit()
    create_notification(post.author, 'like', message)
    return redirect(request.referrer or url_for('main.index'))

@main.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user is None:
        flash(f'User {username} not found.', 'danger')
        return redirect(url_for('main.index'))
    if user == current_user:
        flash('You cannot follow yourself!', 'danger')
        return redirect(url_for('main.profile', username=username))
    current_user.follow(user)
    db.session.commit()
    create_notification(user, 'follow', f'{current_user.username} is now following you.')
    flash(f'You are now following {username}!', 'success')
    return redirect(url_for('main.profile', username=username))

@main.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user is None:
        flash(f'User {username} not found.', 'danger')
        return redirect(url_for('main.index'))
    if user == current_user:
        flash('You cannot unfollow yourself!', 'danger')
        return redirect(url_for('main.profile', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(f'You have unfollowed {username}.', 'success')
    return redirect(url_for('main.profile', username=username))

@main.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    search_form = SearchForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data, folder='static/profile_pics')
            current_user.profile_image = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('main.profile', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template('edit_profile.html', form=form, search_form=search_form)

@main.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    comment_form = CommentForm()
    if form.validate_on_submit():
        query = form.query.data
        users = User.query.filter(User.username.like(f'%{query}%')).all()
        posts = Post.query.join(User).filter(User.username.like(f'%{query}%')).all()
        return render_template('search_results.html', users=users, posts=posts, query=query, form=form, comment_form=comment_form)
    return render_template('search.html', form=form, comment_form=comment_form)

@main.route('/notifications')
@login_required
def notifications():
    form = SearchForm()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.timestamp.desc()).all()
    print(f"Fetched notifications: {notifications}")  # Debugging print
    for notification in notifications:
        notification.read = True
    db.session.commit()
    return render_template('notifications.html', notifications=notifications, form=form)


@main.route('/hashtag/<string:hashtag>')
def hashtag(hashtag):
    form = SearchForm()
    comment_form = CommentForm()
    story_form = CommentForm()
    hashtag_obj = Hashtag.query.filter_by(name=hashtag).first_or_404()
    posts = Post.query.join(Post.hashtags).filter(Hashtag.id == hashtag_obj.id).order_by(Post.timestamp.desc()).all()
    return render_template('hashtag.html', hashtag=hashtag, posts=posts, comment_form=comment_form, form=form, story_form=story_form)