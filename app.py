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

    username = request.cookies.get('username')

    if username != None:
        if len(username) > 0:
            return redirect("/landing")
    
    return render_template("index.html")


app.route("/home")
@login_required
def home():
    """USER HOME"""

    username = request.cookies.get('username')
    db_type = request.cookies.get('db-type')

    user_data = users.get_user(db, username)
    team_data = users.get_team(db, username)
    digimon_data = users.get_all_digimons(db)

    return render_template("home.html", user_data = user_data, team_data = team_data, digimon_data = digimon_data, login = username)


@app.route("/team", methods=['GET', 'POST'])
@login_required
def team():
    '''TEAM PAGE'''

    username = request.cookies.get('username')
    all_digimons = users.get_all_digimons(db)
    print(all_digimons)
    team = users.get_team(db, username)
    print(team)

    if request.method == 'POST':

        digimon_1 = request.form.get('digimon_1')
        digimon_2 = request.form.get('digimon_2')
        digimon_3 = request.form.get('digimon_3')
        digimon_4 = request.form.get('digimon_4')
        digimon_5 = request.form.get('digimon_5')
        digimon_6 = request.form.get('digimon_6')

        users.update_team(db,
                          username,
                          digimon_1,
                          digimon_2,
                          digimon_3,
                          digimon_4,
                          digimon_5,
                          digimon_6
                          )
        
        return redirect('/team')

    return render_template("team.html", all_digimons = all_digimons, team = team, login = username)


@app.route("/profile", methods=["GET"])
@login_required
def profile():
    """Profile Page"""

    username = request.cookies.get('username')
    data = users.get_user(db, username)
    return render_template("profile.html", rows=data, login = username)

        

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        db_type = request.form.get("db-type")
        
        allowed_db_type = ['']

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
@login_required
def compare():
    """ Compare Page """

    username = request.cookies.get('username')
    
    if request.method == 'GET':
        if request.cookies.get('db-type') == 'mongodb':
            # get a reference to the collection
            collection = mongodb["digimon_stats"]
            digimon_collection = mongodb["digimon_stats"]
            pipeline = [
                {
                    "$match": {
                        "$or": [
                            {"Digimon": "Agumon"},
                            {"Digimon": "Betamon"}
                        ]
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "Type": {"$push": "$Type"}
                    }
                },
                {
                    "$project": {
                        "locale": {
                            "$switch": {
                                "branches": [
                                    {
                                        "case": {
                                            "$or": [
                                                {"$and": [{"$eq": [{"$arrayElemAt": ["$Type", 0]}, "Vaccine"]}, {"$eq": [{"$arrayElemAt": ["$Type", 1]}, "Virus"]}]},
                                                {"$and": [{"$eq": [{"$arrayElemAt": ["$Type", 0]}, "Virus"]}, {"$eq": [{"$arrayElemAt": ["$Type", 1]}, "Data"]}]},
                                                {"$and": [{"$eq": [{"$arrayElemAt": ["$Type", 0]}, "Data"]}, {"$eq": [{"$arrayElemAt": ["$Type", 1]}, "Vaccine"]}]},
                                            ]
                                        },
                                        "then": "Super Effective"
                                    }
                                ],
                                "default": "Neutral"
                            }
                        }
                    }
                }
            ]

            # for doc in digimon_collection.aggregate(pipeline):
            #     print(doc.locale)

            digimons = collection.find()
            digimons_fixed_list = []
            for digimon in digimons:
                digimon_list = list(digimon.values())[1:]
                digimons_fixed_list.append(digimon_list)
            return render_template('compare.html', digimons=digimons_fixed_list, login=username)
        else:
        # Read the colors from the JSON file
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
                digimons_fixed_list.append(digimon_list)
        return render_template('compare.html', digimons=digimons_fixed_list, login = username)
    
    if (request.method == "POST"):
        print(request.form.get("digimon_name"))

        # Redirect to landing page with digimon name as a URL parameter
        return redirect(url_for('digimon_details', digimon_name=request.form.get("digimon_name"), login = username))

