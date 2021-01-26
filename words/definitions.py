from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from words.auth import login_required
from words.db import get_db

bp = Blueprint('definitions', __name__)

@bp.route('/')
def index():
    db = get_db()
    definitions = db.execute(
        'SELECT d.id, word, definition, created, author_id, username'
        ' FROM definitions d JOIN user u ON d.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('definitions/index.html', definitions_list=definitions)

@bp.route('/<author_id>/my_words')
def my_words(author_id):
    db = get_db()
    definitions = db.execute(
        'SELECT d.id, word, definition, created, author_id, username'
        ' FROM definitions d JOIN user u ON d.author_id = u.id WHERE author_id = ?'
        ' ORDER BY created DESC', (author_id,)
    ).fetchall()
    return render_template('definitions/index.html', definitions_list=definitions)

@bp.route('/random')
def random():
    db = get_db()
    definitions = db.execute(
        'SELECT d.id, word, definition, created, author_id, username'
        ' FROM definitions d JOIN user u ON d.author_id = u.id'
        ' ORDER BY RANDOM() LIMIT 1'
    ).fetchall()
    return render_template('definitions/index.html', definitions_list=definitions)



@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        word = request.form['word']
        definition = request.form['definition']
        error = None

        if not word:
            error = 'Word is required.'
        
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO definitions (word, definition, author_id)'
                'VALUES (?, ?, ?)',
                (word, definition, g.user['id'])
            )
            db.commit()
            return redirect(url_for('definitions.index'))
    
    return render_template('definitions/add.html')

def get_definition(id, check_author=True):
    definition = get_db().execute(
        'SELECT d.id, word, definition, created, author_id, username'
        ' FROM definitions d JOIN user u ON d.author_id = u.id'
        ' WHERE d.id = ?',
        (id,)
    ).fetchone()

    if definition is None:
        abort(404, "Definition id {0} doesn't exist.".format(id))

    if check_author and definition['author_id'] != g.user['id']:
        abort(403, "Not permitted to edit this one")

    return definition


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_definition(id)

    if request.method == 'POST':
        word = request.form['word']
        definition = request.form['definition']
        error = None

        if not word:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE definitions SET word = ?, definition = ?'
                ' WHERE id = ?',
                (word, definition, id)
            )
            db.commit()
            return redirect(url_for('definitions.index'))

    return render_template('definitions/update.html', post=post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_definition(id)
    db = get_db()
    db.execute('DELETE FROM definitions WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('definitions.index'))


@bp.route('/<int:id>/word')
def word(id):
    definition = get_definition(id, check_author=False)
    return render_template('definitions/word.html', post=definition)