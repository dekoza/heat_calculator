from datetime import date
from datetime import datetime
from pony.orm import *


db = Database()

db.bind(provider='sqlite', filename='heatcalc.sqlite', create_db=True)

class Material(db.Entity):
    name = Required(str, unique=True)
    coeff_a = Required(float, default=0)
    coeff_b = Required(float, default=0)
    coeff_c = Required(float, default=0)
    max_temp = Required(float)
    coeff_200 = Optional(float, default=None, nullable=True)
    coeff_400 = Optional(float, default=None, nullable=True)
    coeff_600 = Optional(float, default=None, nullable=True)
    coeff_800 = Optional(float, default=None, nullable=True)
    coeff_1000 = Optional(float, default=None, nullable=True)
    coeff_1200 = Optional(float, default=None, nullable=True)
    coeff_1400 = Optional(float, default=None, nullable=True)
    coeff_1600 = Optional(float, default=None, nullable=True)
    price = Optional(float, default=None, nullable=True)


db.generate_mapping(create_tables=True)
