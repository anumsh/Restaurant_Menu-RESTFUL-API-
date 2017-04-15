# Item-Catalog (Restaurant-Menu)
This application provides a list of items within a variety of categories as well as provide a user registration(google or facebook) and authentication system. Registered users will have the ability to post, edit and delete their own items.It utilizes Flask, SQL Alchemy, JQUERY, CSS, Java Script, and OAUTH 2 to create an Item catalog website.

# Files Included
* database_setup.py
* lotsofmenus.py
* project.py
* static folder
* templates folder

# Installation
1. Virtual Box
2. Vagrant
3. vagrant image with the following installed
  * Python 2.7
  * Flask
  * git

# setting up OAuth2.0
1. You will need to sign up for a google account and set up a client id and secret.
  * Visit: [http://console.developers.google.com](http://console.developers.google.com) for  google setup
2. You Can also signup for facebook  account and set up the client id and secret.
  * Visit: [https://developers.facebook.com/](https://developers.facebook.com/) for facebook setup

# Setting Up the Enviornment.
1. clone this repo to '<Virtual Box VM Folder>/vagrant/restaurant' folder.
2. Run 'python db_setup.py'
3. Run 'python lotsofmenus.py'
4. Run 'python project.py'
5. Open your web browser and visit [http://localhost:5000/](http://localhost:5000/)
6. The applications main page will open and you will need to click on login and then use Google+ or Facebook to login.

#License
This project is licenced under  © 2011–2017 Udacity, Inc.