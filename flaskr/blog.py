import functools

from flask import (
  Blueprint, flash, g, redirect, render_template,
  request, session, url_for, abort
)

from werkzeug.security import generate_password_hash, check_password_hash

from flaskr.db import get_db
from flaskr.auth import login_required

bp = Blueprint('blog', __name__, url_prefix='/blog')

def get_post(id, check_author=None):
  db = get_db()
  post = db.execute(
    'SELECT p.id, title, body, created, author_id, username'
    ' FROM post p JOIN user u ON p.author_id=u.id'
    ' WHERE p.id=?',
    (id,)
  ).fetchone()

  if post is None:
    abort(404, f"Post id {id} doesn't exist.")
  
  if check_author and post['author_id'] != g.user['id']:
    abort(403)
  
  return post
    

@bp.route("/")
def index():
  db = get_db()
  posts = db.execute(
    'SELECT p.id, title , body, created, author_id, username'
    ' FROM post p JOIN user u ON p.author_id = u.id'
    ' ORDER BY created DESC'
  ).fetchall()
  return render_template("blog/index.html", posts=posts)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
  if request.method == 'POST':
    title = request.form['title']  
    body = request.form['body']

    db = get_db()
    error = None

    try:
      db.execute(
        'INSERT INTO post (title, body, author_id)'
        ' VALUES (?, ?, ?)',
        (title, body, g.user['id'])
      )
      db.commit()
    except db.IntegrityError:
      error = 'Failed to create post'
    else:
      return redirect(url_for('blog.index'))
    flash(error)
  return render_template('blog/create.html')

@bp.route('/update/<int:id>', methods=["GET", "POST"])
@login_required
def update(id):
  post = get_post(id, True)
  if request.method == 'POST':
    title = request.form['title']
    body = request.form['body']

    db = get_db()
    error = None

    try:
      db.execute(
        'UPDATE post SET title = ?, body = ?'
        ' WHERE id = ?',
        (title, body, id)
      )
      db.commit()
    except db.IntegrityError:
      error = "Failed to update post"
    else:
      return redirect(url_for('blog.index'))
    
    flash(error)

  return render_template('blog/update.html', post=post)

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
  get_post(id, True)
  db = get_db()

  try:
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
  except:
    message = 'Failed to delete post'
  else:
    message = 'Success to delete post'
  
  flash(message)
  return redirect(url_for('blog.index'))
  