@app.route("/landing",  methods=["GET", "POST"])
@login_required
def landing():
    """ Landing Page """

    username = request.cookies.get('username')
    
    if request.method == 'GET':
        print(f"This is the saved session: {request.cookies.get('db-type')}")
        
        # Read the colors from the JSON file
        with open('./templates/colors.json') as f:
            colors = json.load(f)
            
        if request.cookies.get('db-type')== 'mongodb':
            print("Trying to get data from mongodb")
            # get a reference to the collection
            collection = mongodb["digimon_stats"]

            # find all documents in the collection
            documents = collection.find()

            # find all documents in the collection
            documents = list(collection.find({}))

            digimons_fixed_list = []

            for document in documents:
                digimon_list = []
                for key in document:
                    if key != "_id":
                        value = document[key]
                        digimon_list.append(value)
                        print(f"{key}: {value}")
                        if key == "Attribute" and value:
                            # Retrieve the color from the colors dict based on the element type
                            color = colors[value]
                            digimon_list.append(color)
                digimons_fixed_list.append(digimon_list)
            # print(digimons_fixed_list)
            return render_template('landing.html', digimons=digimons_fixed_list, login = username)

        # SQLite3 implementation
        if request.cookies.get('db-type') == 'sqlite':
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
            return render_template('landing.html', digimons=digimons_fixed_list, login=username)

    
    if (request.method == "POST"):
        print(request.form.get("digimon_name"))

        # Redirect to landing page with digimon name as a URL parameter
        return redirect(url_for('digimon_details', digimon_name=request.form.get("digimon_name")))
    
# @app.route("/selection",  methods=["GET", "POST"])
# def selection():
#     """Landing Page"""

#     if request.method == "GET":
#         # Retrieve the list of all available digimon from the database
#         digimons = db.execute("SELECT * FROM Digimon").fetchall()
#         print("digimons:", digimons)

#         # Extract the list of digimon names
#         digimon_names = [digimon[0] for digimon in digimons]
#         print("digimon_names:", digimon_names)

#         # Render the landing page with the list of digimon names
#         return render_template("selection.html", digimon_names=digimon_names)

#     if request.method == "POST":
#         # Retrieve the names of the selected digimon from the form data
#         digimon_name_1 = request.form.get("digimon_name_1")
#         digimon_name_2 = request.form.get("digimon_name_2")

#         # Redirect to the evolution page with the selected digimon names as URL parameters
#         return redirect(url_for("evolution_path", digimon_name_1=digimon_name_1, digimon_name_2=digimon_name_2))

@app.route("/path", methods=["GET", "POST"])
@login_required
def path():
    """ Compare Page """

    username = request.cookies.get('username')

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
        return render_template('selection.html', digimons=digimons_fixed_list, login=username)
    
    if request.method == "POST":
        # Retrieve the names of the selected digimon from the form data
        digimon_name_1 = request.form.get("digimon_name_1")
        digimon_name_2 = request.form.get("digimon_name_2")

        # Redirect to evolution page with the selected digimon names as URL parameters
        return redirect(url_for("evolution_path", digimon_name_1=digimon_name_1, digimon_name_2=digimon_name_2))

    
@app.route("/evolution")
@login_required
def evolution_path():
    """Evolution Path Page"""

    # Retrieve the names of the selected digimon from the URL parameters
    digimon_name_1 = request.args.get("digimon_name_1")
    digimon_name_2 = request.args.get("digimon_name_2")
    username = request.cookies.get('username')

    if request.method == 'GET':
        if request.cookies.get('db-type') == 'mongodb':
            # execute pipeline and print result
            paths = []
            path = list(find_all_paths(digimon_name_1, digimon_name_2, mongodb['digivolution']))
            paths.append(path)
            print(f"All possible digivolution paths from {digimon_name_1} to {digimon_name_2}:")
            print(paths)

        if request.cookies.get('db-type') == 'sqlite':

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
            print(paths)
            for p in paths:
                path = p[0].split(',')
                print(' -> '.join(path))

    # Render the evolution path page with the selected digimon names and the evolution path
    return render_template("evolution_path.html", digimon_name_1=digimon_name_1, digimon_name_2=digimon_name_2, path=paths, login=username)

def find_all_paths(start_digimon, target_digimon, digivolution_collection, visited=None, path=None):
    # Create a visited set and a path list for the first call of the function
    if visited is None:
        visited = set()
    if path is None:
        path = start_digimon

    # If the current Digimon is the target Digimon, yield the current path
    if start_digimon == target_digimon:
        print(path)
        yield path

    # Add the current Digimon to the visited set
    visited.add(start_digimon)

    # Retrieve the digivolution data for the current Digimon
    digivolutions = digivolution_collection.find({"Digivolves from": start_digimon})
    digivolutions = [doc["Digivolves to"] for doc in digivolutions]

    # Recursively find all paths from the next Digimon
    for next_digimon in digivolutions:
        if next_digimon not in visited:
            # Append the next Digimon to the path
            new_path = path + ", " + next_digimon
            # Yield all paths from the next Digimon
            yield from find_all_paths(next_digimon, target_digimon, digivolution_collection, visited, new_path)






