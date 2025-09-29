
import pytest

import family_tree

from family_tree import create_app, db as _db
from family_tree.models import User, Person
from tests.testconfig import TestConfig

@pytest.fixture()
def app():
    app = create_app(config_class=TestConfig)

    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def db(app):
    return _db

@pytest.fixture()
def registered_user(client):
    client.post('/register', data={
        'username': 'sampleuser',
        'email': 'sampleuser@example.com',
        'password': 'pass'
    }, follow_redirects=True)
    return User.query.filter_by(email='sampleuser@example.com').first()

@pytest.fixture()
def logged_in_client(client, registered_user):
    client.post('/login', data={
        'email': registered_user.email,
        'password': 'pass'
    }, follow_redirects=True)
    return client
