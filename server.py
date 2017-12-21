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

# Connect to Database and create database session
engine = create_engine("sqlite:///catalog.db")
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route("/")
def mainpage():
    all_category = session.query(Categories).all()
    return render_template("publicindex.html",categories=all_category)

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
    if request.method == "GET":
        all_category = session.query(Categories).all()
        return render_template("item_add_page.html", categories=all_category)
    else:
        the_category = session.query(Categories).filter_by(
                                        name=request.form["category"]).one()
        newitem = Item(
            name=request.form["name"],
            description=request.form["description"],
            price=request.form["price"],
            category_id=the_category.id)
        session.add(newitem)
        flash("New Item %s Successfully Created" % newitem.name)
        session.commit()
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

if __name__ == "__main__":
    app.secret_key = "super_secret_key"
    app.debug = True
    app.run(host="0.0.0.0", port=5000)
