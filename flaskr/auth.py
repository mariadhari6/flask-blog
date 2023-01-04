import functools

from flask import (
  Blueprint, flash, redirect, render_template,
  request, session, url_for, g
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

def not_logged_id(view):
  @functools.wraps(view)
  def wrapped_view(**kwargs):
    if g.user is not None:
      return redirect(url_for(('blog.index')))
    return view(**kwargs)
  return wrapped_view

@bp.route('/register', methods=['GET', 'POST'])
@not_logged_id
def register():
  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']

    db = get_db()
    error = None

    if not username:
      error = 'Username is required'
    elif not password:
      error = 'Password is required'

    if error is None:
      try:
        db.execute(
          "INSERT INTO user (username, password) VALUES (?, ?)",
          (username, generate_password_hash(password))
        )
        db.commit()
      except db.IntegrityError:
        error = f"User {username} is already registered"
      else:
        flash('Account created successfully')
        return redirect(url_for('auth.login'))
    flash(error)

  return render_template('auth/register.html')

@bp.route('/login', methods=["GET", "POST"])
@not_logged_id
def login():
  if request.method == 'POST':

    username = request.form['username']
    password = request.form['password']

    db = get_db()
    error = None
    user = db.execute(
      'SELECT * FROM user WHERE username = ?', (username,)
    ).fetchone()
    
    if user is None or not check_password_hash(user['password'], password):
      error = 'Incorrect username or password'
    if error is None:
      session.clear()
      session['user_id'] = user['id']
      return redirect(url_for('blog.index'))
    
    flash(error)
  return render_template('auth/login.html')

@bp.route('/logout')
def logout():
  session.clear()
  return redirect(url_for('auth.login'))

# guard login
def login_required(view):
  @functools.wraps(view)
  def wrapped_view(**kwargs):
    if g.user is None:
      return redirect(url_for('auth.login'))
    
    return view(**kwargs)
  return wrapped_view

@bp.before_app_request
def load_logged_in_user():
  user_id = session.get('user_id')
  db = get_db()

  if user_id is None:
    g.user = None
  else:
    g.user = db.execute(
      'SELECT * FROM user WHERE id = ?', (user_id,)
    ).fetchone()
  