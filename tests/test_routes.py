import pytest

from sqlalchemy import or_ 

from flask_login import current_user

from seed import seed_database

from family_tree import db, bcrypt

from family_tree.models import (
    User,
    GenderEnum,
    Person,
    RelativesTypeEnum,
    Relatives,
    Address,
    ImportantDateTypeEnum,
    ImportantDates,
    ContactDetails
)


class TestCommonRoutes:
    def test_register_sucess(self, client):
        response = client.post('/register', data={
            'username': 'sampleuser',
            'email': 'sampleuser@example.com',
            'password': 'pass'
        }, follow_redirects=True)
        assert b'Registration successful' in response.data

    def test_register_failure_email(self, client):
        # register a user first
        response = client.post('/register', data={
            'username': 'sampleuser',
            'email': 'sampleuser@example.com',
            'password': 'pass'
        }, follow_redirects=True)

        # email already registered
        response = client.post('/register', data={
            'username': 'sampleuser2',
            'email': 'sampleuser@example.com',
            'password': 'pass'
        }, follow_redirects=True)
        # Check for error message or that register.html is rendered again
        assert b'Email already registered. Please log in.' in response.data  # Form is shown again

    def test_register_failure_username(self, client):
        # register a user first
        response = client.post('/register', data={
            'username': 'sampleuser',
            'email': 'sampleuser@example.com',
            'password': 'pass'
        }, follow_redirects=True)

        # email already registered
        response = client.post('/register', data={
            'username': 'sampleuser',
            'email': 'sampleuser2@example.com',
            'password': 'pass'
        }, follow_redirects=True)
        # Check for error message or that register.html is rendered again
        # Form is shown again
        assert b'Username already registered. Please use a different one.' in response.data

    def test_login_success(self, client, registered_user):
        response = client.post('/login', data={
            'email': registered_user.email,
            'password': 'pass',
            'remember': 'y'
        }, follow_redirects=True)
        assert b'Dashboard' in response.data or b'dashboard' in response.data

    def test_login_failure(self, client):
        response = client.post('/login', data={
            'email': 'test@test.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        assert b'Login Unsuccessful' in response.data

    def test_logout(self, client, registered_user):
        # First, log in
        client.post('/login', data={
            'email': registered_user.email,
            'password': 'pass',
            'remember': 'y'
        })

        response = client.get('/logout', follow_redirects=True)
        print(response.data.decode())
        assert b'Welcome to Your Digital Family' in response.data
        assert not current_user.is_authenticated

class TestUserRoutes:
    def create_users(self):
        # 1. Create users
        users = [
            User(
                username="alice",
                email="alice@example.com",
                password_hash=bcrypt.generate_password_hash("password123").decode('utf-8'),
                is_admin=True
            ),
            User(
                username="bob",
                email="bob@example.com",
                password_hash=bcrypt.generate_password_hash("password123").decode('utf-8'),
                is_admin=False
            ),
            User(
                username="charlie",
                email="charlie@example.com",
                password_hash=bcrypt.generate_password_hash("password123").decode('utf-8'),
                is_admin=False
            )
        ]

        db.session.bulk_save_objects(users)
        db.session.commit()

    def create_persons(self):
        # Make sure to call this function only if the following users exist already
        # Fetch user IDs 
        alice = User.query.filter_by(username="alice").first()
        bob = User.query.filter_by(username="bob").first()
        charlie = User.query.filter_by(username="charlie").first()

        # 3. Create persons
        persons = [
            Person(
                user_id=alice.id,
                gender=GenderEnum.FEMALE,
                first_name="Alice",
                middle_name="Marie",
                last_name="Anderson"
            ),
            Person(
                user_id=bob.id,
                gender=GenderEnum.MALE,
                first_name="Bob",
                middle_name=None,
                last_name="Brown"
            ),
            Person(
                user_id=charlie.id,
                gender=GenderEnum.OTHER,
                first_name="Charlie",
                middle_name="Lee",
                last_name="Campbell"
            )
        ]

        db.session.bulk_save_objects(persons)
        db.session.commit()

    def test_profile_creation(self, client):
        client.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'pass'
        })
        # First, log in
        client.post('/login', data={
            'email': 'newuser@example.com',
            'password': 'pass',
        }, follow_redirects=True)

        response = client.post('/edit_profile', data={
            'first_name': 'John',
            'middle_name': 'M',
            'last_name': 'Doe',
            'gender': 'MALE'
        })

        # Depending on redirect behavior
        assert response.status_code == 200 or response.status_code == 302
        assert b'Profile created successfully!' in response.data

    def test_profile_update(self, client):
        client.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'pass'
        })
        # First, log in
        client.post('/login', data={
            'email': 'newuser@example.com',
            'password': 'pass',
        }, follow_redirects=True)

        # Create initial profile
        client.post('/edit_profile', data={
            'first_name': 'John',
            'middle_name': 'M',
            'last_name': 'Doe',
            'gender': 'MALE'
        })

        response = client.post('/edit_profile', data={
            'first_name': 'Jane',
            'middle_name': 'A',
            'last_name': 'Smith',
            'gender': 'FEMALE'
        })

        # Depending on redirect behavior
        assert response.status_code == 200 or response.status_code == 302
        assert b'Profile updated successfully!' in response.data

    def test_address(self, client):
        client.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'pass'
        })
        # First, log in
        client.post('/login', data={
            'email': 'newuser@example.com',
            'password': 'pass',
        }, follow_redirects=True)

        # Now, access the address page
        response = client.get('/address')
        assert response.status_code == 200
        assert (b'Permanent Address' in response.data 
        or b'Current Address' in response.data
        or b'Add Another Address' in response.data)

    def test_add_address_success(self, client):
        client.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'pass'
        })
        # First, log in
        client.post('/login', data={
            'email': 'newuser@example.com',
            'password': 'pass',
        }, follow_redirects=True)
        # Now, add an address
        response = client.post('/add_address', data={
            'is_permanent': 'y',
            'first_line': '123 Main St',
            'second_line': 'Apt 4B',
            'pin_code': '12345',
            'state': 'State',
            'country': 'Country',
            'landmark': 'Near Park'
        }, follow_redirects=True)
        assert response.status_code == 200 or response.status_code == 302
        assert b'Address added successfully!' in response.data

    def test_add_address_success(self, client):
        client.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'pass'
        })
        # First, log in
        client.post('/login', data={
            'email': 'newuser@example.com',
            'password': 'pass',
        }, follow_redirects=True)
        # Now, add an address
        response = client.post('/add_address', data={
            'is_permanent': 'y',
            'first_line': '123 Main St',
            'second_line': 'Apt 4B',
            'pin_code': '12345',
            'state': 'State',
            'country': 'Country',
            'landmark': 'Near Park'
        }, follow_redirects=True)
        assert response.status_code == 200 or response.status_code == 302
        assert b'Address added successfully!' in response.data

    def test_add_address_failure_1(self, client):
        # Failure when trying to add more than two addresses
        client.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'pass'
        })
        # First, log in
        client.post('/login', data={
            'email': 'newuser@example.com',
            'password': 'pass',
        }, follow_redirects=True)

        # Now, add an address
        response = client.post('/add_address', data={
            'is_permanent': 'y',
            'first_line': '123 Main St',
            'second_line': 'Apt 4B',
            'pin_code': '12345',
            'state': 'State',
            'country': 'Country',
            'landmark': 'Near Park'
        }, follow_redirects=True)

        # Now, add a second address
        response = client.post('/add_address', data={
            'is_permanent': '',
            'first_line': '123 Main St',
            'second_line': 'Apt 4B',
            'pin_code': '12345',
            'state': 'State',
            'country': 'Country',
            'landmark': 'Near Park'
        }, follow_redirects=True)

        # Now try to add a third address using GET
        response = client.get('/add_address', follow_redirects=True)

        # Now, add a third address using POST
        response_2 = client.post('/add_address', data={
            'is_permanent': '',
            'first_line': '123 Main St',
            'second_line': 'Apt 4B',
            'pin_code': '12345',
            'state': 'State',
            'country': 'Country',
            'landmark': 'Near Park'
        }, follow_redirects=True)

        assert response.status_code == 200 or response.status_code == 302
        assert b'You have already added both permanent and current addresses.' in response.data
        assert response_2.status_code == 200 or response_2.status_code == 302
        assert b'You have already added both permanent and current addresses.' in response_2.data

    def test_add_address_failure_2(self, client):
        # Failure when trying to add address of a permanent type that already exists
        client.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'pass'
        })
        # First, log in
        client.post('/login', data={
            'email': 'newuser@example.com',
            'password': 'pass',
        }, follow_redirects=True)

        # Now, add an address
        client.post('/add_address', data={
            'is_permanent': 'y',
            'first_line': '123 Main St',
            'second_line': 'Apt 4B',
            'pin_code': '12345',
            'state': 'State',
            'country': 'Country',
            'landmark': 'Near Park'
        }, follow_redirects=True)

        # Now try to add a permanent address
        response = client.post('/add_address', data={
            'is_permanent': 'y',
            'first_line': '456 Another St',
            'second_line': 'Apt 5C',
            'pin_code': '67890',
            'state': 'Another State',
            'country': 'Another Country',
            'landmark': 'Near Mall'
        }, follow_redirects=True)

        assert response.status_code == 200 or response.status_code == 302
        assert b'You have already added this type of address.' in response.data

    def test_add_address_failure_3(self, client):
        # Failure when trying to add address of a current type that already exists
        client.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'pass'
        })
        # First, log in
        client.post('/login', data={
            'email': 'newuser@example.com',
            'password': 'pass',
        }, follow_redirects=True)

        # Now, add an address
        client.post('/add_address', data={
            'is_permanent': '',
            'first_line': '123 Main St',
            'second_line': 'Apt 4B',
            'pin_code': '12345',
            'state': 'State',
            'country': 'Country',
            'landmark': 'Near Park'
        }, follow_redirects=True)

        # Now try to add a permanent address
        response = client.post('/add_address', data={
            'is_permanent': '',
            'first_line': '456 Another St',
            'second_line': 'Apt 5C',
            'pin_code': '67890',
            'state': 'Another State',
            'country': 'Another Country',
            'landmark': 'Near Mall'
        }, follow_redirects=True)

        assert response.status_code == 200 or response.status_code == 302
        assert b'You have already added this type of address.' in response.data

    def test_edit_address_success(self, client):
        client.post('/register', data={
            'username': 'edituser',
            'email': 'edituser@example.com',
            'password': 'pass'
        })
        client.post('/login', data={
            'email': 'edituser@example.com',
            'password': 'pass',
        }, follow_redirects=True)
        # Add a permanent address
        client.post('/add_address', data={
            'is_permanent': 'y',
            'first_line': 'Old Line',
            'second_line': 'Old Second',
            'pin_code': '11111',
            'state': 'OldState',
            'country': 'OldCountry',
            'landmark': 'Old Landmark'
        }, follow_redirects=True)
        # Get address id
        from family_tree.models import User
        user = User.query.filter_by(email='edituser@example.com').first()
        address_id = user.addresses[0].id
        # Edit the address
        response = client.post(f'/edit_address/{address_id}', data={
            'is_permanent': 'y',
            'first_line': 'New Line',
            'second_line': 'New Second',
            'pin_code': '22222',
            'state': 'NewState',
            'country': 'NewCountry',
            'landmark': 'New Landmark'
        }, follow_redirects=True)
        assert b'Address updated successfully!' in response.data
        assert b'New Line' in response.data

    def test_edit_address_duplicate_type(self, client):
        from family_tree.models import Address

        client.post('/register', data={
            'username': 'edituser2',
            'email': 'edituser2@example.com',
            'password': 'pass'
        })
        client.post('/login', data={
            'email': 'edituser2@example.com',
            'password': 'pass',
        }, follow_redirects=True)
        # Add permanent and current addresses
        client.post('/add_address', data={
            'is_permanent': 'y',
            'first_line': 'Perm',
            'second_line': '',
            'pin_code': '11111',
            'state': 'State',
            'country': 'Country',
            'landmark': ''
        }, follow_redirects=True)
        client.post('/add_address', data={
            'is_permanent': '',
            'first_line': 'Curr',
            'second_line': '',
            'pin_code': '22222',
            'state': 'State',
            'country': 'Country',
            'landmark': ''
        }, follow_redirects=True)
        from family_tree.models import User
        user = User.query.filter_by(email='edituser2@example.com').first()
        perm_address_id = [a.id for a in user.addresses if a.is_permanent][0]
        curr_address_id = [
            a.id for a in user.addresses if not a.is_permanent][0]

        response = client.post(f'/edit_address/{curr_address_id}', data={
            'is_permanent': 'y',
            'first_line': 'Curr',
            'second_line': '',
            'pin_code': '22222',
            'state': 'State',
            'country': 'Country',
            'landmark': ''
        }, follow_redirects=True)

        # Current address should change type to permanent
        curr_address = Address.query.filter_by(id=curr_address_id).first()
        assert curr_address.is_permanent == True

        # Permanent address should change type to current
        perm_address = Address.query.filter_by(id=perm_address_id).first()
        assert perm_address.is_permanent == False

    def test_edit_address_not_found(self, client):
        client.post('/register', data={
            'username': 'edituser3',
            'email': 'edituser3@example.com',
            'password': 'pass'
        })
        client.post('/login', data={
            'email': 'edituser3@example.com',
            'password': 'pass',
        }, follow_redirects=True)
        # Try to edit a non-existent address
        response = client.post('/edit_address/9999', data={
            'is_permanent': 'y',
            'first_line': 'Does Not Exist',
            'second_line': '',
            'pin_code': '00000',
            'state': 'None',
            'country': 'None',
            'landmark': ''
        }, follow_redirects=True)
        assert b'Address not found.' in response.data

    def test_display_address_success(self, client):
        # Register and log in
        client.post('/register', data={
            'username': 'displayuser',
            'email': 'displayuser@example.com',
            'password': 'pass'
        })
        client.post('/login', data={
            'email': 'displayuser@example.com',
            'password': 'pass',
        }, follow_redirects=True)

        # Add an address
        client.post('/add_address', data={
            'is_permanent': 'y',
            'first_line': '123 Main St',
            'second_line': 'Apt 4B',
            'pin_code': '12345',
            'state': 'State',
            'country': 'Country',
            'landmark': 'Near Park'
        }, follow_redirects=True)

        # Get the address id
        from family_tree.models import User
        user = User.query.filter_by(email='displayuser@example.com').first()
        address_id = user.addresses[0].id

        # Display the address
        response = client.get(f'/display_address/{address_id}')
        assert response.status_code == 200
        assert b'Delete Address' in response.data
        assert b'123 Main St' in response.data

    def test_display_address_not_found(self, client):
        # Register and log in
        client.post('/register', data={
            'username': 'displayuser2',
            'email': 'displayuser2@example.com',
            'password': 'pass'
        })
        client.post('/login', data={
            'email': 'displayuser2@example.com',
            'password': 'pass',
        }, follow_redirects=True)

        # Try to display a non-existent address
        response = client.get('/display_address/9999', follow_redirects=True)
        assert b'Address not found.' in response.data or b'No Addresses Found' in response.data

    def test_delete_address_success(self, client):
        # Register and log in
        client.post('/register', data={
            'username': 'deleteuser',
            'email': 'deleteuser@example.com',
            'password': 'pass'
        })
        client.post('/login', data={
            'email': 'deleteuser@example.com',
            'password': 'pass',
        }, follow_redirects=True)

        # Add an address
        client.post('/add_address', data={
            'is_permanent': 'y',
            'first_line': '456 Delete St',
            'second_line': 'Apt 9C',
            'pin_code': '54321',
            'state': 'DeleteState',
            'country': 'DeleteCountry',
            'landmark': 'Delete Landmark'
        }, follow_redirects=True)

        # Get the address id
        from family_tree.models import User
        user = User.query.filter_by(email='deleteuser@example.com').first()
        address_id = user.addresses[0].id

        # Delete the address
        response = client.post(
            f'/delete_address/{address_id}', follow_redirects=True)
        assert response.status_code == 200 or response.status_code == 302
        assert b'Address deleted successfully!' in response.data

        # Confirm address is gone
        user = User.query.filter_by(email='deleteuser@example.com').first()
        assert not user.addresses

    def test_delete_address_not_found(self, client):
        # Register and log in
        client.post('/register', data={
            'username': 'deleteuser2',
            'email': 'deleteuser2@example.com',
            'password': 'pass'
        })
        client.post('/login', data={
            'email': 'deleteuser2@example.com',
            'password': 'pass',
        }, follow_redirects=True)

        # Try to delete a non-existent address
        response = client.post('/delete_address/9999', follow_redirects=True)
        assert b'Address not found.' in response.data or b'No Addresses Found' in response.data

    def test_add_important_date_success(self, client):
        from family_tree.models import ImportantDates
        import datetime
        # Register and log in
        client.post('/register', data={
            'username': 'dateuser',
            'email': 'dateuser@example.com',
            'password': 'pass'
        })
        client.post('/login', data={
            'email': 'dateuser@example.com',
            'password': 'pass',
        }, follow_redirects=True)

        # Add an important date
        response = client.post('/add_important_date', data={
            'date_type': 'BIRTH',
            'date': '2000-01-01',
        }, follow_redirects=True)
        assert response.status_code == 200 or response.status_code == 302
        assert b'Important date added successfully!' in response.data

        # Check that the date is in the database
        user = User.query.filter_by(email='dateuser@example.com').first()
        dates = ImportantDates.query.filter_by(user_id=user.id).all()
        assert any(d.date_type.name == 'BIRTH' and d.date ==
                   datetime.date(2000, 1, 1) for d in dates)

    def test_delete_important_date_success(self, client):
        from family_tree.models import ImportantDates
        import datetime
        # Register and log in
        client.post('/register', data={
            'username': 'deldateuser',
            'email': 'deldateuser@example.com',
            'password': 'pass'
        })
        client.post('/login', data={
            'email': 'deldateuser@example.com',
            'password': 'pass',
        }, follow_redirects=True)

        # Add an important date
        client.post('/add_important_date', data={
            'date_type': 'BIRTH',
            'date': '1999-12-31',
        }, follow_redirects=True)

        # Get the date id
        user = User.query.filter_by(email='deldateuser@example.com').first()
        date_obj = ImportantDates.query.filter_by(user_id=user.id).first()
        assert date_obj is not None
        date_id = date_obj.id

        # Delete the important date
        response = client.post(
            f'/delete_important_date/{date_id}', follow_redirects=True)
        assert response.status_code == 200 or response.status_code == 302
        assert b'Important date deleted successfully!' in response.data

        # Confirm it is deleted
        date_obj = ImportantDates.query.filter_by(id=date_id).first()
        assert date_obj is None

    def test_delete_important_date_not_found(self, client):
        # Register and log in
        client.post('/register', data={
            'username': 'deldateuser2',
            'email': 'deldateuser2@example.com',
            'password': 'pass'
        })
        client.post('/login', data={
            'email': 'deldateuser2@example.com',
            'password': 'pass',
        }, follow_redirects=True)

        # Try to delete a non-existent important date
        response = client.post(
            '/delete_important_date/9999', follow_redirects=True)
        assert response.status_code == 200 or response.status_code == 302
        assert b'Important date not found.' in response.data or b'No important dates found.' in response.data

    def test_edit_important_date_success(self, client):
        from family_tree.models import ImportantDates
        import datetime
        # Register and log in
        client.post('/register', data={
            'username': 'editdateuser',
            'email': 'editdateuser@example.com',
            'password': 'pass'
        })
        client.post('/login', data={
            'email': 'editdateuser@example.com',
            'password': 'pass',
        }, follow_redirects=True)

        # Add an important date
        client.post('/add_important_date', data={
            'date_type': 'BIRTH',
            'date': '1980-01-01',
        }, follow_redirects=True)

        # Get the date id
        user = User.query.filter_by(email='editdateuser@example.com').first()
        date_obj = ImportantDates.query.filter_by(user_id=user.id).first()
        assert date_obj is not None
        date_id = date_obj.id

        # Edit the important date
        response = client.post(f'/edit_important_date/{date_id}', data={
            'date_type': 'MARRIAGE',
            'date': '2005-05-05',
        }, follow_redirects=True)
        assert response.status_code == 200 or response.status_code == 302
        assert b'Important date updated successfully!' in response.data

        # Confirm update in database
        updated = ImportantDates.query.filter_by(id=date_id).first()
        assert updated is not None
        assert updated.date_type.name == 'MARRIAGE'
        assert updated.date == datetime.date(2005, 5, 5)

    def test_edit_important_date_not_found(self, client):
        # Register and log in
        client.post('/register', data={
            'username': 'editdateuser2',
            'email': 'editdateuser2@example.com',
            'password': 'pass'
        })
        client.post('/login', data={
            'email': 'editdateuser2@example.com',
            'password': 'pass',
        }, follow_redirects=True)

        # Try to edit a non-existent important date
        response = client.post('/edit_important_date/9999', data={
            'date_type': 'BIRTH',
            'date': '2020-01-01',
        }, follow_redirects=True)
        assert response.status_code == 200 or response.status_code == 302
        assert b'Important date not found.' in response.data or b'No important dates found.' in response.data

    def test_add_contact_details_success(self, client):
        from family_tree.models import ContactDetails
        # Register and log in
        client.post('/register', data={
            'username': 'contactuser',
            'email': 'contactuser@example.com',
            'password': 'pass'
        })
        client.post('/login', data={
            'email': 'contactuser@example.com',
            'password': 'pass',
        }, follow_redirects=True)

        # CASE 1: WHEN ALL FIELDS ARE FILLED
        # Add contact details
        response = client.post('/add_contact_details', data={
            'country_code': 91,
            'mobile_no': 9876543210,
            'email': 'contactuser@example.com',
        }, follow_redirects=True)
        assert response.status_code == 200 or response.status_code == 302
        assert b'Contact details added successfully!' in response.data

        # Check that the contact is in the database
        user = User.query.filter_by(email='contactuser@example.com').first()
        contacts = ContactDetails.query.filter_by(user_id=user.id).all()
        assert any(c.mobile_no == '9876543210' and c.email ==
                   'contactuser@example.com' for c in contacts)
        
        # CASE 2: WHEN ONLY MOBILE NO IS FILLED
        # Add contact details
        response_2 = client.post('/add_contact_details', data={
            'country_code': 91,
            'mobile_no': 9876523432,
        }, follow_redirects=True)
        assert response_2.status_code == 200 or response_2.status_code == 302
        assert b'Contact details added successfully!' in response_2.data

        # Check that the contact is in the database
        user = User.query.filter_by(email='contactuser@example.com').first()
        contacts = ContactDetails.query.filter_by(user_id=user.id).all()
        assert any(c.mobile_no == '9876523432' for c in contacts)

        # CASE 3: WHEN ONLY EMAIL FIELD IS FILLED
        # Add contact details
        response_3 = client.post('/add_contact_details', data={
            'email': 'contactuser_RANDOM@example.com',
        }, follow_redirects=True)
        assert response_3.status_code == 200 or response_3.status_code == 302
        assert b'Contact details added successfully!' in response_3.data

        # Check that the contact is in the database
        user = User.query.filter_by(email='contactuser@example.com').first()
        contacts = ContactDetails.query.filter_by(user_id=user.id).all()
        assert any(c.email == 'contactuser_RANDOM@example.com' for c in contacts)

    def test_edit_contact_details_success(self, client):
        from family_tree.models import ContactDetails
        # Register and log in
        client.post('/register', data={
            'username': 'editcontactuser',
            'email': 'editcontactuser@example.com',
            'password': 'pass'
        })
        client.post('/login', data={
            'email': 'editcontactuser@example.com',
            'password': 'pass',
        }, follow_redirects=True)

        # Add contact details
        client.post('/add_contact_details', data={
            'country_code': 91,
            'mobile_no': 1234567890,
            'email': 'editcontactuser@example.com',
        }, follow_redirects=True)

        # Get the contact id
        user = User.query.filter_by(
            email='editcontactuser@example.com').first()
        contact = ContactDetails.query.filter_by(user_id=user.id).first()
        assert contact is not None
        contact_id = contact.id

        # Edit the contact details
        response = client.post(f'/edit_contact_details/{contact_id}', data={
            'country_code': 1,
            'mobile_no': 5555555555,
            'email': 'newemail@example.com',
        }, follow_redirects=True)
        assert response.status_code == 200 or response.status_code == 302
        assert b'Contact details updated successfully!' in response.data

        # Confirm update in database
        updated = ContactDetails.query.filter_by(id=contact_id).first()
        assert updated is not None
        assert updated.country_code == 1
        assert updated.mobile_no == '5555555555'
        assert updated.email == 'newemail@example.com'

    def test_edit_contact_details_not_found(self, client):
        # Register and log in
        client.post('/register', data={
            'username': 'editcontactuser2',
            'email': 'editcontactuser2@example.com',
            'password': 'pass'
        })
        client.post('/login', data={
            'email': 'editcontactuser2@example.com',
            'password': 'pass',
        }, follow_redirects=True)

        # Try to edit a non-existent contact
        response = client.post('/edit_contact_details/9999', data={
            'country_code': 1,
            'mobile_no': 1111111111,
            'email': 'notfound@example.com',
        }, follow_redirects=True)
        assert response.status_code == 200 or response.status_code == 302
        assert b'Contact details not found.' in response.data or b'No contact details found.' in response.data

    def test_delete_contact_details_success(self, client):
        from family_tree.models import ContactDetails
        # Register and log in
        client.post('/register', data={
            'username': 'delcontactuser',
            'email': 'delcontactuser@example.com',
            'password': 'pass'
        })
        client.post('/login', data={
            'email': 'delcontactuser@example.com',
            'password': 'pass',
        }, follow_redirects=True)

        # Add contact details
        client.post('/add_contact_details', data={
            'country_code': 91,
            'mobile_no': 2222222222,
            'email': 'delcontactuser@example.com',
        }, follow_redirects=True)

        # Get the contact id
        user = User.query.filter_by(email='delcontactuser@example.com').first()
        contact = ContactDetails.query.filter_by(user_id=user.id).first()
        assert contact is not None
        contact_id = contact.id

        # Delete the contact details
        response = client.post(
            f'/delete_contact_details/{contact_id}', follow_redirects=True)
        assert response.status_code == 200 or response.status_code == 302
        assert b'Contact details deleted successfully!' in response.data

        # Confirm it is deleted
        deleted = ContactDetails.query.filter_by(id=contact_id).first()
        assert deleted is None

    def test_delete_contact_details_not_found(self, client):
        # Register and log in
        client.post('/register', data={
            'username': 'delcontactuser2',
            'email': 'delcontactuser2@example.com',
            'password': 'pass'
        })
        client.post('/login', data={
            'email': 'delcontactuser2@example.com',
            'password': 'pass',
        }, follow_redirects=True)

        # Try to delete a non-existent contact
        response = client.post(
            '/delete_contact_details/9999', follow_redirects=True)
        assert response.status_code == 200 or response.status_code == 302
        assert b'Contact details not found.' in response.data or b'No contact details found.' in response.data

    def test_add_relative_success(self, client):
        # Create two users with profiles

        # Create user
        client.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'pass'
        })

        # Login
        client.post('/login', data={
            'email': 'newuser@example.com',
            'password': 'pass',
        }, follow_redirects=True)

        # Create profile
        client.post('/edit_profile', data={
            'first_name': 'John',
            'middle_name': 'M',
            'last_name': 'Doe',
            'gender': 'MALE'
        })

        # Logout
        client.get('/logout')

        # Create second user
        client.post('/register', data={
            'username': 'newuser2',
            'email': 'newuser2@example.com',
            'password': 'pass'
        })

        # Login as second user
        client.post('/login', data={
            'email': 'newuser2@example.com',
            'password': 'pass',
        }, follow_redirects=True)

        # Create profile for second user
        client.post('/edit_profile', data={
            'first_name': 'Jane',
            'middle_name': 'M',
            'last_name': 'Doe',
            'gender': 'FEMALE'
        })

        response = client.post('/add_relative', data={
            'relative_user_id' : 1,
            'relation_type' : 'PARENT'
        }, follow_redirects=True)

        # print(response.data.decode())
        assert response.status_code == 200 or response.status_code == 302
        assert b'Relative added successfully!' in response.data

        # Make sure that the relationship created was correct
        relation = Relatives.query.filter_by(id=1).first()
        assert relation is not None
        assert relation.user_id==2 
        assert relation.relative_user_id == 1
        assert relation.relation_type.value == 'PARENT'

        # Make sure that the reverse relationship created was correct
        reverse_relation = Relatives.query.filter_by(id=2).first()
        assert reverse_relation is not None 
        assert reverse_relation.user_id == 1
        assert reverse_relation.relative_user_id == 2
        assert reverse_relation.relation_type.value == 'CHILD'

    def test_delete_relatives(self, client):
        self.create_users()
        self.create_persons()

        # TEST 1: WHEN THE RELATION EXISTS
        rel1 = Relatives(user_id=2, relative_user_id=3, relation_type='PARENT')
        rev_rel1 = Relatives(user_id=3, relative_user_id=2, relation_type='CHILD')
        db.session.add(rel1)
        db.session.add(rev_rel1)
        db.session.commit() 

        relations = Relatives.query.all() 
        # Make sure relations were created
        assert len(relations) == 2
        
        # Login user
        bob = User.query.filter_by(id=2).first()
        client.post('/login', data={
            'email' : bob.email,
            'password' : 'password123'
        }, follow_redirects = True)
        response = client.post('/delete_relative/3', follow_redirects = True)
        client.get('/logout', follow_redirects = True)

        assert response.status_code == 200 or response.status_code == 302
        assert b'Deleted relative relation successfully!' in response.data

        # TEST 2: WHEN RELATION DOES NOT EXIST
        client.post('/login', data={
            'email' : bob.email,
            'password' : 'password123'
        }, follow_redirects = True)
        response = client.post('/delete_relative/2', follow_redirects = True)

        assert response.status_code == 200 or response.status_code == 302
        assert b'Could not find relation with relative user id' in response.data

