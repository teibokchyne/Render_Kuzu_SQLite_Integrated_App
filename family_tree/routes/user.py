# Add Contact Details
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

from family_tree.cursor import Cursor

from family_tree.services.user import (
    save_picture,
    update_profile_picture,
    update_person,
    prefill_address_form,
    fill_address_from_form,
    get_relative_details,
    check_relative_constraints,
    check_validity_relation,
    add_relative_to_database,
    prefill_upsert_relative_form,
    delete_relative_from_database
)
from family_tree.models import (
    User,
    GenderEnum,
    Person,
    Picture,
    Address,
    ImportantDateTypeEnum,
    ImportantDates,
    ContactDetails,
    RelativesTypeEnum,
    Relatives
)
from family_tree.forms import (
    UpsertProfilePictureForm,
    UpsertPersonForm,
    UpsertAddressForm,
    UpsertImportantDateForm,
    UpsertContactDetailsForm,
    UpsertRelativeForm
)
from family_tree import db


cursor = Cursor()

bp = Blueprint('user', __name__)


@bp.before_request
def restrict_access_to_user():
    if not current_user.is_authenticated or current_user.is_admin:
        app.logger.warning("Unauthorized access attempt to user routes.")
        return redirect(url_for('common.login'))
    else:
        app.logger.info(f"User {current_user.username} accessed user routes.")


@bp.route('/dashboard')
@login_required
def dashboard():
    """
    Render the user dashboard page.
    """
    app.logger.info(f"Rendering dashboard for user {current_user.get_id()}.")
    return render_template('user/dashboard.html')


@bp.route('/display_profile', methods=['GET', 'POST'])
@login_required
def display_profile():

    form = UpsertProfilePictureForm()

    if form.validate_on_submit():
        picture_filename = save_picture(form.picture_filename.data)
        update_profile_picture(db, Picture, current_user, picture_filename)
        flash('Profile Picture Updated!', 'success')

    if current_user.profile_picture:
        profile_image_url = url_for(
            'static', filename=f'profile_pictures/{current_user.profile_picture.picture_filename}')
    else:
        profile_image_url = None

    return render_template('user/display_profile.html', form=form, user=current_user, profile_image_url=profile_image_url)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """
    Render the user's edit profile page.
    """
    app.logger.info(
        f"Rendering edit profile page for user {current_user.username}.")
    form = UpsertPersonForm()
    if request.method == 'GET' and current_user.person:
        form.first_name.data = current_user.person.first_name
        form.middle_name.data = current_user.person.middle_name
        form.last_name.data = current_user.person.last_name
        form.gender.data = current_user.person.gender.value
    if form.validate_on_submit():
        app.logger.info(f"Form submitted for user {current_user.username}.")
        if current_user.person is None:
            app.logger.info(
                f"Creating profile for new user {current_user.username}.")
            cursor.add(
                db,
                Person,
                user_id=current_user.id,
                first_name=form.first_name.data,
                middle_name=form.middle_name.data,
                last_name=form.last_name.data,
                gender=GenderEnum(form.gender.data)
            )
            flash('Profile created successfully!', 'success')
            app.logger.info(
                f"Profile created for user {current_user.username}.")
        else:
            app.logger.info(
                f"Updating profile for user {current_user.username}.")
            update_person(db, current_user, form)
            flash('Profile updated successfully!', 'success')
            app.logger.info(
                f"Profile updated for user {current_user.username}.")

    return render_template(
        'user/edit_profile.html',
        user=current_user,
        form=form)


@bp.route('/address', methods=['GET', 'POST'])
@login_required
def address():
    """
    Render and process the user's address form.
    """
    app.logger.info(
        f"Rendering address page for user {current_user.username}.")

    return render_template(
        'user/address.html',
        addresses=current_user.addresses
    )


