import os
import random
import sqlite3

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for, make_response
from tempfile import TemporaryFile, mkdtemp
import requests
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import aiosqlite
import json
import array
from flask_bootstrap import Bootstrap
from pymongo import MongoClient
from users import users

from helpers import apology, login_required, allowed_file, placename, joinroute


# Configure application
UPLOAD_FOLDER = './static/images'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)

# set up a MongoDB client
client = MongoClient("mongodb+srv://jonaw:digimondb123@digimondb.4zjqool.mongodb.net")

# get a reference to the database
mongodb = client["test"]

print(" * MONGO Connection: Success")

bootstrap = Bootstrap(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 6 * 1024 * 1024

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"

    # NO CACHE TO RELOAD JS/ CSS
    response.headers['Cache-Control'] = 'public, max-age=0'

    return response

# Custom Jinja filter
app.jinja_env.filters["joinroute"] = joinroute


# SQLite database
db = sqlite3.connect("./dataset/digimon.db", check_same_thread=False)
print(" * DB connection:", db.total_changes == 0)

app.secret_key = 'secret_key'


@app.route("/")
def index():
    """Index page"""
    return render_template("index.html")


app.route("/home")
@login_required
def home():
    """USER HOME"""

    username = request.cookies.get('username')

    user_data = users.get_user(db, username)
    team_data = users.get_team(db, username)
    digimon_data = users.get_all_digimons(db)

    print(type(user_data), user_data)
    print(type(team_data), team_data)

    return render_template("home.html", user_data = user_data, team_data = team_data, digimon_data = digimon_data)



@app.route("/profile", methods=["GET"])
@login_required
def profile():
    """Profile Page"""

    username = request.cookies.get('username')
    data = users.get_user(db, username)
    return render_template("profile.html", rows=data)
    

@app.route("/change", methods=["GET", "POST"])
@login_required
def change():
    """Change Profile Page"""

    username = request.cookies.get('username')
    
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

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        db_type = request.form.get("db-type")

        # Ensure username was submitted
        if not username:
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 400)
        
        # Query database for username
        res = users.check_credentials(db, username, password)
                
        # Ensure username exists and password is correct
        if res == False:
            return apology("password and username does not match", 400)

        # Set cookie and redirect
        resp = make_response(redirect("/landing"))
        resp.set_cookie('username', username)
        resp.set_cookie('db-type', db_type)
        return resp
        
        # Remember which type of db the user 

        # print("this is my db-type:" + request.form.get("db-type"))
        # session['db-type'] = request.form.get("db-type")
        

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        print ("logging in form")
        return render_template("login.html")

@app.route("/compare",  methods=["GET", "POST"])
def compare():
    """ Compare Page """
    
    if request.method == 'GET':
        # print("This is the saved session:" + session.get('db-type'))
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

        digimonTypeEffective = db.execute("""
                              SELECT
                                IIF(
                                    (d1.digimon_type = 'Vaccine' and d2.digimon_type = 'Virus') or
                                    (d1.digimon_type = 'Virus' and d2.digimon_type = 'Data') or
                                    (d1.digimon_type = 'Data' and d2.digimon_type = 'Vaccine') 
                                    ,
                                    'Super Effective',
                                    'Neutral')
                                    AS locale
                                
                                FROM
                                digimon d1,digimon d2
                                Where d1.digimon_name = "Agumon" and d2.digimon_name = "Betamon"
                              """).fetchall()
        
        digimonBestAttack = db.execute("""
                              SELECT s1.skill AS best_move
                                FROM Digimon_Skills AS ds1
                                JOIN Skills_Info AS s1 ON ds1.skill = s1.skill
                                JOIN Digimon AS dg1 ON dg1.digimon_name = ds1.digimon_name
                                JOIN Digimon AS dg2 
                                JOIN Skill_Type_Advantage AS sta ON s1.attribute = sta.attacking_type AND dg2.attribute = sta.defending_type
                                WHERE dg1.digimon_name = 'Agumon' AND dg2.digimon_name = 'Tanemon' AND sta.advantage = 2   
                                LIMIT 1;                
                    """).fetchall()
        
        digimons = db.execute("""
                              SELECT * from digimon;
                    """).fetchall()
        digimonBestAttack
        digimonTypeEffective
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
        print(f"This is the saved session: {session.get('db-type')}")
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
    
