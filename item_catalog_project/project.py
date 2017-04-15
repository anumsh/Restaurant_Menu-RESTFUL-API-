""" this is main project file of item catalog project of FSND"""
# Flask
from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
from functools import wraps
app = Flask(__name__)

# sqlachemy
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker

# connect to database and creating  session
from database_setup import Base, Restaurant, MenuItem, User
engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Oauth
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

# google client_secrets  client_id and application_name
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"

# user login decorator
def login_required(f):
  @wraps(f)
  def decorated_function(*args, **kwargs):
    if 'username' in login_session:
      return f(*args, **kwargs)
    else:
      flash('Please login first for creating, updating or deleting the restaurant')
      return redirect('/login')
  return decorated_function



# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # render a login template
    return render_template('login.html',STATE=state)

# creating oauth google connection
@app.route('/gconnect', methods=['POST'])
def gconnect():

  # If valid state token
  if request.args.get('state') != login_session['state']:
    response = make_response(json.dumps('Invalid state token'))
    response.headers['Content-Type'] = 'application/json'
    return response

  # Get authorization code
  code = request.data

  # Upgrade authorization code to credentials object
  try:
    oauth_flow = flow_from_clientsecrets('client_secrets.json',
      scope='')
    oauth_flow.redirect_uri = 'postmessage'
    credentials = oauth_flow.step2_exchange(code)
  except FlowExchangeError:
    response = make_response(
      json.dumps('Failed to upgrade the authorization code.'), 401)
    response.headers['Content-Type'] = 'application/json'
    return response

  # Check for valid access token.
  access_token = credentials.access_token
  url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
    % access_token)
  h = httplib2.Http()
  result = json.loads(h.request(url, 'GET')[1])

  # Abort if errors
  if result.get('error') is not None:
    response.make_response(json.dumps(result.get('error')), 500)
    response.headers['Content-Type'] = 'application/json'

  # Match access token to intended user
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
    print "Token's client ID does not match an app token."
    response.headers['Content-Type'] = 'application/json'
    return response

  # Access token with the app
  stored_credentials = login_session.get('credentials')
  stored_gplus_id = login_session.get('gplus_id')
  if stored_credentials is not None and gplus_id == stored_gplus_id:
    response = make_response(json.dumps('You are connected!'), 200)
    response.headers['Content-Type'] = 'application/json'
    return response

  # Store the access token
  login_session['access_token'] = credentials.access_token
  login_session['gplus_id'] = gplus_id

  # Get user info
  userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
  params = {'access_token': credentials.access_token, 'alt': 'json'}
  answer = requests.get(userinfo_url, params=params)

  data = answer.json()

  login_session['provider'] = 'google'
  login_session['username'] = data['name']
  login_session['picture'] = data['picture']
  login_session['email'] = data['email']

  print 'User email is: ' + str(login_session['email'])
  user_id = getUserID(login_session['email'])
  if user_id:
    print 'Existing user #' + str(user_id) + ' matches this email.'
  else:
    user_id = createUser(login_session)
    print 'New user id #' + str(user_id) + ' created.'
    if user_id is None:
      print 'A new user could not be created.'
  login_session['user_id'] = user_id
  print 'Login session is tied to: id #' + str(login_session['user_id'])

  output = ''
  output += '<h2>Welcome, '
  output += login_session['username']
  output += '!</h2>'
  output += '<img src="'
  output += login_session['picture']
  output += ' " style = "width: 80px; height: 80px;border-radius: 40px;"> '
  flash("You are now logged in as %s" % login_session['username'])
  return output

