from flask import (
    Blueprint, 
    render_template,
    flash,
    redirect,
    url_for,
    request,
    current_app as app
    )

from flask_login import current_user, login_required

from family_tree import (
    db,
    bcrypt
)

from family_tree.models import (
    User,
    Person
)

from family_tree.cursor import Cursor

cursor = Cursor()   

bp = Blueprint('admin',__name__,url_prefix='/admin')

@bp.before_request
def restrict_access_to_admin():
    if not (current_user.is_authenticated and current_user.is_admin):
        app.logger.warning(f'User does not have admin permissions')
        flash('User does not have admin permissions', 'danger')
        return redirect(url_for('common.home'))
    
@bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('admin/dashboard.html')

@bp.route('/display_user/<int:user_id>')
@login_required
def display_user(user_id):
    user = cursor.query(db, User, filter_by=True, id=user_id).first()
    return render_template('admin/display_user.html', user=user)

@bp.route('/display_users')
@login_required
def display_users():
    users = cursor.query(db, User, *[User.is_admin == False], filter_by=False).all()
    return render_template('admin/display_users.html', users=users)

@bp.route('/delete_user/<int:user_id>', methods = ['POST'])
@login_required
def delete_user(user_id):
    cursor.delete(db, User, id=user_id)
    app.logger.info(f'Deleted user {user_id}')
    flash('Deleted Successfully!', 'success')
    return redirect(url_for('admin.display_users'))