class TestAdminRoutes:
    def test_delete_user(self, client, app):
        seed_database(app)
        client.post('/login', data={
            'email':'alice@example.com',
            'password':'password123'
        }, follow_redirects = True)

        # Check that the user exists in all tables
        user = User.query.filter_by(id=3).all()
        assert len(user) != 0

        person = Person.query.filter_by(user_id=3).all()
        assert len(person) != 0

        address = Address.query.filter_by(user_id=3).all()
        assert len(address) != 0

        contact_details = ContactDetails.query.filter_by(user_id=3).all()
        assert len(contact_details) != 0

        important_dates = ImportantDates.query.filter_by(user_id=3).all()
        assert len(important_dates) != 0

        relatives = Relatives.query.filter(
            or_(Relatives.user_id == 3, Relatives.relative_user_id == 3)
        ).all()
        assert len(relatives) != 0       

        # Delete user. Make sure that all corresponding entries in other tables are deleted.
        response = client.post('/admin/delete_user/3', follow_redirects = True)

        assert response.status_code == 200 or response.status_code == 302
        assert b'Deleted Successfully!' in response.data

        user = User.query.filter_by(id=3).all()
        assert len(user) == 0

        person = Person.query.filter_by(user_id=3).all()
        assert len(person) == 0

        address = Address.query.filter_by(user_id=3).all()
        assert len(address) == 0

        contact_details = ContactDetails.query.filter_by(user_id=3).all()
        assert len(contact_details) == 0

        important_dates = ImportantDates.query.filter_by(user_id=3).all()
        assert len(important_dates) == 0

        relatives = Relatives.query.filter(
            or_(Relatives.user_id == 3, Relatives.relative_user_id == 3)
        ).all()
        assert len(relatives) == 0

