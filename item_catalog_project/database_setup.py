""" this is the Restaurant Database """
# imports all necessary modules
# beginning of configuration code
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

# create the instance of class in order
# to inherit all the features of SQL alchemy.
Base = declarative_base()

# defining the User class
class User(Base):
    """class defines the table User for Restaurant in the Database"""
    #defines the name of the table(user)
    __tablename__ = 'user'

    # mapper variables for each of the attributes of restaurant.
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Restaurant(Base):
    """class defines the table Restaurant for Restaurant in the Database"""
    #defines the name of the table(restaurant)
    __tablename__ = 'restaurant'

    # mapper variables for each of the attributes of restaurant.
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)


    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name': self.name,
           'id': self.id
       }

class MenuItem(Base):
    """class defines the table MenuItem for Restaurant in the Database"""
    #defines the name of the table(menu_item)
    __tablename__ = 'menu_item'

    # mapper variables for each of the attributes of restaurant.
    name =Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    description = Column(String(250))
    price = Column(String(8))
    course = Column(String(250))
    restaurant_id = Column(Integer,ForeignKey('restaurant.id'))
    restaurant = relationship(Restaurant)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)


    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name': self.name,
           'description': self.description,
           'id': self.id,
           'price': self.price,
           'course': self.course
       }


# end of configuration code
# to connect to exisitng database or
# create a new one ( add tables and columns)
engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.create_all(engine)