# creating oauth facebook connection
@app.route('/fbconnect', methods=['POST'])
def fbconnect():

  # If valid state token
  if request.args.get('state') != login_session['state']:
    response = make_response(json.dumps('Invalid state parameter.'), 401)
    response.headers['Content-Type'] = 'application/json'
    return response

  # Get authorization code
  access_token = request.data

  # Upgrade authorization code to credentials object
  print "Facebook access token received: %s" % access_token

  app_id = json.loads(
    open('fb_client_secrets.json', 'r').read())['web']['app_id']
  app_secret = json.loads(
    open('fb_client_secrets.json', 'r').read())['web']['app_secret']
  url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
      app_id, app_secret, access_token)
  h = httplib2.Http()
  result = h.request(url, 'GET')[1]

  # Use token to get user info from API
  userinfo_url = "https://graph.facebook.com/v2.4/me"

  # Strip expire tag from access token
  token = result.split("&")[0]

  url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
  h = httplib2.Http()
  result = h.request(url, 'GET')[1]

  data = json.loads(result)
  login_session['provider'] = 'facebook'
  login_session['username'] = data["name"]
  login_session['email'] = data["email"]
  login_session['facebook_id'] = data["id"]

  # The token must be stored in the login_session in order to properly logout,
  # let's strip out the information before the equals sign in our token
  stored_token = token.split("=")[1]
  login_session['access_token'] = stored_token

  # Get user picture
  url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
  h = httplib2.Http()
  result = h.request(url, 'GET')[1]
  data = json.loads(result)

  login_session['picture'] = data["data"]["url"]

  # Check if user exists
  user_id = getUserID(login_session['email'])
  if not user_id:
    user_id = createUser(login_session)
  login_session['user_id'] = user_id

  output = ''
  output += '<h2>Welcome, '
  output += login_session['username']
  output += '!</h2>'
  output += '<img src="'
  output += login_session['picture']
  output += ' " style = "width: 80px; height: 80px;border-radius: 40px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
  flash("You are now logged in as %s" % login_session['username'])
  return output

# google disconnect function
@app.route('/gdisconnect')
def gdisconnect():
  access_token = login_session['access_token']
  if access_token is None:
      print 'Access Token is None'
      response = make_response(json.dumps('Current user not connected.'), 401)
      response.headers['Content-Type'] = 'application/json'
      return response
  url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
  h = httplib2.Http()
  result = h.request(url, 'GET')[0]
  if result['status'] != '200':
    response = make_response(
      json.dumps('Failed to revoke token for given user.', 400))
    response.headers['Content-Type'] = 'application/json'
    return response

# facebook disconnect function
@app.route('/fbdisconnect')
def fbdisconnect():
  facebook_id = login_session['facebook_id']
  access_token = login_session['access_token']
  url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
  h = httplib2.Http()
  result = h.request(url, 'DELETE')[1]
  return "you have been logged out"

# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
  if 'provider' in login_session:
    if login_session['provider'] == 'google':
      gdisconnect()
      del login_session['access_token']
      del login_session['gplus_id']
    if login_session['provider'] == 'facebook':
      fbdisconnect()
      del login_session['facebook_id']


    del login_session['username']
    del login_session['email']
    del login_session['picture']
    del login_session['user_id']
    del login_session['provider']
    flash("You have successfully been logged out.")
    return redirect(url_for('showRestaurants'))
  else:
    flash("You were not logged in")
    return redirect(url_for('showRestaurants'))


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
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


#JSON APIs to view Restaurant Information

# JSON API to view all restaurant information
@app.route('/restaurants/JSON')
def restaurantsJSON():
    restaurants = session.query(Restaurant).all()
    return jsonify(restaurants= [r.serialize for r in restaurants])

