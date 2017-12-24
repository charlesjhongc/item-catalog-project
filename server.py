from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from flask import make_response
from flask import session as login_session
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from database_setup import Base, User, Categories, Item
import random
import string
import httplib2
import json
import requests


app = Flask(__name__)

CLIENT_ID = json.loads(
    open("client_secrets.json", "r").read())["web"]["client_id"]
APPLICATION_NAME = "Item Catalog Application"

# Connect to Database and create database session
engine = create_engine("sqlite:///catalog.db")
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route("/")
def mainpage():
    all_category = session.query(Categories).all()
    return render_template("publicindex.html",categories=all_category)

@app.route("/login")
def loginpage():
    return render_template("login.html")

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print("done!")
    return output

def createUser(login_session):
    newUser = User(name=login_session["username"], email=login_session[
                   "email"], picture=login_session["picture"])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session["email"]).one()
    print("Id of user-{} is {}".format(login_session["email"], user.id))
    return user.id

def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user

def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

@app.route("/category/<category_name>/")
def category_page(category_name):
    the_category = session.query(Categories).filter_by(
                                        name=category_name).one()
    the_item_list = session.query(Item).filter_by(
                                    category_id=the_category.id).all()
    all_category = session.query(Categories).all()
    return render_template("category_page.html",
                            categories=all_category,
                            category=the_category,
                            item_list=the_item_list)

@app.route("/category/<category_name>/<item_name>/")
def item_page(category_name, item_name):
    the_item = session.query(Item).filter_by(name=item_name).one()
    return render_template("item_page.html", item=the_item)

@app.route("/category/additem/", methods=["GET","POST"])
def item_add_page():
    if "username" not in login_session:
        return redirect("/login")
    elif request.method == "GET":
        all_category = session.query(Categories).all()
        return render_template("item_add_page.html", categories=all_category)
    else:
        the_category = session.query(Categories).filter_by(
                                        name=request.form["category"]).one()
        newitem = Item(
            name=request.form["name"],
            description=request.form["description"],
            price=request.form["price"],
            category_id=the_category.id,
            user_id=login_session["user_id"])
        session.add(newitem)
        session.commit()
        flash("New Item %s Successfully Created" % newitem.name)
        return redirect(url_for("category_page", category_name=the_category.name))

@app.route("/category/<item_name>/edit/", methods=["GET","POST"])
def item_edit_page(item_name):
    the_item = session.query(Item).filter_by(name=item_name).one()
    if request.method == "GET":
        all_category = session.query(Categories).all()
        return render_template("item_edit_page.html", categories=all_category, item=the_item)
    else:
        the_category=session.query(Categories).filter_by(
                                            name=request.form["category"]).one()
        the_item.name=request.form["name"]
        the_item.description=request.form["description"]
        the_item.price=request.form["price"]
        the_item.category_id=the_category.id
        session.add(the_item)
        session.commit()
        return redirect(url_for("item_page", category_name=the_category.name, item_name=the_item.name))

@app.route("/category/<item_name>/delete/", methods=["GET","POST"])
def item_delete_page(item_name):
    the_item = session.query(Item).filter_by(name=item_name).one()
    if request.method == "GET":
        return render_template("item_delete_page.html", item=the_item)
    else:
        session.delete(the_item)
        session.commit()
        return redirect(url_for("mainpage"))

@app.route("/category/<category_name>/JSON")
def categoryJSON(category_name):
    the_category = session.query(Categories).filter_by(
                                        name=category_name).one()
    items = session.query(Item).filter_by(category_id=the_category.id).all()
    return jsonify(Item=[i.serialize for i in items])

if __name__ == "__main__":
    app.secret_key = "super_secret_key"
    app.debug = True
    app.run(host="0.0.0.0", port=5000)