@app.route("/selection",  methods=["GET", "POST"])
def selection():
    """Landing Page"""

    if request.method == "GET":
        # Retrieve the list of all available digimon from the database
        digimons = db.execute("SELECT * FROM Digimon").fetchall()
        print("digimons:", digimons)

        # Extract the list of digimon names
        digimon_names = [digimon[0] for digimon in digimons]
        print("digimon_names:", digimon_names)

        # Render the landing page with the list of digimon names
        return render_template("selection.html", digimon_names=digimon_names)

    if request.method == "POST":
        # Retrieve the names of the selected digimon from the form data
        digimon_name_1 = request.form.get("digimon_name_1")
        digimon_name_2 = request.form.get("digimon_name_2")

        # Redirect to the evolution page with the selected digimon names as URL parameters
        return redirect(url_for("evolution_path", digimon_name_1=digimon_name_1, digimon_name_2=digimon_name_2))

    
@app.route("/evolution")
def evolution_path():
    """Evolution Path Page"""

    # Retrieve the names of the selected digimon from the URL parameters
    digimon_name_1 = request.args.get("digimon_name_1")
    digimon_name_2 = request.args.get("digimon_name_2")

    # Query the database to retrieve the evolution path between the two digimon
    path_query = """
    WITH start_node(digimon_name) AS (
        SELECT digimon_name
        FROM Digimon
        WHERE digimon_name = :digimon_name_1
    ),
    evolution_path(level, from_digimon, to_digimon, chain) AS (
        SELECT 1, sn.digimon_name, d2.digimon_name, sn.digimon_name || ',' || d2.digimon_name
        FROM start_node sn
        JOIN Digivolutions AS e ON e.digivolves_from = sn.digimon_name
        JOIN Digimon AS d2 ON e.digivolves_to = d2.digimon_name
        UNION ALL
        SELECT ep.level + 1, ep.from_digimon, d2.digimon_name, ep.chain || ',' || d2.digimon_name
        FROM evolution_path AS ep
        JOIN Digivolutions AS e ON e.digivolves_from = ep.to_digimon
        JOIN Digimon AS d2 ON e.digivolves_to = d2.digimon_name
        WHERE instr(ep.chain, d2.digimon_name) = 0
        AND ep.level < (SELECT COUNT(*) FROM Digimon)
    )
    SELECT chain
    FROM evolution_path
    WHERE to_digimon = :digimon_name_2
    ORDER BY level;
    """
    paths = db.execute(path_query, {"digimon_name_1": digimon_name_1, "digimon_name_2": digimon_name_2}).fetchall()
    for p in paths:
        path = p[0].split(',')
        print(' -> '.join(path))

    # Render the evolution path page with the selected digimon names and the evolution path
    return render_template("evolution_path.html", digimon_name_1=digimon_name_1, digimon_name_2=digimon_name_2, path=paths)



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

    resp = make_response(redirect("/"))
    resp.set_cookie('username', '', max_age=0)
    resp.set_cookie('db_type', '', max_age=0)
    return resp



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":    

        # pw = generate_password_hash(request.form.get("password"))

        username = request.form.get("username")
        email = request.form.get("email")
        name = request.form.get("name")
        password = request.form.get("password")

        if users.get_user(db, username) != None:
            return apology("username already exists", 400)
        
    
        # Ensure username was submitted
        if not username:
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not email:
            return apology("must provide email", 400)
        
        elif not name:
            return apology("must provide name", 400)
        
        elif not password:
            return apology("must provide password", 400)
        
        res = users.create_user(db, username, email, name, password)
        
        if res == False:
            return apology("internal server error", 500)
        
        res = users.create_team(db, username, "", "", "", "", "", "")
        
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
    app.run(port=8080, host='0.0.0.0', debug=True)
