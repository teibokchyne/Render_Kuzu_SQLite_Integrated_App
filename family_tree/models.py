from datetime import datetime
import enum

from flask_login import UserMixin

from family_tree import db, bcrypt


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    profile_picture = db.relationship(
        'Picture', backref='user', uselist=False, cascade='all, delete-orphan')
    person = db.relationship('Person', backref='user',
                             uselist=False, cascade='all, delete-orphan')
    addresses = db.relationship(
        'Address', backref='user', lazy=True, cascade='all, delete-orphan')
    important_dates = db.relationship(
        'ImportantDates', backref='user', lazy=True, cascade='all, delete-orphan')
    contact_details = db.relationship(
        'ContactDetails', backref='user', lazy=True, cascade='all, delete-orphan')

    # This user is the source of the relationship (user_id)
    relatives = db.relationship(
        'Relatives',
        foreign_keys='Relatives.user_id',
        backref='user',
        cascade='all, delete-orphan',
        lazy=True
    )

    # This user is the target of the relationship (relative_user_id)
    relatives_of = db.relationship(
        'Relatives',
        foreign_keys='Relatives.relative_user_id',
        backref='relative_user',
        cascade='all, delete-orphan',
        lazy=True
    )

    def create_password_hash(self, password):
        self.password_hash = bcrypt.generate_password_hash(
            password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    # mobile_numbers = db.relationship('MobileNumber', backref='person', lazy=True, cascade='all, delete-orphan')
    # education = db.relationship('Education', backref='person', lazy=True, cascade='all, delete-orphan')
    # records = db.relationship('Record', backref='person', lazy=True, cascade='all, delete-orphan')
    # additional_info = db.relationship('AdditionalInfo', backref='person', lazy=True, cascade='all, delete-orphan', uselist=False)
    # photos = db.relationship('Photos', backref='person', lazy=True, cascade='all, delete-orphan')


class Picture(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    picture_filename = db.Column(db.String(100), nullable=False)

class GenderEnum(enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"

# Main Person entity


class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    gender = db.Column(db.Enum(GenderEnum), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    middle_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Person {self.first_name} {self.last_name}>'


class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_permanent = db.Column(db.Boolean, nullable=False)
    first_line = db.Column(db.String(255), nullable=False)
    second_line = db.Column(db.String(255))
    pin_code = db.Column(db.Integer, nullable=False)
    state = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    landmark = db.Column(db.String(255))

    def __repr__(self):
        return f'<Address {self.first_line}, {self.state}, {self.country}>'


class ImportantDateTypeEnum(enum.Enum):
    BIRTH = "BIRTH"
    DEATH = "DEATH"
    MARRIAGE = "MARRIAGE"


class ImportantDates(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_type = db.Column(db.Enum(ImportantDateTypeEnum),
                          nullable=False)  # e.g., Birth, Anniversary
    date = db.Column(db.Date, nullable=False)


class ContactDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    country_code = db.Column(db.Integer)
    mobile_no = db.Column(db.String(15))
    email = db.Column(db.String(120))


class RelativesTypeEnum(enum.Enum):
    PARENT = "PARENT"
    STEPPARENT = "STEPPARENT"
    CHILD = "CHILD"
    STEPCHILD = "STEPCHILD"
    SIBLING = "SIBLING"
    HALFSIBLING = "HALFSIBLING"
    STEPSIBLING = "STEPSIBLING"
    SPOUSE = "SPOUSE"
    EXSPOUSE = "EXSPOUSE"


class Relatives(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    relative_user_id = db.Column(
        db.Integer, db.ForeignKey('user.id'), nullable=False)
    # e.g., 'parent', 'sibling', 'child'
    relation_type = db.Column(db.Enum(RelativesTypeEnum), nullable=False)

    # Reverse mapping for gender-neutral relationships
    REVERSE_RELATIONSHIP_MAP = {
        'PARENT': 'CHILD',
        'STEPPARENT': 'STEPCHILD',
        'CHILD': 'PARENT',
        'STEPCHILD': 'STEPPARENT',
        'SIBLING': 'SIBLING',
        'HALFSIBLING': 'HALFSIBLING',
        'STEPSIBLING': 'STEPSIBLING',
        'SPOUSE': 'SPOUSE',
        'EXSPOUSE': 'EXSPOUSE',
        'UNKNOWN': 'UNKNOWN'
    }

    @classmethod
    def get_reverse_relation(cls, relation_type):
        if relation_type not in Relatives.REVERSE_RELATIONSHIP_MAP:
            return "UNKNOWN"
        return Relatives.REVERSE_RELATIONSHIP_MAP[relation_type]
