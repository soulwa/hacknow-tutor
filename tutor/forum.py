import pytz
from datetime import datetime

from flask import Blueprint, request, g, abort, render_template, redirect, url_for

from .auth import login_required
from .db import get_db, get_dict_cursor
from .md import md_to_html

bp = Blueprint('forum', __name__)

@bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
  db = get_db()
  cur = get_dict_cursor(db)
  user = g.user

  if user is None:
    abort(403, 'please clear your session data!')

  if request.method == 'GET':

    lang = user['lang']
    cur.execute(
      "SELECT posts.*, users.username FROM posts JOIN users ON posts.user_id = users.id WHERE posts.lang = %s \
      ORDER BY created DESC;", 
      (lang,)
    )
    posts = cur.fetchall()

    return render_template('forum/index.html', posts=posts)
  
  elif request.method == 'POST':
    lang = user['lang']
    title = request.form.get('title')
    post_content = request.form.get('post_content')

    tags = request.form.get('tags').split()

    if title is None or post_content is None or title == "" or post_content == "":
      abort(400, "please add a title/content!") # post missing title or content
    if len(title) > 128:
      abort(400, "title too long (max 128 characters)") # too long for database

    cur.execute(
      "INSERT INTO posts (title, post_content, created, lang, user_id) VALUES (%s, %s, %s, %s, %s) RETURNING id;",
      (title, post_content, datetime.now().astimezone(pytz.timezone('US/Eastern')), lang, user['id'])
    )
    post_id = cur.fetchone()[0]
    
    if tags != []:
      cur.executemany("INSERT INTO tags (tag_content) VALUES (%s) ON CONFLICT (tag_content) DO NOTHING;", iter([(tag,) for tag in tags]))

      cur.execute(
        "SELECT id FROM tags WHERE tag_content IN ({0});".format(', '.join('%s' for _ in tags)),
        tags)
      tag_ids = cur.fetchall()

      tag_map = [(post_id, tag_id['id']) for tag_id in tag_ids]
      cur.executemany("INSERT INTO tags_to_posts (post_id, tag_id) VALUES (%s, %s);", tag_map)

    db.commit()
    cur.close()

    return redirect(url_for('index'))


@bp.route('/search', methods=['GET'])
@login_required
def search():
  db = get_db()
  cur = get_dict_cursor(db)
  user = g.user

  query = request.args.get('q')
  tag_query = request.args.get('tq')

  if query is None:
    query = ''
  query = '%' + query + '%'
  if tag_query is None:
    tag_query = ''
  tag_query = '%' + tag_query + '%'

  cur.execute(
    """SELECT posts.*, users.username, tags.tag_content 
      FROM posts
      INNER JOIN tags_to_posts ON posts.id = tags_to_posts.post_id
      INNER JOIN tags ON tags.id = tags_to_posts.tag_id
      JOIN users ON posts.user_id = users.id 
      WHERE posts.lang = %s
      AND posts.post_content LIKE %s 
      AND tags.tag_content LIKE %s 
      ORDER BY created DESC;""", 
    (user['lang'], query, tag_query)
  )
  posts = cur.fetchall()

  return render_template('forum/index.html', posts=posts)


@bp.route('/post/<int:id>', methods=['GET', 'POST'])
@login_required
def forum_post(id):
  db = get_db()
  cur = get_dict_cursor(db)
  user = g.user

  if user is None:
    abort(403, 'please clear your session data!')
  
  if request.method == 'GET':
    cur.execute(
      "SELECT posts.*, users.username FROM posts JOIN users ON posts.user_id = users.id WHERE posts.id=%s;", 
      (id,)
    )
    post = cur.fetchone()
    html_content = md_to_html(post['post_content'])

    cur.execute(
      "SELECT comments.*, users.username FROM comments JOIN users ON comments.user_id = users.id WHERE comments.post_id = %s \
      ORDER BY created DESC;",
      (id,))
    comments = cur.fetchall()

    cur.execute(
      "SELECT * FROM tags JOIN tags_to_posts ON tags_to_posts.tag_id = tags.id WHERE tags_to_posts.post_id = %s;", 
      (id, ))
    tags = cur.fetchall()
    cur.close()

    return render_template('forum/post.html', forum_post=post, comments=comments, tags=tags, html_post=html_content)


@bp.route('/comment/<int:id>', methods=['POST'])
@login_required
def comment(id):
  db = get_db()
  cur = get_dict_cursor(db)
  user = g.user
  post_id = id

  comment_text = request.form.get('comment')
  if comment_text is None:
    return abort(403, 'comment was empty!')
  
  cur.execute(
    "INSERT INTO comments (comment_content, created, post_id, user_id) VALUES (%s, %s, %s, %s);",
    (comment_text, datetime.now().astimezone(pytz.timezone('US/Eastern')), post_id, user['id'])
  )
  db.commit()
  cur.close()

  return redirect(url_for('forum.forum_post', id=post_id))
  