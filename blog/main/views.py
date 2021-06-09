from . import main
from .. import db
from flask import render_template, flash, redirect, url_for, abort, request
from flask_login import login_required, current_user
from .forms import EditProfileForm, EditProfileAdminForm, PostForm
from ..models import User, Role, Permission, Post
from ..decorators import admin_required, permission_required



@main.route('/', methods = ['GET', 'POST'])
def index():
    form = PostForm()
    # To prevent guest users from writing posts to the site, we check permission
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        post = Post(body = form.body.data,
                    author = current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('.index'))
    # TODO: Add pagination for user posts
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template('main/index.html', form = form, posts = posts)


@main.route('/user/<username>')
@login_required
def user(username):
    u = User.query.filter_by(username = username).first_or_404()
    posts = u.posts.order_by(Post.timestamp.desc()).all()
    return render_template('main/user.html', user = u, posts = posts)


@main.route('/edit-profile', methods = ['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user._get_current_object())
        db.session.commit()
        flash('Profile successfully updated.')
        return redirect(url_for('.user', username = current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('main/edit_profile.html', form = form)


@main.route('/edit-profile/<int:user_id>', methods = ['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(user_id):
    """Method will not be used till I have the strength to do the html and all that
    other work I hate.
    Aborting with a 404 for now."""
    u = User.query.get_or_404(user_id)
    form = EditProfileAdminForm(user = u)
    if form.validate_on_submit():
        u.email = form.email.data
        u.username = form.username.data
        u.confirmed = form.confirmed.data
        u.role = Role.query.get(form.role.data)
        u.name = form.name.data
        u.location = form.location.data
        u.about_me = form.about_me.data
        db.session.add(u)
        db.session.commit()
        flash('The profile has been updated.')
        return redirect(url_for('.user', username = u.username))
    form.email.data = u.email
    form.username.data = u.username
    form.confirmed.data = u.confirmed
    form.role.data = u.role_id
    form.name.data = u.name
    form.location.data = u.location
    form.about_me.data = u.about_me
    # return render_template('edit_profile.html', form = form, user = u)
    abort(404)


@main.route('/post/<int:post_id>')
def post(post_id):
    p = Post.query.get_or_404(post_id)
    return render_template('main/post.html', posts = [p])


@main.route('/edit/<int:post_id>', methods = ['GET', 'POST'])
@login_required
def edit(post_id):
    p = Post.query.get_or_404(post_id)
    # Prevent normal users and guests on the site.
    if current_user != p.author and not current_user.can(Permission.ADMIN):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        p.body = form.body.data
        db.session.add(p)
        db.session.commit()
        flash('Post updated!')
        return redirect(url_for('.post', post_id = p.id))
    form.body.data = p.body
    return render_template('main/edit_post.html', form = form)

@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    abort(404)
    """
    View function handling following of users
    Custom decorator attached to ensure user has the permission to follow
    :param username: Username of account being followed
    :return: redirect back to profile
    """
    # Holds user to be followed
    user = User.query.filter_by(username = username).first()
    if user is None:
        flash('Invalid User')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('You are already following this user.')
        return redirect(url_for('.user', username = username))
    current_user.follow(user)
    db.session.commit()
    flash('Followed {}'.format(username))
    return redirect(url_for('.user', username = username))

@main.route('/followers/<username>')
def followers(username):
    abort(404)
    user = User.query.filter_by(username = username).first()
    if user is None:
        flash('Invalid User.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type = int)
