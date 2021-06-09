from . import auth
from .. import db
from .forms import LoginForm, RegForm
from ..models import User
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from pathlib import Path



@auth.route('/login', methods = ['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            # Login the user and also add a cookie based on their remember choice
            login_user(user, form.remember_me.data)
            next_page = request.args.get('next')
            # Redirect to Home page if user didn't try accessing another page
            if next_page is None or not next_page.startswith('/'):
                next_page = url_for('main.index')
            return redirect(next_page)
        flash('Invalid username or password.')

    return render_template('auth/login.html', form = form)


@auth.route('/register', methods = ['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        # logout()
        pass
    form = RegForm()
    if form.validate_on_submit():
        user = User(email = form.email.data,
                    username = form.username.data,
                    password = form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        # TODO: Send confirmation email here
        flash('A confirmation email has been sent to your inbox.')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form = form)


@auth.route('/logout')
@login_required
def logout():
    """Login is clearly required as the app cannot logout a non-authenticated user"""
    logout_user()
    return redirect(url_for('.login'))


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    elif current_user.confirm(token):
        # Commit again to update the User's confirmed status
        db.session.commit()
        flash('Account Confirmed!')
    else:
        flash('Confirmation link invalid or expire.')
    return redirect(url_for('main.index'))


@auth.before_app_request
def before_request():
    # Basically if an authenticated user tries to access a main part of the site
    # that is not for authentication or a static file.
    if current_user.is_authenticated:
        # Ping the user to update their last_seen.
        current_user.ping()
        if not current_user.confirmed \
                and request.endpoint \
                and request.blueprint != 'auth' \
                and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    """
    Redirecting the user to the confirmation notice page with an option to resend
    the link
    :return:
    """
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    # send user mail here
    flash('A new confirmation mail has been sent to your inbox!')
    return redirect(url_for('main.index'))