# JSON API  to view menu item based on restaurant id
@app.route('/restaurant/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
    items = session.query(MenuItem).filter_by(restaurant_id=restaurant_id)
    return jsonify(MenuItems=[i.serialize for i in items])

# JSON API to view menu info of menu id of particular restaurant id
@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def menuItemJSON(restaurant_id, menu_id):
    Menu_Item = session.query(MenuItem).filter_by(id = menu_id).one()
    return jsonify(Menu_Item = Menu_Item.serialize)


# MAIN HANDLERS -----------

# show all restaurants
@app.route('/')
@app.route('/restaurant/')
def showRestaurants():
  restaurants = session.query(Restaurant).order_by('id desc').all()
  return render_template('restaurants.html', restaurants = restaurants)

# create the  new restaurant
@app.route('/restaurant/new/', methods=['GET', 'POST'])
@login_required
def newRestaurant():
    if request.method == 'POST':
        newRestaurant = Restaurant(name=request.form['name'], user_id=login_session['user_id'])
        session.add(newRestaurant)
        session.commit()
        flash('New Restaurant %s Successfully Created' % newRestaurant.name)
        return redirect(url_for('showRestaurants'))
    else:
        return render_template('newRestaurant.html')

# update the restaurant
@app.route('/restaurant/<int:restaurant_id>/edit/', methods=['GET', 'POST'])
@login_required
def editRestaurant(restaurant_id):
    editedRestaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    owner = getUserInfo(editedRestaurant.user_id)
    if owner.id != login_session['user_id']:
        flash('You do not have access to edit %s.' % editedRestaurant.name)
        return redirect(url_for('showRestaurants'))
    if request.method == 'POST':
        if request.form['name']:
            editedRestaurant.name = request.form['name']
            session.add(editedRestaurant)
            session.commit()
            flash('Restaurant %s Successfully Edited ' % editedRestaurant.name)
            return redirect(url_for('showRestaurants'))
    else:
        return render_template('editRestaurant.html', restaurant=editedRestaurant)


# Delete the  restaurant
@app.route('/restaurant/<int:restaurant_id>/delete/', methods=['GET', 'POST'])
@login_required
def deleteRestaurant(restaurant_id):
    restaurantToDelete = session.query(Restaurant).filter_by(id=restaurant_id).one()
    owner = getUserInfo(restaurantToDelete.user_id)
    if owner.id != login_session['user_id']:
        flash('You do not have access to delete %s.' % restaurantToDelete.name)
        return redirect(url_for('showRestaurants'))
    if request.method == 'POST':
        session.delete(restaurantToDelete)
        session.commit()
        flash('%s Successfully Deleted' % restaurantToDelete.name)
        return redirect(url_for('showRestaurants', restaurant_id=restaurant_id))
    else:
        return render_template('deleteRestaurant.html', restaurant=restaurantToDelete)

# show a restaurant menu
@app.route('/restaurant/<int:restaurant_id>/')
@app.route('/restaurant/<int:restaurant_id>/menu/')
def showMenu(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    owner = getUserInfo(restaurant.user_id)
    items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).order_by('id desc').all()
    return render_template('menu.html',restaurant=restaurant, items=items, owner=owner, login_session=login_session)


# Create the new menu item
@app.route('/restaurant/<int:restaurant_id>/menu/new/', methods=['GET', 'POST'])
@login_required
def newMenuItem(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    owner = getUserInfo(restaurant.user_id)
    if owner.id != login_session['user_id']:
        flash('You do not have access to create menu item of  %s.' % restaurant.name)
        return redirect(url_for('showRestaurants'))
    if request.method == 'POST':
        newItem = MenuItem(name=request.form['name'], description=request.form['description'], price=request.form[
                           'price'], course=request.form['course'], restaurant_id=restaurant_id, user_id=restaurant.user_id)
        session.add(newItem)
        session.commit()
        flash('New Menu %s Item Successfully Created' % (newItem.name))
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    else:
        return render_template('newmenuitem.html', restaurant_id=restaurant_id)

# Edit a menu item
@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/edit', methods=['GET', 'POST'])
@login_required
def editMenuItem(restaurant_id, menu_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    owner = getUserInfo(restaurant.user_id)
    if owner.id != login_session['user_id']:
        flash('You do not have access to edit the menu item of %s.' % restaurant.name)
        return redirect(url_for('showRestaurants'))
    editedItem = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
        if request.form['name'] or request.form['description'] or \
                    request.form['price'] or request.form['course']:
            editedItem.name = request.form['name']
            editedItem.description = request.form['description']
            editedItem.price = request.form['price']
            editedItem.course = request.form['course']
            session.add(editedItem)
            session.commit()
            flash('Menu Item Successfully Edited')
            return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    else:
        return render_template('editmenuitem.html', restaurant=restaurant, item=editedItem)


# Delete the  menu item
@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/delete', methods=['GET', 'POST'])
@login_required
def deleteMenuItem(restaurant_id, menu_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    owner = getUserInfo(restaurant.user_id)
    if owner.id != login_session['user_id']:
        flash('You do not have access to delete the menu item of  %s.' % restaurant.name)
        return redirect(url_for('showRestaurants'))
    itemToDelete = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Menu Item %s Successfully Deleted' % (itemToDelete.name))
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    else:
        return render_template('deletemenuitem.html', restaurant=restaurant, item=itemToDelete)


# run at localhost:5000/  port
if __name__ == '__main__':
  app.secret_key = 'super_secret_key'
  app.debug = True
  app.run(host = '0.0.0.0', port = 5000)
