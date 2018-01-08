from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, User, Categories, Item

engine = create_engine("sqlite:///catalog.db")
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


user1 = User(name="Tom", email="tom@gmail.com")
session.add(user1)
session.commit()

catalog1 = Categories(name="Macbook")
session.add(catalog1)
session.commit()

catalog2 = Categories(name="Macbook Air")
session.add(catalog2)
session.commit()

catalog3 = Categories(name="Macbook Pro")
session.add(catalog3)
session.commit()

catalog3 = Categories(name="iMac")
session.add(catalog3)
session.commit()

catalog3 = Categories(name="iMac Pro")
session.add(catalog3)
session.commit()

catalog3 = Categories(name="Mac Pro")
session.add(catalog3)
session.commit()

catalog3 = Categories(name="Mac mini")
session.add(catalog3)
session.commit()


item1 = Item(name="12-inch MacBook with 1.2GHz CPU",
    description="Light. Years ahead.",
    price="1,299",
    category_id=1, user_id=1)
session.add(item1)
session.commit()

item2 = Item(name="12-inch MacBook with 1.3GHz CPU",
    description="Light. Years ahead.",
    price="1,599",
    category_id=1, user_id=1)
session.add(item2)
session.commit()

print("added menu items!")
