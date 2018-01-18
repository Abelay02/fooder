from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import random
import time

from helpers import apology, login_required

from flask_mail import Mail
from flask_mail import Message

# Configure application
app = Flask(__name__)

app.config.update(
	DEBUG=True,
	#EMAIL SETTINGS
	MAIL_SERVER='mail.smtp2go.com',
	MAIL_PORT=2525,
	MAIL_USE_SSL=False,
	MAIL_USERNAME = 'abdub1@hotmail.com',
	MAIL_PASSWORD = 'iloverahal'
	)
mail = Mail(app)

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///fooder.db")


##This is where users confirm their email addresses, before they can use the app
@app.route("/confirm", methods=["GET", "POST"])
@login_required
def confirm():

    if request.method == "POST":

        rows = db.execute("SELECT * FROM users WHERE userid=:userid", userid=session["user_id"])

        ##confcode is generated upon registration and stored in the db, in the users table
        confirmation_code = request.form.get("code")
        confcode = rows[0]["confcode"]

        ##confirmation is only required once
        if confcode == confirmation_code:
            db.execute("UPDATE users SET confirmed=:confirmed WHERE userid=:userid",
                       confirmed=1, userid=session["user_id"])

            return redirect("/")

        else:
            return apology("incorrect confirmation code", 400)

    else:
        return render_template("confirm.html")


@app.route("/email")
@login_required
def email():
    """sends the confirmation email and code to the user"""

    ##value 'email' is taken out of the users table, input at registration
    rows = db.execute("SELECT * FROM users WHERE userid=:userid", userid=session["user_id"])
    email = rows[0]["email"]


    msg = Message("Confirmation Code",
                  sender="abdub1@hotmail.com",
                  recipients=['%(email)s' % {'email': email}])

    confcode = rows[0]["confcode"]

    msg.body = ('Your confirmation code is %(confcode)s' %
                {'confcode': confcode})

    mail.send(msg)

    return redirect("/confirm")



@app.route("/")
@login_required
def index():
    """displaying all of the orders placed within the last 2 hours"""

    ##making sure that unconfirmed users cannot use the app
    rows = db.execute("SELECT * FROM users WHERE userid=:userid", userid=session["user_id"])
    confirmation = rows[0]["confirmed"]
    if confirmation == 0:
        return redirect("/confirm")

    ##unixtime is given in seconds, 7200 seconds represents 1 hour
    orders = db.execute("SELECT orderid FROM orders WHERE unixtime > (:unixtimenow - 7200) AND commits > 0", unixtimenow=int(time.time()))


    for order in orders:


        order["orderid"] = db.execute("Select orderid From info Where orderid=:orderid", orderid=order["orderid"])[0]["orderid"]

        order["username"] = db.execute("Select username From info Where orderid=:orderid", orderid=order["orderid"])[0]["username"]

        order["foodtype"] = db.execute("Select foodtype From info Where orderid=:orderid", orderid=order["orderid"])[0]["foodtype"]

        order["description"] = db.execute("Select description From info Where orderid=:orderid", orderid=order["orderid"])[0]["description"]

        order["location"] = db.execute("Select geolocation From info Where orderid=:orderid", orderid=order["orderid"])[0]["geolocation"]

        order["commits"] = db.execute("Select commits From info Where orderid=:orderid", orderid=order["orderid"])[0]["commits"]

        order["time"] = db.execute("Select datetime From info Where orderid=:orderid", orderid=order["orderid"])[0]["datetime"]

        order["email"] = db.execute("SELECT users.email FROM users INNER JOIN info ON users.username = info.username WHERE info.orderid=:orderid", orderid=order["orderid"])[0]["email"]

        order["venmo"] = db.execute("SELECT users.venmo FROM users INNER JOIN info ON users.username = info.username WHERE info.orderid=:orderid", orderid=order["orderid"])[0]["venmo"]

        order["phone"] = db.execute("SELECT users.phone FROM users INNER JOIN info ON users.username = info.username WHERE info.orderid=:orderid", orderid=order["orderid"])[0]["phone"]

        order["commits"] = db.execute("SELECT commits FROM info WHERE orderid=:orderid", orderid=order["orderid"])[0]["commits"]

        order["rating"] = db.execute("SELECT users.rating FROM users INNER JOIN info ON users.username = info.username WHERE info.orderid=:orderid", orderid=order["orderid"])[0]["rating"]

        order["counter"] = db.execute("SELECT users.counter FROM users INNER JOIN info ON users.username = info.username WHERE info.orderid=:orderid", orderid=order["orderid"])[0]["counter"]

        order["stars"] = round(order["rating"]/order["counter"],1)

        order["starp"] = order["stars"] * 20

    return render_template("index.html", orders=orders)