@bp.route('/add_address', methods=['GET', 'POST'])
@login_required
def add_address():
    """
    Render the add address page if user has less than two addresses.
    """
    app.logger.info(
        f"Rendering add address page for user {current_user.username}.")
    if current_user.addresses and len(current_user.addresses) >= 2:
        app.logger.info(
            f"User {current_user.username} already has two addresses.")
        flash('You have already added both permanent and current addresses.', 'info')
        return redirect(url_for('user.address'))
    form = UpsertAddressForm()
    if form.validate_on_submit():
        is_permanent = form.is_permanent.data
        if current_user.addresses:
            if any(addr.is_permanent == is_permanent for addr in current_user.addresses):
                app.logger.info(
                    f"User {current_user.username} attempted to add duplicate address type.")
                flash('You have already added this type of address.', 'warning')
                return redirect(url_for('user.address'))
        cursor.add(
            db,
            Address,
            user_id=current_user.id,
            is_permanent=is_permanent,
            first_line=form.first_line.data,
            second_line=form.second_line.data,
            pin_code=form.pin_code.data,
            state=form.state.data,
            country=form.country.data,
            landmark=form.landmark.data
        )
        flash('Address added successfully!', 'success')
        app.logger.info(f"Address added for user {current_user.username}.")
        return redirect(url_for('user.address'))
    return render_template(
        'user/add_address.html',
        form=form
    )


@bp.route('/edit_address/<int:address_id>', methods=['GET', 'POST'])
@login_required
def edit_address(address_id):
    """
    Render the edit address page for a specific address.
    """
    app.logger.info(
        f"Rendering edit address page for user {current_user.username}, address ID {address_id}.")
    address = cursor.query(db, Address, filter_by=True,
                           id=address_id, user_id=current_user.id).first()
    if not address:
        app.logger.warning(
            f"Address ID {address_id} not found for user {current_user.username}.")
        flash('Address not found.', 'danger')
        return redirect(url_for('user.address'))

    form = UpsertAddressForm()
    if request.method == 'GET':
        prefill_address_form(form, address)

    if form.validate_on_submit():
        if address.is_permanent != form.is_permanent.data:
            if len(current_user.addresses) >= 2:
                other_address = cursor.query(db, Address,
                                             filter_by=True, is_permanent=form.is_permanent.data,
                                             user_id=current_user.id).first()
                if other_address:
                    app.logger.info(
                        f"User {current_user.username} attempted to change to duplicate address type.")
                    app.logger.info(
                        f'The other address ID is {other_address.id}, is_permanent: {other_address.is_permanent}, has been changed to {address.is_permanent}')
                    other_address.is_permanent = address.is_permanent
                    db.session.commit()

        fill_address_from_form(address, form)

        db.session.commit()
        flash('Address updated successfully!', 'success')
        app.logger.info(
            f"Address ID {address_id} updated for user {current_user.username}.")
        return redirect(url_for('user.address'))

    return render_template(
        'user/edit_address.html',
        form=form,
        address=address
    )


@bp.route('/display_address/<int:address_id>')
@login_required
def display_address(address_id):
    """
    Render the display address page for a specific address.
    """
    app.logger.info(
        f"Rendering display address page for user {current_user.username}, address ID {address_id}.")
    address = cursor.query(db, Address, filter_by=True,
                           id=address_id, user_id=current_user.id).first()
    if not address:
        app.logger.warning(
            f"Address ID {address_id} not found for user {current_user.username}.")
        flash('Address not found.', 'danger')
        return redirect(url_for('user.address'))

    return render_template(
        'user/display_address.html',
        address=address
    )


@bp.route('/delete_address/<int:address_id>', methods=['POST'])
@login_required
def delete_address(address_id):
    """
    Render the delete address confirmation page and handle deletion.
    """
    app.logger.info(
        f"Rendering delete address page for user {current_user.username}, address ID {address_id}.")
    address = cursor.query(db, Address, filter_by=True,
                           id=address_id, user_id=current_user.id).first()
    if not address:
        app.logger.warning(
            f"Address ID {address_id} not found for user {current_user.username}.")
        flash('Address not found.', 'danger')

    if request.method == 'POST':
        cursor.delete(db, Address, id=address_id, user_id=current_user.id)
        flash('Address deleted successfully!', 'success')
        app.logger.info(
            f"Address ID {address_id} deleted for user {current_user.username}.")

    return redirect(url_for('user.address'))


@bp.route('/display_important_dates')
@login_required
def display_important_dates():
    """
    Render the important dates page for the user.
    """
    app.logger.info(
        f"Rendering important dates page for user {current_user.username}.")

    return render_template(
        'user/display_important_dates.html',
        important_dates=current_user.important_dates
    )


