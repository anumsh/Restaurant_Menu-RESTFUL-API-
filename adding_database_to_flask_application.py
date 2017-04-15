from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem
app = Flask(__name__)

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/')
@app.route('/restaurant')
def HelloWorld():
    restaurant = session.query(Restaurant).first()
    print restaurant.name
    print restaurant.id
    items = session.query(MenuItem).filter_by(restaurant_id=restaurant.id)
    #return items.restaurant.name
    output = ''
    for i in items:
        output += i.restaurant.name
        output += '</br>'
        output += str(i.restaurant.id)
        output += '</br>'
        output += i.name
        output += '</br>'
        output += i.price
        output += '</br>'
        output += '</br>'
    return output
if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