@app.route("/commitsdb", methods=["GET", "POST"])
@login_required
def commitsdb():
    """inputs new commitments into database, updates how many commitments an order is waiting for"""

    ##making sure that unconfirmed users cannot use the app
    rows = db.execute("SELECT * FROM users WHERE userid=:userid", userid=session["user_id"])
    confirmation = rows[0]["confirmed"]
    if confirmation == 0:
        return redirect("/confirm")

    if request.method == "POST":

        oldcommits = db.execute("SELECT commits FROM orders WHERE orderid=:orderid", orderid=request.form.get("commit"))[0]["commits"]

        alreadycommitted = db.execute("SELECT userid FROM commits WHERE orderid = :orderid",
                          orderid=request.form.get("commit"))

        alreadycommitted2 = db.execute("SELECT userid FROM commits WHERE orderid = :orderid AND userid=:userid",
                          orderid=request.form.get("commit"), userid=session["user_id"])


        ##ensures that no-one can commit to an order more than once
        if len(alreadycommitted2) != 0:
            return redirect("/commitments")

        db.execute("INSERT INTO commits (userid, orderid) VALUES (:userid, :orderid)",
                   userid=session["user_id"], orderid=request.form.get("commit"))

        db.execute("UPDATE orders SET commits=:commits WHERE orderid=:orderid",
                       commits=(oldcommits)-1, orderid=request.form.get("commit"))

    return redirect("/commitments")


@app.route("/commitments", methods=["GET", "POST"])
@login_required
def commitments():
    """shows a user all of the orders that they have commited to"""

    ##prevents unregistered users from using the app
    rows = db.execute("SELECT * FROM users WHERE userid=:userid", userid=session["user_id"])
    confirmation = rows[0]["confirmed"]
    if confirmation == 0:
        return redirect("/confirm")

    orders = db.execute("Select orderid from commits Where userid=:userid",userid = session["user_id"] )

    for order in orders:

        # filling index with data from the portfolio
        #data = lookup(order["symbol"])

        order["username"] = db.execute("Select username From info Where orderid=:orderid", orderid=order["orderid"])[0]["username"]

        order["foodtype"] = db.execute("Select foodtype From info Where orderid=:orderid", orderid=order["orderid"])[0]["foodtype"]

        order["description"] = db.execute("Select description From info Where orderid=:orderid", orderid=order["orderid"])[0]["description"]

        order["location"] = db.execute("Select geolocation From info Where orderid=:orderid", orderid=order["orderid"])[0]["geolocation"]

        order["piclocation"] = db.execute("Select piclocation From info Where orderid=:orderid", orderid=order["orderid"])[0]["piclocation"]

        order["time"] = db.execute("Select datetime From info Where orderid=:orderid", orderid=order["orderid"])[0]["datetime"]

        order["email"] = db.execute("SELECT users.email FROM users INNER JOIN info ON users.username = info.username WHERE info.orderid=:orderid", orderid=order["orderid"])[0]["email"]

        order["venmo"] = db.execute("SELECT users.venmo FROM users INNER JOIN info ON users.username = info.username WHERE info.orderid=:orderid", orderid=order["orderid"])[0]["venmo"]

        order["phone"] = db.execute("SELECT users.phone FROM users INNER JOIN info ON users.username = info.username WHERE info.orderid=:orderid", orderid=order["orderid"])[0]["phone"]

        order["commits"] = db.execute("SELECT commits FROM info WHERE orderid=:orderid", orderid=order["orderid"])[0]["commits"]

    return render_template("commitments.html", orders=orders)