@bp.route('/add_important_date', methods=['GET', 'POST'])
@login_required
def add_important_date():
    """
    Render the add important date page.
    """
    app.logger.info(
        f"Rendering add important date page for user {current_user.username}.")

    form = UpsertImportantDateForm()
    form.date_type.choices = [(e.name, e.value) for e in ImportantDateTypeEnum]
    if form.validate_on_submit():
        cursor.add(
            db,
            ImportantDates,
            user_id=current_user.id,
            date_type=ImportantDateTypeEnum(form.date_type.data),
            date=form.date.data
        )
        flash('Important date added successfully!', 'success')
        app.logger.info(
            f"Important date added for user {current_user.username}.")
        return redirect(url_for('user.add_important_date'))
    return render_template(
        'user/add_important_date.html',
        form=form
    )


@bp.route('/edit_important_date/<int:date_id>', methods=['GET', 'POST'])
@login_required
def edit_important_date(date_id):
    """
    Render the edit important date page for a specific important date.
    """
    app.logger.info(
        f"Rendering edit important date page for user {current_user.username}, date ID {date_id}.")
    important_date = cursor.query(db, ImportantDates, filter_by=True,
                                  id=date_id, user_id=current_user.id).first()
    if not important_date:
        app.logger.warning(
            f"Important date ID {date_id} not found for user {current_user.username}.")
        flash('Important date not found.', 'danger')
        return redirect(url_for('user.display_important_dates'))

    form = UpsertImportantDateForm()
    form.date_type.choices = [(e.name, e.value) for e in ImportantDateTypeEnum]
    if request.method == 'GET':
        form.date_type.data = important_date.date_type.name
        form.date.data = important_date.date

    if form.validate_on_submit():
        important_date.date_type = ImportantDateTypeEnum(form.date_type.data)
        important_date.date = form.date.data
        db.session.commit()
        flash('Important date updated successfully!', 'success')
        app.logger.info(
            f"Important date ID {date_id} updated for user {current_user.username}.")
        return redirect(url_for('user.display_important_dates'))

    return render_template(
        'user/edit_important_date.html',
        form=form,
        important_date=important_date
    )


@bp.route('/delete_important_date/<int:date_id>', methods=['POST'])
@login_required
def delete_important_date(date_id):
    """
    Handle deletion of an important date.
    """
    app.logger.info(
        f"User {current_user.username} attempting to delete important date ID {date_id}.")
    important_date = cursor.query(db, ImportantDates, filter_by=True,
                                  id=date_id, user_id=current_user.id).first()
    if not important_date:
        app.logger.warning(
            f"Important date ID {date_id} not found for user {current_user.username}.")
        flash('Important date not found.', 'danger')
        return redirect(url_for('user.display_important_dates'))

    cursor.delete(db, ImportantDates, id=date_id, user_id=current_user.id)
    flash('Important date deleted successfully!', 'success')
    app.logger.info(
        f"Important date ID {date_id} deleted for user {current_user.username}.")
    return redirect(url_for('user.display_important_dates'))


@bp.route('/display_contact_details')
@login_required
def display_contact_details():
    """
    Render the contact details page for the user.
    """
    app.logger.info(
        f"Rendering contact details page for user {current_user.username}.")

    return render_template(
        'user/display_contact_details.html',
        contact_details=current_user.contact_details
    )


@bp.route('/add_contact_details', methods=['GET', 'POST'])
@login_required
def add_contact_details():
    """
    Render the add contact details page.
    """
    app.logger.info(
        f"Rendering add contact details page for user {current_user.username}.")
    form = UpsertContactDetailsForm()
    if form.validate_on_submit():
        cursor.add(
            db,
            ContactDetails,
            user_id=current_user.id,
            country_code=form.country_code.data,
            mobile_no=str(form.mobile_no.data),
            email=form.email.data
        )
        flash('Contact details added successfully!', 'success')
        app.logger.info(
            f"Contact details added for user {current_user.username}.")
        return redirect(url_for('user.display_contact_details'))
    return render_template('user/add_contact_details.html', form=form)

# Edit Contact Details


