from flask import Flask, render_template, redirect, url_for, request, session
from sqlalchemy import *
from sqlalchemy.orm import create_session, mapper
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

# All the available sports
availSports = dbSession.query(Sport).all()

# Homepage route
@app.route('/')
def index():
    return render_template('index.html', sports = availSports)

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
    return render_template('create.html', sports=availSports)

# Add a new sport event form route
@app.route('/addevent', methods=['POST'])
def addevent():
    if request.method == 'POST' and session['user']:
        sport = request.form['sport']
        description = request.form['description']
        starttime = request.form['starttime']
        endtime = request.form['endtime']
        country = request.form['country']
        city = request.form['city']
        street = request.form['street']
        postalcode = request.form['postalcode']

        # Insert into Location and get the location id to insert the data into SportEvent

        newLocation = Location(Country=country, City=city, Street=street, PostalCode=postalcode)
        dbSession.add(newLocation)
        dbSession.flush()
        locID = dbSession.query(Location).order_by(Location.LocationID.desc()).first().LocationID

        user = session['user']
        newEvent = SportEvent(SportName=sport, Description=description, IsFull=0, StartTime=starttime, EndTime=endtime, LocationID=locID, CreatedBy=user)
        dbSession.add(newEvent)
        dbSession.flush()
        eventID = dbSession.query(SportEvent).order_by(SportEvent.EventID.desc()).first().EventID

        # Register the user who created the event
        newUserEvent = UserEvent(Username=user, EventID=eventID)
        dbSession.add(newUserEvent)
        dbSession.flush()

        return redirect(url_for('index'))

# Route for the user events page
@app.route('/myevents')
def myevents():
    if not session.has_key('user'):
        return redirect(url_for('index'))

    user = session['user']

    # Find events the user has created
    events = dbSession.query(SportEvent). \
        join(Location). \
        filter(user == SportEvent.CreatedBy). \
        all()

    return render_template('myevents.html', events=events)

# Route when the user clicks an event to edit
@app.route('/editevent/<eventID>/<action>')
def editevent(eventID, action):
    selectedEvent = dbSession.query(SportEvent).filter(SportEvent.EventID == eventID).first()
    # User chose to delete their event
    if action == "delete":
        # Delete the event
        dbSession.delete(selectedEvent)
        # Delete all the user events associated with that event
        userEventToDelete = dbSession.query(UserEvent).filter(UserEvent.EventID == eventID).all()
        for event in userEventToDelete:
            dbSession.delete(event)

        dbSession.flush()
        return render_template('myevents.html')
    else:
        # Location of the event
        location = dbSession.query(Location).filter(Location.LocationID == selectedEvent.LocationID).first()
        return render_template('editevent.html', event=selectedEvent, sports=availSports, location=location)

# Route for when the edit event form
@app.route('/modifyevent/<eID>/<lID>', methods=['POST'])
def modifyevent(eID, lID):
    if request.method == 'POST':
        sport = request.form['sport']
        description = request.form['description']
        starttime = request.form['starttime']
        endtime = request.form['endtime']
        country = request.form['country']
        city = request.form['city']
        street = request.form['street']
        postalcode = request.form['postalcode']

        # Update Location
        location = dbSession.query(Location). \
            filter(Location.LocationID == lID). \
            first()

        location.Country = country
        location.City = city
        location.Street = street
        location.PostalCode = postalcode

        dbSession.add(location)

        # Update SportEvent
        event = dbSession.query(SportEvent). \
            filter(SportEvent.EventID == eID). \
            first()

        event.SportName = sport
        event.Description = description
        event.StartTime = starttime
        event.EndTime = endtime

        dbSession.add(event)

        dbSession.flush()

        return redirect(url_for('myevents'))

# Route for joining events
@app.route('/joinevent/<eID>')
def joinevent(eID):
    user = session['user']
    # Check if the event is full
    if dbSession.query(SportEvent).filter(SportEvent.EventID == eID).first().IsFull:
        return redirect(url_for('index'))
    # Check if user is already in the event
    if dbSession.query(UserEvent). \
            filter(UserEvent.EventID == eID). \
            filter(UserEvent.Username == user).\
            all():
        return redirect(url_for('index'))

    # Add user to the event
    newUserEvent = UserEvent(Username=user, EventID=eID)
    dbSession.add(newUserEvent)
    dbSession.flush()

    # Check if the Event is full now
    currUsers = dbSession.query(SportEvent).join(UserEvent). \
        filter(UserEvent.EventID == eID). \
        count()
    # Get player limit of the event
    maxUsers = dbSession.query(Sport).join(SportEvent). \
        filter(SportEvent.EventID == eID). \
        first() .\
        PlayerLimit

    if currUsers == maxUsers:
        event = dbSession.query(SportEvent).filter(SportEvent.EventID == eID).first()
        event.IsFull = 1
        dbSession.add(event)
        dbSession.flush()

    return redirect(url_for('index'))


# Route for exit page
@app.route('/exit')
def exit():
    session.clear()
    return render_template('exit.html')

if __name__ == '__main__':
    app.run(debug = True)

