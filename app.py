import os
import random
import sqlite3

from flask import Flask, redirect, render_template, request, session, url_for
from tempfile import TemporaryFile, mkdtemp
import requests
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import aiosqlite
import json
import array
from flask_bootstrap import Bootstrap
from pymongo import MongoClient

from helpers import apology, login_required, allowed_file, placename, joinroute


# Configure application
UPLOAD_FOLDER = './static/images'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)

# set up a MongoDB client
client = MongoClient("mongodb+srv://jonaw:digimondb123@digimondb.4zjqool.mongodb.net")

# get a reference to the database
mongodb = client["test"]

bootstrap = Bootstrap(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 6 * 1024 * 1024

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom Jinja filter
app.jinja_env.filters["joinroute"] = joinroute


# SQLite database
db = sqlite3.connect("./dataset/digimon.db", check_same_thread=False)
print(" * DB connection:", db.total_changes == 0)

app.secret_key = 'secret_key'



@app.route("/")
def index():
    """Home page"""
    return render_template("index.html")

@app.route("/me", methods=["GET", "POST"])
@login_required
def me():
    """Me Page"""

    sess_id = session["user_id"]
    rows = db.execute("SELECT des, postal, placename, date, time, pic, p_id FROM spots WHERE p_id = ? ORDER BY date DESC, time DESC", (sess_id,)).fetchall()
    username = db.execute("SELECT username FROM users WHERE id = ?", (sess_id,)).fetchone()[0]

    if request.method == "POST":

        delPid = request.form.get("del")
        db.execute("DELETE FROM spots WHERE p_id = ?", (int(delPid),))
        db.commit()
    
        return redirect("/me")

    return render_template("me.html", rows=rows, username=username)

@app.route("/profile", methods=["GET"])
@login_required
def profile():
    """Profile Page"""

    sess_id = session["user_id"]
    rows = db.execute("SELECT profilepic, username, email FROM users WHERE id = ?", (sess_id,)).fetchone()
    return render_template("profile.html", rows=rows)
    

@app.route("/change", methods=["GET", "POST"])
@login_required
def change():
    """Change Profile Page"""

    sess_id = session["user_id"]
    
    if request.method == "POST":
        pw = generate_password_hash(request.form.get("password"))
        email = request.form.get("email")
        file = request.files["file"]
        sess_id = session["user_id"]
        
        # filename checker
        if allowed_file(file.filename):
            # own filenaming convention
            f = (str(sess_id), "_pp.", file.content_type[6:])
            filename = "".join(f)
            print(filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            return apology("Invalid file", 400)
            
        # password confirmation
        if request.form.get("confirmation") != request.form.get("password"):
            return apology("password does not match", 400)
        
        # checks if there's a response
        if len(filename) > 1:
            db.execute("UPDATE users SET profilepic = ? WHERE id = ?", (filename, sess_id,))
        
        if len(request.form.get("password")) > 1:
            db.execute("UPDATE users SET hash = ? WHERE id = ?", (pw, sess_id,))
        
        if len(email) > 1:
            db.execute("UPDATE users SET email = ? WHERE id = ?", (email, sess_id,))
        
        db.commit()

        return redirect("/profile")
        
    else:
        return render_template("change.html")
        
@app.route("/groups", methods=["GET", "POST"])
@login_required
def groups():
    """Groups"""
    # User reached route via POST (as by submitting a form via POST)

    sess_id = session["user_id"]
    rows = db.execute("SELECT gname, gid FROM grps WHERE uid = ?", (sess_id,)).fetchall()

    grpname = db.execute("SELECT gname, username FROM users JOIN grps ON grps.uid=users.id").fetchall()

    if request.method == "POST":
        if request.form.get("del") != None:
            db.execute("DELETE FROM grps WHERE gid = ? AND uid = ?", (request.form.get("del"), sess_id))
        elif request.form.get("join") == "1":
            if db.execute("SELECT COUNT(gname) FROM grps WHERE gname = ? and uid != ?", (request.form.get("name"), sess_id,)).fetchone()[0] != 0:
                db.execute("INSERT INTO grps(gname, uid) VALUES (?,?)", (request.form.get("name"),sess_id,))
            else:
                return apology("Group doesnt exist or already joined", 400)
        else:
            if db.execute("SELECT COUNT(gname) FROM grps WHERE gname = ?", (request.form.get("name"),)).fetchone()[0] == 0:
                db.execute("INSERT INTO grps(gname, uid) VALUES (?,?)", (request.form.get("name"),sess_id,))
            else:
                return apology("Group exists", 400)

        db.commit()
        return redirect("/groups")

    return render_template("grps.html", rows=rows, grpname=grpname)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)
        
        print((request.form.get("username")), (request.form.get("password")))
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE login = ? AND password = ?", 
                          ((request.form.get("username")), (request.form.get("password")))).fetchone()
                
        # Ensure username exists and password is correct
        if not rows:
            return apology("invalid username or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[1]
        
        # Remember which type of db the user 

        print("this is my db-type:" + request.form.get("db-type"))
        session['db-type'] = request.form.get("db-type")
        
        # Redirect user to home page
        return redirect("/landing")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        print ("logging in form")
        return render_template("login.html")

@app.route("/compare",  methods=["GET", "POST"])
def compare():
    """ Compare Page """
    
    if request.method == 'GET':
        print("This is the saved session:" + session.get('db-type'))
        if session.get('db-type') == 'mongodb':
            # get a reference to the collection
            collection = mongodb["digimon_stats"]

            # find all documents in the collection
            documents = collection.find()

            # iterate over the documents and print each document
            for document in documents:
                print(document)
            
        # Read the colors from the JSON file
        with open('./templates/colors.json') as f:
            colors = json.load(f)

        digimons = db.execute("SELECT * FROM digimon").fetchall()
        digimons_fixed_list = []

        for digimon in digimons:
            digimon_list = list(digimon)
            element = digimon_list[3]
            if element:
                # Retrieve the color from the colors dict based on the element type
                color = colors[element]
                digimon_list.append(color)
                digimons_fixed_list.append(digimon_list)
        return render_template('compare.html', digimons=digimons_fixed_list)
    
    if (request.method == "POST"):
        print(request.form.get("digimon_name"))

        # Redirect to landing page with digimon name as a URL parameter
        return redirect(url_for('digimon_details', digimon_name=request.form.get("digimon_name")))

@app.route("/landing",  methods=["GET", "POST"])
def landing():
    """ Landing Page """
    
    if request.method == 'GET':
        print("This is the saved session:" + session.get('db-type'))
        if session.get('db-type') == 'mongodb':
            print("Trying to get data from mongodb")
            # get a reference to the collection
            collection = mongodb["digimon_stats"]

            # find all documents in the collection
            documents = collection.find()

            # iterate over the documents and print each document
            for document in documents:
                print(document)
            
        # Read the colors from the JSON file
        with open('./templates/colors.json') as f:
            colors = json.load(f)

        digimons = db.execute("SELECT * FROM digimon").fetchall()
        digimons_fixed_list = []

        for digimon in digimons:
            digimon_list = list(digimon)
            element = digimon_list[3]
            if element:
                # Retrieve the color from the colors dict based on the element type
                color = colors[element]
                digimon_list.append(color)
                digimons_fixed_list.append(digimon_list)
        return render_template('landing.html', digimons=digimons_fixed_list)
    
    if (request.method == "POST"):
        print(request.form.get("digimon_name"))

        # Redirect to landing page with digimon name as a URL parameter
        return redirect(url_for('digimon_details', digimon_name=request.form.get("digimon_name")))

@app.route('/landing/<digimon_name>', methods=["GET", "POST"])
def digimon_details(digimon_name):

    # Retrieve the data from the URL parameters and store it in a dictionary
    print("retrieving digimon stats for:" + digimon_name)

    # Get all the digimon names in order
    digimon_names = db.execute("SELECT * FROM digimon").fetchall()
    digimon_names = [name[0] for name in digimon_names]

    # Find the index of the current digimon
    current_index = digimon_names.index(digimon_name)

    # Find the indices of the adjacent digimon names
    if current_index == 0:
        adjacent_indices = [1]
    elif current_index == len(digimon_names) - 1:
        adjacent_indices = [len(digimon_names) - 2]
    else:
        adjacent_indices = [current_index - 1, current_index + 1]

    # Get the digimon information for the current and adjacent digimon names
    adjacent_digimons = [db.execute("SELECT * FROM digimon WHERE digimon_name = ?", (digimon_names[i],)).fetchone() for i in adjacent_indices]
    current_digimon = db.execute("SELECT * FROM digimon WHERE digimon_name = ?", (digimon_name,)).fetchone()

    print(adjacent_digimons)
    digimon_api_url = "https://www.digi-api.com/api/v1/digimon/{}".format(digimon_name)
    response = requests.get(digimon_api_url)
    english_description = "Unknown Description"

    if response.ok:
        digimon_description = response.json()
        if (digimon_description):
            for desc in digimon_description['descriptions']:
                if desc['origin'] == 'reference_book' and desc['language'] == 'en_us':
                    english_description = desc['description']
                    break


    # Check if the current digimon is the first or last in the list
    first_digimon = db.execute("SELECT * FROM digimon ORDER BY rowid ASC LIMIT 1").fetchone()
    last_digimon = db.execute("SELECT * FROM digimon ORDER BY rowid DESC LIMIT 1 OFFSET 1").fetchone()
    
    if current_digimon == first_digimon:
        previous_digimon = "NA"
    elif adjacent_digimons and adjacent_digimons[0]:
        previous_digimon = adjacent_digimons[0][0]
    else:
        previous_digimon = "NA"

    if current_digimon == last_digimon:
        next_digimon = "NA"
    elif adjacent_digimons and len(adjacent_digimons) > 1 and adjacent_digimons[1]:
        next_digimon = adjacent_digimons[1][0]
    elif adjacent_digimons and adjacent_digimons[0] and adjacent_digimons[0][0] > current_digimon[0]:
        next_digimon = adjacent_digimons[0][0]
    else:
        next_digimon = "NA"



    digivolution_paths_sql_query = """
    WITH RECURSIVE digivolutions_cte(digimon_name, digivolves_to, path) AS (
        SELECT digivolves_from, digivolves_to, CAST(digivolves_from AS TEXT) AS path
        FROM digivolutions
        WHERE digivolves_from = ?

        UNION ALL

        SELECT d.digivolves_from , d.digivolves_to, cte.path || ' -> ' || d.digivolves_from 
        FROM digivolutions d
        JOIN digivolutions_cte cte ON d.digivolves_from = cte.digivolves_to
    )
    SELECT DISTINCT path
    FROM digivolutions_cte
    WHERE digivolves_to IS NOT NULL;
    """
    digivolution_paths = db.execute(digivolution_paths_sql_query, (digimon_name,)).fetchall()
    max_path_length = max([path[0].count('->') for path in digivolution_paths])
    longest_paths = [path for path in digivolution_paths if path[0].count('->') == max_path_length]
    random_longest_evolution_path = random.choice(longest_paths)

    print(random_longest_evolution_path)

    random_longest_evolution_list = random_longest_evolution_path[0].split(' -> ')
    print(random_longest_evolution_list)

    # Render the landing page template with the data
    return render_template(
        "details.html", 
        digimon=current_digimon, 
        digimon_description = english_description,
        next_digimon = next_digimon,
        previous_digimon = previous_digimon,
        digivolution_paths = digivolution_paths,
        random_longest_evolution_path = random_longest_evolution_list
    )

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":    
        rows = db.execute("SELECT COUNT(id) FROM users WHERE username = ?", (request.form.get("username"),)).fetchone()
        username = request.form.get("username")
        pw = generate_password_hash(request.form.get("password"))
        email = request.form.get("email")
    
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)
        
        elif request.form.get("confirmation") != request.form.get("password"):
            return apology("password does not match", 400)
        
        elif rows[0] == 1:
            return apology("Username already exist", 400)
        
        db.execute("INSERT INTO users (username, hash, email) VALUES (?, ?, ?)", (username, pw, email,))

        db.commit()
        
        # Redirect user to success
        return render_template("success.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


if __name__ == '__main__':
    app.run(port=5000, host='localhost', debug=True)