@bp.route('/edit_contact_details/<int:contact_id>', methods=['GET', 'POST'])
@login_required
def edit_contact_details(contact_id):
    """
    Render the edit contact details page for a specific contact.
    """
    app.logger.info(
        f"Rendering edit contact details page for user {current_user.username}, contact ID {contact_id}.")
    contact = cursor.query(db, ContactDetails, filter_by=True,
                           id=contact_id, user_id=current_user.id).first()
    if not contact:
        app.logger.warning(
            f"Contact details ID {contact_id} not found for user {current_user.username}.")
        flash('Contact details not found.', 'danger')
        return redirect(url_for('user.display_contact_details'))

    form = UpsertContactDetailsForm()
    if request.method == 'GET':
        form.country_code.data = contact.country_code
        form.mobile_no.data = int(contact.mobile_no)
        form.email.data = contact.email

    if form.validate_on_submit():
        contact.country_code = form.country_code.data
        contact.mobile_no = str(form.mobile_no.data)
        contact.email = form.email.data
        db.session.commit()
        flash('Contact details updated successfully!', 'success')
        app.logger.info(
            f"Contact details ID {contact_id} updated for user {current_user.username}.")
        return redirect(url_for('user.display_contact_details'))

    return render_template('user/edit_contact_details.html', form=form, contact=contact)

# Delete Contact Details


@bp.route('/delete_contact_details/<int:contact_id>', methods=['POST'])
@login_required
def delete_contact_details(contact_id):
    """
    Handle deletion of contact details.
    """
    app.logger.info(
        f"User {current_user.username} attempting to delete contact details ID {contact_id}.")
    contact = cursor.query(db, ContactDetails, filter_by=True,
                           id=contact_id, user_id=current_user.id).first()
    if not contact:
        app.logger.warning(
            f"Contact details ID {contact_id} not found for user {current_user.username}.")
        flash('Contact details not found.', 'danger')
        return redirect(url_for('user.display_contact_details'))

    cursor.delete(db, ContactDetails, id=contact_id, user_id=current_user.id)
    flash('Contact details deleted successfully!', 'success')
    app.logger.info(
        f"Contact details ID {contact_id} deleted for user {current_user.username}.")
    return redirect(url_for('user.display_contact_details'))


@bp.route('/display_relatives')
@login_required
def display_relatives():
    """
    Render the relatives page for the user.
    """
    app.logger.info(
        f"Rendering relatives page for user {current_user.username}.")
    relatives = cursor.query(
        db, Relatives, filter_by=True, user_id=current_user.id).all()
    relative_details = get_relative_details(db, User, relatives)
    return render_template(
        'user/display_relatives.html',
        relative_details=relative_details
    )


@bp.route('/add_relative', methods=['GET', 'POST'])
@login_required
def add_relative():
    """
    Render the add relative page.
    """
    app.logger.info(
        f"Rendering add relative page for user {current_user.username}.")
    form = UpsertRelativeForm()
    prefill_upsert_relative_form(db, User, current_user.id, form)
    if form.validate_on_submit():
        if (check_relative_constraints(db, User, Relatives, current_user, form)
                and check_validity_relation(db, User, Relatives, current_user,
                                            form.relative_user_id.data, form.relation_type.data)):
            add_relative_to_database(
                db, Relatives, RelativesTypeEnum, current_user, form)
            flash('Relative added successfully!', 'success')
            app.logger.info(
                f"Relative added for user {current_user.username}.")
            return redirect(url_for('user.add_relative'))
        else:
            app.logger.warning(
                f"User {current_user.username} attempted to add invalid relative relationship.")
            return redirect(url_for('user.display_relatives'))
    return render_template(
        'user/add_relative.html',
        form=form
    )


@bp.route('/delete_relative/<int:relative_user_id>', methods=['POST'])
@login_required
def delete_relative(relative_user_id):
    app.logger.info(
        f'Delete relative_user_id {relative_user_id} from current_user_id {current_user.id} relatives tables')
    result = delete_relative_from_database(
        db, User, Relatives, current_user, relative_user_id)
    if result:
        app.logger.info(
            f'Deleted successfully relative_user_id {relative_user_id} from current_user_id {current_user.id} relatives tables')
        flash('Deleted relative relation successfully!', 'success')
    else:
        app.logger.info(
            f'Delete unsuccessfull: relative_user_id {relative_user_id} from current_user_id {current_user.id} relatives tables')
    return redirect(url_for('user.display_relatives'))


