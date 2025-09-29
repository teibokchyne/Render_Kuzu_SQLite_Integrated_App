from flask import (
    Blueprint, 
    render_template,
    flash,
    redirect,
    url_for,
    request,
    current_app as app
    )

from flask_login import login_user, current_user, login_required, logout_user

from family_tree import db, bcrypt

from family_tree.forms import (
    LoginForm,
    RegistrationForm
)

from family_tree.models import (
    User
)

from family_tree.cursor import Cursor

cursor = Cursor()

bp = Blueprint('common',__name__)

@bp.route('/')
def home():
    """
    Render the home page.
    """
    app.logger.info("Rendering home page.")
    return render_template('common/home.html')

@bp.route('/login', methods = ['GET', 'POST'])
def login():
    """
    Handle user login. Renders login form and processes authentication.
    """
    if current_user.is_authenticated:
        app.logger.info("User already authenticated, redirecting to home.")
        return redirect(url_for('common.home'))
    else:
        form = LoginForm()
        if form.validate_on_submit():
            user = cursor.query(db, User, filter_by=True, email=form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember.data)
                app.logger.info(f"User {form.email.data} logged in successfully.")
                return redirect(url_for('common.home'))
            else:
                app.logger.warning(f"Failed login attempt for {form.email.data}.")
                flash('Login Unsuccessful. Please check email and password', 'danger')
        else:
            if request.method == 'POST':
                app.logger.warning(f"Login form validation failed for {form.email.data}.")
        return render_template('common/login.html', form=form)
    
@bp.route('/register', methods = ['GET', 'POST'])
def register():
    """
    Handle user registration. Renders registration form and creates new user.
    """
    if current_user.is_authenticated:
        app.logger.info("User already authenticated, redirecting to home.")
        return redirect(url_for('common.home'))
    else:
        form = RegistrationForm()
        if form.validate_on_submit():
            user = cursor.query(db, User, filter_by=True, email=form.email.data).first()
            if user:
                flash('Email already registered. Please log in.', 'warning')
                return redirect(url_for('common.register'))
            user = cursor.query(db, User, filter_by=True, username=form.username.data).first()
            if user:
                flash('Username already registered. Please use a different one.', 'warning')
                return redirect(url_for('common.register'))
            cursor.add(
                db,
                User,
                username=form.username.data,
                email=form.email.data,
                password_hash=bcrypt.generate_password_hash(form.password.data).decode('utf-8') ,
                is_admin=False
            )
            app.logger.info(f"New user registered: {form.email.data}")
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('common.login'))
        else:
            if request.method == 'POST':
                app.logger.warning(f"Registration form validation failed for {form.email.data}.")
        return render_template('common/register.html', form=form)
    
@bp.route('/logout')
@login_required
def logout():
    """
    Log out the current user and redirect to home page.
    """
    app.logger.info(f"User {current_user.get_id()} logged out.")
    logout_user()
    return redirect(url_for('common.home'))
