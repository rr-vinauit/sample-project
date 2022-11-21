from typing import Tuple

from table_row import TableRow


class VehicleDatapoint(TableRow):
    make: str
    model: str
    price: str
    mileage: str
    location: str
    year: str

    def __init__(self, make: str, model: str, price: str, mileage: str, location: str, year: str):
        self.make = make
        self.model = model
        self.price = price
        self.mileage = mileage
        self.location = location
        self.year = year

    def to_database_representation(self) -> Tuple:
        return self.year, self.make, self.mileage, self.model, self.price, self.location