@app.route("/myorders")
@login_required
def myorders():
    """shows user all of the orders that they have placed"""

    ##prevents unregistered users from using the app
    rows = db.execute("SELECT * FROM users WHERE userid=:userid", userid=session["user_id"])
    confirmation = rows[0]["confirmed"]
    if confirmation == 0:
        return redirect("/confirm")

    orders = db.execute("Select orderid from orders Where userid=:userid", userid = session["user_id"])

    for order in orders:

        order["username"] = db.execute("Select username From info Where orderid=:orderid", orderid=order["orderid"])[0]["username"]

        order["foodtype"] = db.execute("Select foodtype From info Where orderid=:orderid", orderid=order["orderid"])[0]["foodtype"]

        order["description"] = db.execute("Select description From info Where orderid=:orderid", orderid=order["orderid"])[0]["description"]#orders.description

        order["location"] = db.execute("Select geolocation From info Where orderid=:orderid", orderid=order["orderid"])[0]["geolocation"]
        #orders.geolocation

        order["commits"] = db.execute("Select commits From info Where orderid=:orderid", orderid=order["orderid"])[0]["commits"]

        order["time"] = db.execute("Select datetime From info Where orderid=:orderid", orderid=order["orderid"])[0]["datetime"]#orders.datetime

        order["email"] = db.execute("SELECT users.email FROM users INNER JOIN info ON users.username = info.username WHERE info.orderid=:orderid", orderid=order["orderid"])[0]["email"]

        order["venmo"] = db.execute("SELECT users.venmo FROM users INNER JOIN info ON users.username = info.username WHERE info.orderid=:orderid", orderid=order["orderid"])[0]["venmo"]

        order["phone"] = db.execute("SELECT users.phone FROM users INNER JOIN info ON users.username = info.username WHERE info.orderid=:orderid", orderid=order["orderid"])[0]["phone"]

        order["commits"] = db.execute("SELECT commits FROM info WHERE orderid=:orderid", orderid=order["orderid"])[0]["commits"]

    return render_template("myorders.html", orders=orders)


#this is were users can add an entry
@app.route("/addentry", methods=["GET", "POST"])
@login_required
def addentry():

    ##prevents unregistered users from using the app
    rows = db.execute("SELECT * FROM users WHERE userid=:userid", userid=session["user_id"])
    confirmation = rows[0]["confirmed"]
    if confirmation == 0:
        return redirect("/confirm")

    """Add an entry to the db"""
    if request.method == "POST":
        # these if not statements assure that none of the boxes in addentry are left empty
        if not (request.form.get("dorms")):
            return apology("must provide dorm", 403)

        if not (request.form.get("description")):
            return apology("must provide description", 403)

        if len (request.form.get("description")) > 25:
            return apology("please submit a shorter description", 400)

        if not (request.form.get("foodtype")):
            return apology("must provide food type", 403)

        if not (request.form.get("room number")):
            return apology("must provide room number", 403)

        if not (request.form.get("number of commits")):
            return apology("must provide commits", 403)


        #once somebody submits the form, the info is submitted into a new row in a the orders table
        bob = db.execute("INSERT INTO orders (userid, geolocation, description, piclocation, datetime, commits, foodtype, unixtime) \
                          VALUES(:userid, :geolocation, :description, :piclocation, :datetime, :commits, :foodtype, :unixtime)",
                         userid=session["user_id"], geolocation=request.form.get("dorms"),
                         description=request.form.get("description"),
                         piclocation=request.form.get("room number"), datetime="{:%Y/%m/%d %H:%M:%S}".format(datetime.now()),
                         commits=request.form.get("number of commits"), foodtype=request.form.get("foodtype"), unixtime=int(time.time()))



        if not bob:
            return apology("order taken", 400)

        #selects the order id from an order placed at time :unixtime
        orderid = db.execute("SELECT orderid FROM orders WHERE unixtime=:unixtime",
                            unixtime=int(time.time()))[0]["orderid"]

        #inserts the userid and order id into the commits table
        db.execute("INSERT INTO commits (userid, orderid) VALUES (:userid, :orderid)",
                   userid=session["user_id"], orderid=orderid)

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("addentry.html")


