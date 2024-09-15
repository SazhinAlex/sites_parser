from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import declarative_base, Session




Base = declarative_base()


class LamodaItem(Base):
    __tablename__ = "LamodaItem"

    id = Column(Integer, primary_key=True)
    img_rel_path = Column(String)
    materials = Column(String)
    size_on_model = Column(String)
    model_params = Column(String)
    model_heigh = Column(String)
    lenght = Column(String)
    season = Column(String)
    color = Column(String)
    print = Column(String)
    knitwear = Column(String)
    guarantee = Column(String)
    prod_country = Column(String)
    clasp = Column(String)
    sku = Column(String)
    price = Column(String)
    description = Column(String)
    prod_url = Column(String)
    img_url = Column(String)



