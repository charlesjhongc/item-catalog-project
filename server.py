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
    the_category = session.query(Categories).filter_by(name=category_name).one()
    the_item_list = session.query(Item).filter_by(category_id=the_category.id).all()
    return render_template("category_page.html",
                            category=the_category, item_list=the_item_list)


if __name__ == "__main__":
    #app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host="0.0.0.0", port=5000)
