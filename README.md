# Item Catalog Project
## Introduction
This is a simple online item catalog. Anyone can view every items anytime. User can Add/Edit/Delete items after login using their Google account.
## Setup Instructions
- step0: Make sure you've got python3 environment
- step1: setup database
```python
python database_setup.py
```
- step2: insert initial items/categories into database
```python
python item_list.py
```
- step3: start http server
```python
python server.py
```
## Start Visiting Website
Open http://localhost:5000 using your browser.
## JSON API Endpoint
### Item
Append category name to http://localhost:5000/api/json/category/  
For example : http://localhost:5000/api/json/category/Macbook/
### Category
Append category name to http://localhost:5000/api/json/item/  
For example : http://localhost:5000/api/json/item/12-inchMacBook/
