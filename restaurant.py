from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem
engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()
myfirstrestaurant = Restaurant(name = "pizza Place")
session.add(myfirstrestaurant)
session.commit()
resto=session.query(Restaurant).all()
for rest in resto:
    print rest.id
    print rest.name