@app.route('/landing/<digimon_name>', methods=["GET", "POST"])
@login_required
def digimon_details(digimon_name):

    username = request.cookies.get('username')

    if request.cookies.get('db-type') == "mongodb":
        print("Retrieving Details from MongoDB...")
        # Get all the digimon names in order
        digimon_names = [doc['Digimon'] for doc in mongodb['digimon_stats'].find()]

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
        adjacent_digimons = [mongodb['digimon_stats'].find_one({'Digimon': digimon_names[i]}) for i in adjacent_indices]
        current_digimon = mongodb['digimon_stats'].find_one({'Digimon': digimon_name})

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
        first_digimon = mongodb['digimon_stats'].find_one(sort=[('rowid', 1)])
        last_digimon = mongodb['digimon_stats'].find_one(sort=[('rowid', -1)], skip=1)

        if current_digimon == first_digimon:
            previous_digimon = "NA"
        elif adjacent_digimons and adjacent_digimons[0]:
            previous_digimon = adjacent_digimons[0]['Digimon']
        else:
            previous_digimon = "NA"

        if current_digimon == last_digimon:
            next_digimon = "NA"
        elif adjacent_digimons and len(adjacent_digimons) > 1 and adjacent_digimons[1]:
            next_digimon = adjacent_digimons[1]['Digimon']
        elif adjacent_digimons and adjacent_digimons[0] and adjacent_digimons[0]['Digimon'] > current_digimon['Digimon']:
            next_digimon = adjacent_digimons[0]['Digimon']
        else:
            next_digimon = "NA"
        
        digivolutions = mongodb["digivolution"].find({'Digivolves from': digimon_name})
        paths = []

        for digivolution in digivolutions:
            path = [digivolution['Digivolves from'], digivolution['Digivolves to']]
            processed_evolutions = set([(digivolution['Digivolves from'], digivolution['Digivolves to'])])

            while True:
                previous_digivolution = mongodb["digivolution"].find_one({'Digivolves from': path[-1]}) # Modified line
                if previous_digivolution is None:
                    break

                # check if the evolution has already been processed in reverse
                if (previous_digivolution['Digivolves from'], previous_digivolution['Digivolves to']) in processed_evolutions:
                    break

                # check if the evolution can be reversed
                if (previous_digivolution['Digivolves to'], previous_digivolution['Digivolves from']) in processed_evolutions:
                    break

                path.append(previous_digivolution['Digivolves to']) # Modified line
                processed_evolutions.add((previous_digivolution['Digivolves from'], previous_digivolution['Digivolves to']))

            paths.append(' -> '.join(path))

        # Removes all the N/A in each digivolution
        paths_fixed = [path.replace("-> N/A", "") if "N/A" in path else path for path in paths]

        longest_path = max(paths_fixed, key=lambda path: path.count('->'))
        longest_path_list = longest_path.split(' -> ')
        
        current_digimon_fixed = [value for key, value in current_digimon.items() if key != '_id']

        # Render the landing page template with the data
        return render_template(
            "details.html", 
            digimon=current_digimon_fixed, 
            digimon_description = english_description,
            next_digimon = next_digimon,
            previous_digimon = previous_digimon,
            digivolution_paths = longest_path_list,
            random_longest_evolution_path = longest_path_list, login = username
        )

    if request.cookies.get('db-type') == "sqlite":
        print("Retrieving details from sqlite")
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
                    
        print(english_description)
        # Check if the current digimon is the first or last in the list
        first_digimon = db.execute("SELECT * FROM digimon ORDER BY rowid ASC LIMIT 1").fetchone()
        last_digimon = db.execute("SELECT * FROM digimon ORDER BY rowid DESC LIMIT 1 OFFSET 1").fetchone()
        
        
        print(first_digimon)
        print(last_digimon)
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
            random_longest_evolution_path = random_longest_evolution_list, 
            login = username
        )


@app.route("/logout")
@login_required
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
    app.run(port=9091, host='0.0.0.0', debug=True)
