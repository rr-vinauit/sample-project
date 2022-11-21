#!/usr/bin/env python3

import sys
from database import database
from vehicle_datapoint import VehicleDatapoint
from unidecode import unidecode


class DataImporter:

    def __init__(self, batch_size: int):
        self.data_insert_query = "INSERT INTO db.price_datapoints_m (year, make, mileage, model, listing_price, location) VALUES (%s, %s, %s, %s, %s, %s)"
        self.db = database()
        self.batch_size = batch_size
        self.batch_id = 0
        self.counter = 0
        self.batch = []

    def import_from_file(self, file_path: str, start_from: int):

        with open(file_path) as f:

            next(f)

            for _ in range(start_from):
                next(f)

            for line in f:
                line = unidecode(line)

                line_items = line.split("|")

                self.counter += 1

                print(
                    "Importing batch #{batch}, record #{record}"
                        .format(batch=self.batch_id, record=self.counter)
                )

                self.batch.append(VehicleDatapoint(
                    year=line_items[1],
                    make=line_items[2],
                    model=line_items[3],
                    price=line_items[10],
                    mileage=line_items[11],
                    location="{city}, {state}".format(city=line_items[7], state=line_items[8])
                ))

                if self.counter >= self.batch_size:
                    self.db.make_insert_many_query(self.data_insert_query, self.batch, str(self.batch_id))
                    self.batch_id += 1
                    self.counter = 0
                    self.batch = []

            if len(self.batch) > 0:
                self.db.make_insert_many_query(self.data_insert_query, self.batch, str(self.batch_id))


batch_size = sys.argv[1]
file_location = sys.argv[2]
start_from = sys.argv[3]

DataImporter(batch_size=int(batch_size)).import_from_file(
    file_path=file_location,
    start_from=int(start_from)
)