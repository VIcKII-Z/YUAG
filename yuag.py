"""This file contains the code for the web version of the LUX app."""
import sqlite3
from flask import Flask, request, make_response, render_template, jsonify, url_for, redirect
from database import details, filter_obj

#-----------------------------------------------------------------------
app = Flask(__name__, template_folder='.')
DATABASE = 'lux.sqlite'
#-----------------------------------------------------------------------

@app.route('/', methods=['GET'])
@app.route('/search', methods=['GET'])
def index():
    """index page"""
    label = request.args.get('l') if request.args.get('l') is not None else ''
    classification = request.args.get('c') if request.args.get('c') is not None else ''
    agent = request.args.get('a') if request.args.get('a') is not None else ''
    department = request.args.get('d') if request.args.get('d') is not None else ''
    html = render_template('static/index.html', label=label,
                           classification=classification, agent=agent, department=department)
    response = make_response(html)
    return response

@app.route('/searchresults', methods=['GET'])
def searchresults():
    """This function renders the search results page."""
    label = request.args.get('l') if request.args.get('l') != 'null' else ''
    classification = request.args.get('c') if request.args.get('c') != 'null' else ''
    agent = request.args.get('a') if request.args.get('a') != 'null' else ''
    department = request.args.get('d') if request.args.get('d') != 'null' else ''
    print(label, classification, agent, department)

    if all(val is None or val.strip() == '' for val in [label, classification, agent, department]):
        results = 'no response'
        print('no response')
    else:
        results = filter_obj.search(agent, department, classification, label)
        print(results)
    return jsonify({'results':results})

@app.route('/obj', methods=['GET'])
def missing_obj_id():
    """ This function renders the error page if the object id is missing."""
    return render_error_page("Error: missing object id.")

@app.route('/obj/<int:obj_id>', methods=['GET'])
def object_details(obj_id):
    """This function renders the object details page."""
    try:
        obj_id = int(obj_id)
    except ValueError:
        return render_error_page(f"Error: no object with id {obj_id} exists")
    if obj_id < 0 or query_db("SELECT * FROM objects WHERE id = ?", (obj_id,), one=True) is None:
        return render_error_page(f"Error: no object with id {obj_id} exists")

    obj = details.get_obj_by_id(obj_id)
    if obj is None:
        return render_error_page(f"Error: no object with id {obj_id} exists")

    return render_template('static/object_details.html', obj=obj)

@app.errorhandler(404)
def page_not_found(ex):
    """This function renders the error page if the page is not found."""
    return render_template('static/error_page.html', error_message=ex.description), 404

def render_error_page(message, status_code=404):
    """This function renders the error page."""
    response = make_response(render_template('static/error_page.html',
                             error_message=message), status_code)
    return response

def query_db(query, args=(), one=False):
    """This function queries the database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    retrieve = cur.fetchall()
    conn.commit()
    cur.close()
    return (retrieve[0] if retrieve else None) if one else retrieve


@app.route('/object_details/<int:obj_id>/edit_label', methods=['GET', 'POST'])
def edit_label(obj_id):
    """This function renders the edit label page."""
    if request.method == 'POST':
        new_label = request.form['label']
        query = "UPDATE objects SET label = ? WHERE id = ?"
        query_db(query, (new_label, obj_id))
        return redirect(url_for('object_details', obj_id=obj_id))

    obj = query_db("SELECT * FROM objects WHERE id = ?", (obj_id,), one=True)
    return render_template('static/edit_label.html', obj=obj)
