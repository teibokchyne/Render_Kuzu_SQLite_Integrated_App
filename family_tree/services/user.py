import secrets
import os

from PIL import Image

from flask import (
    flash,
    url_for,
    current_app as app
)

from family_tree.cursor import Cursor

cursor = Cursor()


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_filename = random_hex + f_ext
    picture_path = os.path.join(
        app.root_path, 'static/profile_pictures', picture_filename)

    # Resize image before saving
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)

    # Save the picture
    i.save(picture_path)

    app.logger.info(f'Save picture to static/profile_pictures')
    return picture_filename


def get_profile_picture(db, picture_table, user_id):
    picture_filename = cursor.query(
        db, picture_table, filter_by=True, user_id=user_id).first()
    return picture_filename


def update_profile_picture(db, picture_table, user, picture_filename):
    # If user already has a profile picture, delete the current picture in the static folder
    if user.profile_picture:
        fn = user.profile_picture.picture_filename
        picture_path = os.path.join(
            app.root_path, 'static/profile_pictures', fn)
        os.remove(picture_path)
        app.logger.info(f'Remove old profile picture of user {user.username}')

        # Change profile picture filename in database
        user.profile_picture.picture_filename = picture_filename
        db.session.commit()
        app.logger.info(
            f'Change profile picture filename of user {user.username}')
    else:
        cursor.add(db, picture_table, user_id=user.id,
                   picture_filename=picture_filename)
        app.logger.info(f'Add profile picture for user {user.username}')


def update_person(db, user, form):
    if form.first_name.data is not None:
        user.person.first_name = form.first_name.data
    if form.middle_name.data is not None:
        user.person.middle_name = form.middle_name.data
    if form.last_name.data is not None:
        user.person.last_name = form.last_name.data
    if form.gender.data is not None:
        user.person.gender = form.gender.data
    db.session.commit()


def prefill_address_form(form, address):
    form.is_permanent.data = address.is_permanent
    form.first_line.data = address.first_line
    form.second_line.data = address.second_line
    form.pin_code.data = address.pin_code
    form.state.data = address.state
    form.country.data = address.country
    form.landmark.data = address.landmark


def fill_address_from_form(address, form):
    address.is_permanent = form.is_permanent.data
    address.first_line = form.first_line.data
    address.second_line = form.second_line.data
    address.pin_code = form.pin_code.data
    address.state = form.state.data
    address.country = form.country.data
    address.landmark = form.landmark.data


def get_relative_details(db, user_table, relatives):
    relative_details = []
    for rel in relatives:
        relative_user = cursor.query(
            db, user_table, filter_by=True, id=rel.relative_user_id).first()
        person = relative_user.person
        if relative_user.profile_picture:
            profile_picture_url = url_for(
                'static', filename=f'profile_pictures/{relative_user.profile_picture.picture_filename}')
        else:
            profile_picture_url = url_for(
                'static', filename='profile_pictures/default.jpg'
            )
        if person:
            relative_details.append({
                'first_name': person.first_name,
                'middle_name': person.middle_name,
                'last_name': person.last_name,
                'relationship': rel.relation_type.value,
                'relative_user_id': rel.relative_user_id,
                'profile_picture_url': profile_picture_url
            })
    return relative_details


def prefill_upsert_relative_form(db, user_table, user_id, form):
    all_users = cursor.query(db, user_table, filter_by=False).all()
    form.relative_user_id.choices = [
        (u.id, f'{u.person.first_name} {u.person.last_name}')
        for u in all_users
        if u.id != user_id and u.person is not None
    ]
    form.relation_type.choices = [
        ('PARENT', 'PARENT'),
        ('STEPPARENT', 'STEPPARENT'),
        ('CHILD', 'CHILD'),
        ('STEPCHILD', 'STEPCHILD'),
        ('SPOUSE', 'SPOUSE'),
        ('EXSPOUSE', 'EXSPOUSE')
    ]


def check_relative_constraints(db, user_table, relatives_table, user, form):
    # Check if the relative exists
    relative_user = cursor.query(
        db, user_table, filter_by=True, id=int(form.relative_user_id.data)).first()
    if not relative_user:
        app.logger.warning("Relative user not found.")
        flash("The selected relative does not exist.", "danger")
        return False

    # Check if the user is trying to add themselves as a relative
    if relative_user and relative_user.id == user.id:
        app.logger.warning("User attempted to add themselves as a relative.")
        flash("You cannot add yourself as a relative.", "danger")
        return False

    # Check for duplicate relationships. There can only be one relationship between two users in one direction.
    existing_relation = cursor.query(
        db,
        relatives_table,
        filter_by=True,
        user_id=user.id,
        relative_user_id=int(form.relative_user_id.data)).first()
    if existing_relation:
        app.logger.warning(
            "User attempted to add more than one relationship to a relative.")
        flash("This relationship already exists.", "danger")
        return False

    # Check that both user profiles exist
    if not user.person or not relative_user.person:
        app.logger.warning(
            "One or both of the users does not have a complete profile.")
        flash(
            "Both users must have complete profiles to establish a relationship.", "danger")
        return False

    return True


