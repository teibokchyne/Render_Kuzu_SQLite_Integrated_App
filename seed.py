from datetime import date

from family_tree import db, create_app, bcrypt

from family_tree.models import (
    User,
    GenderEnum,
    Person,
    Address,
    RelativesTypeEnum,
    Relatives,
    ImportantDates,
    ImportantDateTypeEnum,
    ContactDetails
)


def seed_database(app=None):
    if not app:
        app = create_app()

    with app.app_context():
        db.drop_all()
        db.create_all()

        # 1. Create users
        users = [
            User(
                username="alice",
                email="alice@example.com",
                password_hash=bcrypt.generate_password_hash(
                    "password123").decode('utf-8'),
                is_admin=True
            ),
            User(
                username="bob",
                email="bob@example.com",
                password_hash=bcrypt.generate_password_hash(
                    "password123").decode('utf-8'),
                is_admin=False
            ),
            User(
                username="charlie",
                email="charlie@example.com",
                password_hash=bcrypt.generate_password_hash(
                    "password123").decode('utf-8'),
                is_admin=False
            )
        ]

        for i in range(4, 24):  # Starts from user4 to user23
            users.append(
                User(
                    username=f"user{i}",
                    email=f"user{i}@example.com",
                    password_hash=bcrypt.generate_password_hash(
                        "password123").decode('utf-8'),
                    is_admin=False
                )
            )

        db.session.bulk_save_objects(users)
        db.session.commit()

        # 2. Fetch user IDs (after commit, so they have IDs assigned)
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

        for i in range(4, 24):
            persons.append(
                Person(
                    user_id=i,
                    gender=GenderEnum.MALE if i % 3 == 0 else GenderEnum.FEMALE if i % 3 == 1 else GenderEnum.OTHER,
                    first_name=f'person_user_no_{i}',
                    middle_name=None,
                    last_name="Random"
                )
            )

        db.session.bulk_save_objects(persons)
        db.session.commit()

        # 4. Create addresses
        addresses = [
            Address(
                user_id=alice.id,
                is_permanent=True,
                first_line="123 Maple Street",
                second_line="Apt 4B",
                pin_code=560001,
                state="Karnataka",
                country="India",
                landmark="Near Central Park"
            ),
            Address(
                user_id=bob.id,
                is_permanent=False,
                first_line="456 Oak Avenue",
                second_line=None,
                pin_code=110001,
                state="Delhi",
                country="India",
                landmark="Opposite City Mall"
            ),
            Address(
                user_id=charlie.id,
                is_permanent=True,
                first_line="789 Pine Road",
                second_line="Suite 202",
                pin_code=400001,
                state="Maharashtra",
                country="India",
                landmark="Next to Skyline Towers"
            )
        ]

        for i in range(4, 24):
            addresses.append(
                Address(
                    user_id=i,
                    is_permanent=True if i % 2 == 1 else False,
                    first_line=f"address_{i}_789 Pine Road",
                    second_line=f"address_{i}_Suite 202",
                    pin_code=400001,
                    state="Maharashtra",
                    country="India",
                    landmark="Next to Skyline Towers"
                )
            )

        db.session.bulk_save_objects(addresses)
        db.session.commit()

        # Fetch users
        alice = User.query.filter_by(username="alice").first()
        bob = User.query.filter_by(username="bob").first()
        charlie = User.query.filter_by(username="charlie").first()

        # Create important dates
        important_dates = [
            ImportantDates(
                user_id=alice.id,
                date_type=ImportantDateTypeEnum.BIRTH,
                date=date(1990, 5, 21)
            ),
            ImportantDates(
                user_id=bob.id,
                date_type=ImportantDateTypeEnum.BIRTH,
                date=date(1985, 8, 14)
            ),
            ImportantDates(
                user_id=charlie.id,
                date_type=ImportantDateTypeEnum.BIRTH,
                date=date(2020, 2, 29)
            )
        ]

        for i in range(4, 24):
            important_dates.append(
                ImportantDates(
                    user_id=i,
                    date_type=ImportantDateTypeEnum.BIRTH,
                    date=date(2000, 2, 29)
                )
            )

        # Insert into DB
        db.session.bulk_save_objects(important_dates)
        db.session.commit()

        # Create contact details
        contact_details = [
            ContactDetails(
                user_id=alice.id,
                country_code=91,
                mobile_no="9876543210",
                email="alice.contact@example.com"  # Optional override
            ),
            ContactDetails(
                user_id=bob.id,
                country_code=1,
                mobile_no="2025550181",
                email="bob.contact@example.com"
            ),
            ContactDetails(
                user_id=charlie.id,
                country_code=44,
                mobile_no="7700900900",
                email="charlie.contact@example.com"
            )
        ]

        # Insert into DB
        db.session.bulk_save_objects(contact_details)
        db.session.commit()

        # Create relationships and reverse relationships
        relationships = []


        # 3 -> 4: PARENT, 4 -> 3: CHILD
        relationships.append(Relatives(
            user_id=3,
            relative_user_id=4,
            relation_type=RelativesTypeEnum.PARENT
        ))
        relationships.append(Relatives(
            user_id=4,
            relative_user_id=3,
            relation_type=RelativesTypeEnum.CHILD
        ))

        # 5 -> 6: STEPPARENT, 6 -> 5: STEPCHILD
        relationships.append(Relatives(
            user_id=5,
            relative_user_id=6,
            relation_type=RelativesTypeEnum.STEPPARENT
        ))
        relationships.append(Relatives(
            user_id=6,
            relative_user_id=5,
            relation_type=RelativesTypeEnum.STEPCHILD
        ))

        # 11 <-> 12: EXSPOUSE (bidirectional)
        relationships.append(Relatives(
            user_id=11,
            relative_user_id=12,
            relation_type=RelativesTypeEnum.EXSPOUSE
        ))
        relationships.append(Relatives(
            user_id=12,
            relative_user_id=11,
            relation_type=RelativesTypeEnum.EXSPOUSE
        ))

        # For the rest, create some mixed parent-child relationships for demo

        for i in range(15, 23, 2):
            # i -> i+1: PARENT, i+1 -> i: CHILD
            relationships.append(Relatives(
                user_id=i,
                relative_user_id=i+1,
                relation_type=RelativesTypeEnum.PARENT
            ))
            relationships.append(Relatives(
                user_id=i+1,
                relative_user_id=i,
                relation_type=RelativesTypeEnum.CHILD
            ))
        
        # User 3 -> User 5 (PARENT), User 5 -> User 3 (CHILD)
        relationships.append(Relatives(
            user_id=3,
            relative_user_id=5,
            relation_type=RelativesTypeEnum.PARENT
        ))
        relationships.append(Relatives(
            user_id=5,
            relative_user_id=3,
            relation_type=RelativesTypeEnum.CHILD
        ))

        # User 3 -> User 6 (STEPPARENT), User 6 -> User 3 (STEPCHILD)
        relationships.append(Relatives(
            user_id=3,
            relative_user_id=6,
            relation_type=RelativesTypeEnum.STEPPARENT
        ))
        relationships.append(Relatives(
            user_id=6,
            relative_user_id=3,
            relation_type=RelativesTypeEnum.STEPCHILD
        ))

        # User 8 -> User 3 (CHILD -> PARENT)
        relationships.append(Relatives(
            user_id=8,
            relative_user_id=3,
            relation_type=RelativesTypeEnum.PARENT
        ))
        relationships.append(Relatives(
            user_id=3,
            relative_user_id=8,
            relation_type=RelativesTypeEnum.CHILD
        ))

        # User 9 -> User 3 (STEPCHILD -> STEPPARENT)
        relationships.append(Relatives(
            user_id=9,
            relative_user_id=3,
            relation_type=RelativesTypeEnum.STEPPARENT
        ))
        relationships.append(Relatives(
            user_id=3,
            relative_user_id=9,
            relation_type=RelativesTypeEnum.STEPCHILD
        ))

        # User 10 -> User 3 (CHILD -> PARENT)
        relationships.append(Relatives(
            user_id=10,
            relative_user_id=3,
            relation_type=RelativesTypeEnum.PARENT
        ))
        relationships.append(Relatives(
            user_id=3,
            relative_user_id=10,
            relation_type=RelativesTypeEnum.CHILD
        ))

        # Commit to DB
        db.session.bulk_save_objects(relationships)
        db.session.commit()
        print("SEEDING SUCCESSFULL!")

if __name__ == "__main__":
    seed_database()
