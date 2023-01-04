import pytest
from flaskr.db import get_db

def test_index(client, auth):
  response = client.get('/blog/')
  assert b"Login" in response.data
  assert b"Register" in response.data

  auth.login()
  response = client.get('/blog/')
  assert b"Log Out" in response.data
  assert b"test title" in response.data
  assert b"by test" in response.data
  assert b"test\nbody" in response.data
  assert b"href='/update/1'" in response.data



@pytest.mark.parametrize('path', (
  '/create',
  '/update/1',
  'delete/1'
))
def test_login_required(client, path):
  response = client.post(path)
  assert response.headers['Location'] == '/auth/login'