def check_validity_relation(db, user_table, relatives_table, user, relative_user_id, relation_type):
    """
        This function assumes that 
        1. both user and relative exist 
        2. both user and relative profiles are created
        3. no previous relationship exists between user and relative
        4. user and relative are different

        Returns:
            Bool
    """
    relative = cursor.query(db, user_table, filter_by=True,
                            id=relative_user_id).first()
    if not relative:
        app.logger.warning(
            f'relative user id {relative_user_id} does not exist')
        return False

    # Checks for relation_type PARENT
    if relation_type == 'PARENT':
        parents = cursor.query(db, relatives_table, filter_by=True,
                               user_id=user.id, relation_type='PARENT').all()
        # Check if there are currently no parents
        if not parents:
            app.logger.info(f'user {user.id} has no parents currently added')
            return True
        # Check if there already exists two parents
        if len(parents) >= 2:
            app.logger.warning(f'user {user.id} already has two parents')
            flash('User already has two parents', 'danger')
            return False

        # Check if father already exists
        parent = cursor.query(db, user_table, filter_by=True,
                              id=parents[0].relative_user_id).first().person
        if parent.gender.value == 'MALE' and relative.person.gender.value == 'MALE':
            app.logger.warning(
                f'user {user.id} tried to add a father when one already exists')
            flash(
                'Cannot add parent as parent of the same gender already exists', 'danger')
            return False

        # Check if mother already exists
        if parent.gender.value == 'FEMALE' and relative.person.gender.value == 'FEMALE':
            app.logger.warning(
                f'user {user.id} tried to add a father when one already exists')
            flash(
                'Cannot add parent as parent of the same gender already exists', 'danger')
            return False

    # Check for relation_type 'SPOUSE'
    elif relation_type == 'SPOUSE':
        spouse = cursor.query(
            db, relatives_table, filter_by=True, user_id=user.id, relation_type='SPOUSE').first()
        if not spouse:
            app.logger.info(f'No spouse found for user {user.id}')
            return True
        else:
            app.logger.info(f'user {user.id} already has a spouse')
            flash('Cannot add more than one spouse', 'danger')
            return False
    return True


def add_relative_to_database(db, relative_table, relative_enum, user, form):
    cursor.add(
        db,
        relative_table,
        user_id=user.id,
        relative_user_id=int(form.relative_user_id.data),
        relation_type=relative_enum(form.relation_type.data)
    )
    cursor.add(
        db,
        relative_table,
        user_id=int(form.relative_user_id.data),
        relative_user_id=user.id,
        relation_type=relative_enum(
            relative_table.get_reverse_relation(form.relation_type.data)
        )
    )
    app.logger.info(f"Relative added for user {user.username}.")


def delete_relative_from_database(db, user_table, relatives_table, user, relative_user_id):
    app.logger.info(
        f'Attempt to delete relative {relative_user_id} of user {user.id}')
    relation = cursor.query(db, relatives_table, filter_by=True,
                            user_id=user.id, relative_user_id=relative_user_id).first()
    if not relation:
        app.logger.info(
            f'Could not find relative of user {user.id} with relative user id {relative_user_id}')
        flash(
            f'Could not find relation with relative user id {relative_user_id}')
        return False
    else:
        reverse_relation = cursor.query(
            db, relatives_table, filter_by=True, user_id=relative_user_id, relative_user_id=user.id).first()
        if not reverse_relation:
            app.logger.info(
                f'Could not find reverse relation from relative {relative_user_id} to user {user.id}')
        else:
            cursor.delete(db, relatives_table,
                          user_id=relative_user_id, relative_user_id=user.id)
            app.logger.info(
                f'Successfully deleled reverse relation from relative {relative_user_id} to user {user.id}')
        cursor.delete(db, relatives_table, user_id=user.id,
                      relative_user_id=relative_user_id)
        app.logger.info(
            f'Successfully deleled relation from user {user.id} to relative {relative_user_id}')
        return True
