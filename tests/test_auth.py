import pytest
from flask import g, session
from flaskr.db import get_db

def test_register(client, app):
  # Step 1
  assert client.get('/auth/register').status_code == 200
  
  # Step 2
  response = client.post(
    '/auth/register',
    data={'username': 'firman123', 'password': 'firman123'}
  )
  assert response.headers["Location"] == '/auth/login'

  with app.app_context():
    assert get_db().execute(
      "SELECT * FROM user WHERE username = 'firman123'"
    ).fetchone() is not None


@pytest.mark.parametrize(('username', 'password', 'message'), (
  ('', '', b'Username is required.'),
  ('a', '', b'Password is required.'),
  ('test', 'test', b'already registered'),
))
def test_regiser_validate_input(client, username, password, message):
  response = client.post(
    '/auth/register',
    data={'username': username, 'password': password}
  )
  assert message in response.data

def test_logout(client, auth):
  auth.login()

  with client:
    auth.logout()
    assert 'user_id' not in session

@pytest.mark.parametrize('path', (
  '/'
))
def test_not_logged_in(client, path):
  response = client.get(path)
  assert response.headers['Location'] == '/blog/'

def test_author_required(app, client, auth):
  # change the post author to another user
  with app.app_context():
    db = get_db()
    db.execute('UPDATE post SET author_id = 2 WHERE id = 1')
    db.commit()
  
  auth.login()

  # Current user can't modify other user's post
  assert client.post('/update/1').status_code == 403
  assert client.post('/delete/1').status_code == 403

  # Current user doesn't see edit link
  assert b'href="/update/1"' not in client.get('/blog/').data

@pytest.mark.parametrize('path', (
  'update/2',
  'delete/2'
))
def test_exists_required(client, auth, path):
  auth.login()
  assert client.post(path).status_code == 404

def test_create(client, auth, app):
  auth.login()
  assert client.get('/create').status_code == 200
  client.post('/create', data={'title': 'created', 'body': ''})

  with app.app_context():
    db = get_db()
    count = db.execute('SELECT COUNT(id) FROM post').fetchone()[0]
    assert count == 2

def test_update(client, auth, app):
    auth.login()
    assert client.get('/update/1').status_code == 200
    client.post('/update/1', data={'title': 'updated', 'body': ''})

    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM post WHERE id = 1').fetchone()
        assert post['title'] == 'updated'

@pytest.mark.parametrize('path', (
    '/create',
    '/update/1',
))
def test_create_update_validate(client, auth, path):
    auth.login()
    response = client.post(path, data={'title': '', 'body': ''})
    assert b'Title is required.' in response.data

def test_delete(client, auth, app):
    auth.login()
    response = client.post('/delete/1')
    assert response.headers["Location"] == "/blog/"

    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM post WHERE id = 1').fetchone()
        assert post is None