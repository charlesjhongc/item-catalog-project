from flask import Flask, render_template, request,\
                redirect, jsonify, url_for, flash
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

from google.oauth2 import id_token
from google.auth.transport import requests as grequests


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
    return render_template("publicindex.html", categories=all_category)


@app.route("/login")
def loginpage():
    state = "".join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session["state"] = state
    # return "The current session state is %s" % login_session['state']
    return render_template("login.html", STATE=state)


@app.route("/gconnect", methods=["POST"])
def gconnect():
    token = request.form.get("idtoken")
    try:
        idinfo = id_token.verify_oauth2_token(
                                        token, grequests.Request(), CLIENT_ID)
        # Or, if multiple clients access the backend server:
        # idinfo = id_token.verify_oauth2_token(token, requests.Request())
        # if idinfo['aud'] not in [CLIENT_ID_1, CLIENT_ID_2, CLIENT_ID_3]:
        #     raise ValueError('Could not verify audience.')
        if idinfo['iss'] not in [
                        'accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        # If auth request is from a G Suite domain:
        # if idinfo['hd'] != GSUITE_DOMAIN_NAME:
        #     raise ValueError('Wrong hosted domain.')

        # ID token is valid. Get the user's
        # Google Account ID from the decoded token.
        login_session["username"] = idinfo["name"]
        login_session["picture"] = idinfo["picture"]
        login_session["email"] = idinfo["email"]
        login_session["token"] = token
        print(idinfo["email"]+" Logged in")
        user_id = getUserID(idinfo["email"])
        if not user_id:
            user_id = createUser(login_session)
        login_session["user_id"] = user_id
        return redirect("/")
    except ValueError:
        # Invalid token
        pass


@app.route("/gdisconnect")
def gdisconnect():
    del login_session["username"]
    del login_session["email"]
    del login_session["picture"]
    del login_session["user_id"]
    del login_session["token"]
    return redirect("/")


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
    return render_template(
        "category_page.html", categories=all_category,
        category=the_category, item_list=the_item_list)


@app.route("/category/<category_name>/<item_name>/")
def item_page(category_name, item_name):
    the_item = session.query(Item).filter_by(name=item_name).one()
    if "user_id" in login_session:
        return render_template(
            "item_page.html", item=the_item, userid=login_session["user_id"])
    else:
        return render_template("item_page.html", item=the_item)


@app.route("/category/additem/", methods=["GET", "POST"])
def item_add_page():
    # user can't get this page without login
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
        return redirect(
            url_for("category_page", category_name=the_category.name))


@app.route("/category/<item_name>/edit/", methods=["GET", "POST"])
def item_edit_page(item_name):
    # user can't get this page without login
    if "username" not in login_session:
        return redirect("/login")
    the_item = session.query(Item).filter_by(name=item_name).one()
    # user can't get this page if lack ownership of the item
    if login_session["user_id"] != the_item.user_id:
        return render_template("accessdenied.html")
    if request.method == "GET":
        all_category = session.query(Categories).all()
        return render_template(
            "item_edit_page.html", categories=all_category, item=the_item)
    else:
        the_category = session.query(Categories).filter_by(
                                        name=request.form["category"]).one()
        the_item.name = request.form["name"]
        the_item.description = request.form["description"]
        the_item.price = request.form["price"]
        the_item.category_id = the_category.id
        session.add(the_item)
        session.commit()
        return redirect(url_for(
            "item_page", category_name=the_category.name,
            item_name=the_item.name))


@app.route("/category/<item_name>/delete/", methods=["GET", "POST"])
def item_delete_page(item_name):
    # user can't get this page without login
    if "username" not in login_session:
        return redirect("/login")
    the_item = session.query(Item).filter_by(name=item_name).one()
    # user can't get this page if lack ownership of the item
    if login_session["user_id"] != the_item.user_id:
        return render_template("accessdenied.html")
    if request.method == "GET":
        return render_template("item_delete_page.html", item=the_item)
    else:
        session.delete(the_item)
        session.commit()
        return redirect(url_for("mainpage"))


@app.route("/api/json/item/<item_name>/")
def itemJSON(item_name):
    the_item = session.query(Item).filter_by(
                                        name=item_name).one()
    return jsonify(Item=the_item.serialize)


@app.route("/api/json/category/<category_name>/")
def categoryJSON(category_name):
    the_category = session.query(Categories).filter_by(
                                        name=category_name).one()
    items = session.query(Item).filter_by(category_id=the_category.id).all()
    return jsonify(Item=[i.serialize for i in items])

if __name__ == "__main__":
    app.secret_key = "super_secret_key"
    app.debug = True
    app.run(host="0.0.0.0", port=5000)
