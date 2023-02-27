import os
import sqlite3

from flask import Flask, redirect, render_template, request, session
from tempfile import TemporaryFile, mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, allowed_file, placename, joinroute

# Configure application
UPLOAD_FOLDER = './static/images'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
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

        # Query database for username
        rows = db.execute("SELECT COUNT(id), id, hash FROM users WHERE username = ?", (request.form.get("username"),)).fetchone()

        # Ensure username exists and password is correct
        if rows[0] != 1 or not check_password_hash(rows[2], request.form.get("password")):
            return apology("invalid username or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[1]

        # Redirect user to home page
        return redirect("/around")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


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