from flask import Flask, render_template, redirect, url_for, request, session
from sqlalchemy import *
from sqlalchemy.orm import create_session
from sqlalchemy.ext.declarative import declarative_base

app = Flask(__name__)
app.secret_key = 'secret key'
# Create an engine and get the metadata
Base = declarative_base()
engine = create_engine('mysql://root:12345678@localhost/se3309db')
metadata = MetaData(bind=engine)

# Map each database table
class Location(Base):
    __table__ = Table('Location', metadata, autoload=True)


class Message(Base):
    __table__ = Table('Message', metadata, autoload=True)


class SkillLevel(Base):
    __table__ = Table('SkillLevel', metadata, autoload=True)


class Sport(Base):
    __table__ = Table('Sport', metadata, autoload=True)


class SportEvent(Base):
    __table__ = Table('SportEvent', metadata, autoload=True)


class SystemUser(Base):
    __table__ = Table('SystemUser', metadata, autoload=True)


class UserEvent(Base):
    __table__ = Table('UserEvent', metadata, autoload=True)

dbSession = create_session(bind=engine)


# Homepage route
@app.route('/')
def index():
    # Load all the available sports
    sports = dbSession.query(Sport).all()
    return render_template('index.html', sports = sports)

# Sport events page route
@app.route('/sportevents/<sport>/<country>/<city>/<date>')
def sportevents(sport, country, city, date):
    # Query SportEvent to find matching events
    events = dbSession.query(SportEvent).join(Location).\
        filter(sport == SportEvent.SportName).\
        filter(country == Location.Country).\
        filter(city == Location.City).\
        filter(date == func.DATE(SportEvent.StartTime)).\
        all()

    print events
    return render_template('events.html', events = events)

# Login page route
@app.route('/login')
def login():
    return render_template('login.html')

# Sports event search form route
@app.route('/search', methods=['GET'])
def search():
    if request.method == 'GET':
        sport = request.args.get('sport')
        country = request.args.get('country')
        city = request.args.get('city')
        date = request.args.get('date')
        return redirect(url_for('sportevents', sport=sport, country=country, city=city, date=date))

# Register form route
@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        # Error message if username is already taken
        error = None
        fName = request.form['fName']
        lName = request.form['lName']
        username = request.form['username']
        password = request.form['password']

        # Check if username exists
        if dbSession.query(SystemUser).filter(SystemUser.Username == username).count():
            error = "Username already exists. Choose a different username"
        else:
            #Valid registration made
            newUser = SystemUser(Username=username, UserPassword=password, FirstName=fName, LastName=lName)
            dbSession.add(newUser)
            dbSession.flush()
            return redirect(url_for('login'))

    return render_template('login.html', error=error)

# Login authentication form route
@app.route('/authenticate', methods=['POST'])
def authenticate():
    if request.method == 'POST':
        # Error message if username does not match password
        error = None
        username = request.form['username']
        password = request.form['password']

        # Find if there is a username password match in the database
        if dbSession.query(SystemUser).filter(SystemUser.Username == username).\
                filter(SystemUser.UserPassword == password).\
                count():
            session['user'] = username
            return redirect(url_for('index'))
        else:
            #Invalid login
            error = "Username and password does not match"
            return render_template('login.html', authError = error)

# Create sport event page route
@app.route('/createevent')
def createevent():
    # Load all the available sports
    sports = dbSession.query(Sport).all()
    return render_template('create.html', sports=sports)

# Add a new sport event form route
# @app.route('addevent', methods=['POST'])
# def addevent():
#     if request.method == 'POST':


if __name__ == '__main__':
    app.run(debug = True)

# TODO
# -make all form fields that are required required and accompany other form fields in the route
