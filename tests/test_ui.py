class TestCommonUI:
    def test_home_page(self, client):
        response = client.get('/')
        assert b'Home' in response.data or b'home' in response.data

    def test_login_page(self, client):
        response = client.get('/login')
        assert b'Login' in response.data or b'login' in response.data
        assert b'Email' in response.data
        assert b'Password' in response.data

    def test_register_page(self, client):
        response = client.get('/register')
        assert b'Register' in response.data or b'register' in response.data
        assert b'Username' in response.data
        assert b'Email' in response.data
        assert b'Password' in response.data

    def test_dashboard_requires_login(self, client):
        response = client.get('/dashboard', follow_redirects=True)
        # Should redirect to login or home if not authenticated
        assert b'Login' in response.data or b'login' in response.data or b'Home' in response.data


class TestUserUI:
    def test_address_page_renders(self, client):
        client.post('/register', data={
            'username': 'uiuser',
            'email': 'uiuser@example.com',
            'password': 'pass'
        })
        client.post('/login', data={
            'email': 'uiuser@example.com',
            'password': 'pass',
        }, follow_redirects=True)
        response = client.get('/address')
        assert response.status_code == 200
        assert (b'Add Another Address' in response.data
                or (b'Edit' in response.data and b'Delete' in response.data))

    def test_add_address_page_renders(self, client):
        client.post('/register', data={
            'username': 'uiuser2',
            'email': 'uiuser2@example.com',
            'password': 'pass'
        })
        client.post('/login', data={
            'email': 'uiuser2@example.com',
            'password': 'pass',
        }, follow_redirects=True)
        response = client.get('/add_address')
        assert response.status_code == 200
        assert b'Address Line 1' in response.data
        assert b'Country' in response.data

    def test_edit_address_page_renders(self, client):
        client.post('/register', data={
            'username': 'uiuser3',
            'email': 'uiuser3@example.com',
            'password': 'pass'
        })
        client.post('/login', data={
            'email': 'uiuser3@example.com',
            'password': 'pass',
        }, follow_redirects=True)
        # Add address
        client.post('/add_address', data={
            'is_permanent': 'y',
            'first_line': 'Line',
            'second_line': '',
            'pin_code': '12345',
            'state': 'State',
            'country': 'Country',
            'landmark': ''
        }, follow_redirects=True)
        from family_tree.models import User
        user = User.query.filter_by(email='uiuser3@example.com').first()
        address_id = user.addresses[0].id
        response = client.get(f'/edit_address/{address_id}')
        assert response.status_code == 200
        assert b'Edit Address' in response.data
        assert b'Address Line 1' in response.data

    def test_important_dates_page_renders(self, client):
        client.post('/register', data={
            'username': 'uiuser4',
            'email': 'uiuser4@example.com',
            'password': 'pass'
        })
        client.post('/login', data={
            'email': 'uiuser4@example.com',
            'password': 'pass',
        }, follow_redirects=True)
        response = client.get('/display_important_dates')
        assert response.status_code == 200
        assert b'Important Dates' in response.data
        # Should show table or info message
        assert (
            b'<table' in response.data or b'No important dates found.' in response.data)