#this is were users login
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["userid"]

        confirmation = rows[0]["confirmed"]

        if confirmation == 1:

        # Redirect user to home page
            return redirect("/")

        else:
            return redirect("/email")

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



#registers a new user
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        #assigns variables to all the boxes in the register page
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        email = request.form.get("email")
        venmo = request.form.get("venmo")
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        phone = request.form.get("phone")

        #these if not statements make sure that all the boxes in register are filled
        if not "@college.harvard.edu" in email:
            return apology("only available for Harvard Students", 400)

        if not username:
            return apology("no username input", 400)

        if not password:
            return apology("no password input", 400)

        if not email:
            return apology("no email input", 400)

        if not firstname:
            return apology("name not valid", 400)

        if not lastname:
            return apology("name not valid", 400)

        if not phone:
            return apology("insert a valid phone number", 400)

        if not confirmation:
            return apology("password does not match confirmation", 400)

        if password != confirmation:
            return apology("password does not match confirmation", 400)

        #password requires one letter, number and symbol
        num_count = 0
        let_count = 0
        sym_count = 0
        for c in password:

            if c.isdigit():
                num_count += 1
            elif c.isalpha():
                let_count += 1
            else:
                sym_count += 1

        if not num_count and not let_count and not sym_count:
            return apology("your password needs at least one letter, number, and symbol!")

        rows = db.execute("SELECT * FROM users WHERE username = :username", username=username)
        e_rows = db.execute("SELECT * FROM users WHERE email = :email", email=email)

        # makes sure that a username is not being used
        if len(rows) != 0:
            return apology("username already taken", 400)

        #requires a unique email address
        if len(e_rows) != 0:
            return apology("email account already in use", 400)

        #hashes the password
        hashpass = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        # creating the user profile in users
        db.execute("INSERT INTO users (username, hash, email, venmo, firstname, lastname, phone, confcode) VALUES (:username, :password, :email, :venmo, :firstname, :lastname, :phone, :confcode)",
                   username=username, password=hashpass, email=email, venmo=venmo, firstname=firstname, lastname=lastname, phone=phone, confcode=(random.randrange(1000, 9999)))

        userid = db.execute("SELECT userid FROM users WHERE username=:username",
                            username=username)[0]["userid"]
        session["user_id"] = userid

        return redirect("/email")

    else:
        return render_template("register.html")

@app.route("/rating", methods=["GET", "POST"])
@login_required
def rating():

    rows = db.execute("SELECT * FROM users WHERE userid=:userid", userid=session["user_id"])
    confirmation = rows[0]["confirmed"]
    if confirmation == 0:
        return redirect("/confirm")

    if request.method == "POST":

        #assigns the varibale symbols to whatever is in the username box
        symbol = request.form.get("username")

        #assigns the int variable rating to whatever the assigned rating is
        rating = int(request.form.get("rating"))

        #this preevents users from reviewing themselves
        if symbol == db.execute("SELECT username FROM users WHERE userid=:userid", userid = session["user_id"] ):
            return apology("Invalid username", 400)


        #selects the int counter from 'symbol'
        Counter = db.execute("SELECT counter FROM users WHERE username=:username", username = symbol)
        Counters = Counter[0]["counter"]

        #increase the counter by one
        db.execute("UPDATE users SET counter = counter + 1 WHERE username=:username", username = symbol)

        #selects the rating variable from the corresponding username
        Rating = db.execute("SELECT rating FROM users WHERE username=:username", username = symbol)[0]["rating"]

        #updates the rating variable by adding the ratig int from the beginning
        db.execute("UPDATE users SET rating=:rating WHERE username=:username", rating= Rating + rating, username = symbol)

        return redirect("/")

    else:
        return render_template("rating.html" )




def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)







