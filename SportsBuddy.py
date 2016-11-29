from flask import Flask, render_template, redirect, url_for, request
from sqlalchemy import *
from sqlalchemy.orm import create_session
from sqlalchemy.ext.declarative import declarative_base

app = Flask(__name__)
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

session = create_session(bind=engine)

testlist = session.query(Sport).all()

for test in testlist:
    print test.SportName

# Homepage route
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sportevents/<sport>/<country>/<city>/<date>')
def sportevents(sport, country, city, date):
    return render_template('events.html')

# Sports event search form
@app.route('/search', methods=['GET'])
def search():
    if request.method == 'GET':
        sport = request.args.get('sport')
        country = request.args.get('country')
        city = request.args.get('city')
        date = request.args.get('date')
        return redirect(url_for('sportevents', sport=sport, country=country, city=city, date=date))

if __name__ == '__main__':
    app.run(debug = True)
