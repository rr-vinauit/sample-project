import json
import os
import pickle
from typing import List, Tuple, Union
import pandas as pd
import numpy as np
from sklearn import linear_model
from sklearn.preprocessing import PolynomialFeatures
from sklearn.impute import SimpleImputer
from database import database
from vehicle_datapoint import VehicleDatapoint
from sklearn.metrics import mean_squared_error
import math
from dotenv import load_dotenv
import redis


class Prediction:

    db: database

    def __init__(self):
        """
        * Load .env file
        * Get an instance of the db for future ops
        * Set the minimum records required for prediction threshold
        * Set the select query template to get similar records from the db
        """
        load_dotenv()
        self.redis_session = redis.Redis(
            host=os.getenv("REDIS_HOST"),
            port=int(os.getenv("REDIS_PORT")),
            db=int(os.getenv("REDIS_DB"))
        )
        self.db = database()
        self.MINIMUM_RECORDS_REQUIRED_FOR_PREDICTION = int(os.getenv("MINIMUM_RECORDS_REQUIRED_FOR_PREDICTION"))
        self.SELECT_QUERY_TEMPLATE = os.getenv("SELECT_QUERY_TEMPLATE")

    def get_estimate_and_at_most_100_records(
            self,
            make: str,
            model: str,
            mileage: float,
            year: float
    ) -> Union[Tuple[str, List[VehicleDatapoint]], None]:

        """
        Get relevant datapoints from the database and make 
        a prediction with it by using a regression model.
        Finally, return at most 100 records used to predict and the estimate 
        """
        
        # Create a hash to retrieve from redis
        redis_key = hash(json.dumps({
            "make": make, "model": model,
            "mileage": mileage, "year": year
        }))
        
        # Try getting cached data
        cache_val = self.redis_session.get(redis_key)
        
        # unpickle and return cached results if available 
        if cache_val:
            print("fetched from cache")
            return pickle.loads(cache_val)

        # Get the closest datapoints from the database
        records = self.get_closest_make_models(make, model)

        # If there are insufficient datapoints, exit.
        if len(records) < self.MINIMUM_RECORDS_REQUIRED_FOR_PREDICTION:
            return None

        # Prepare a dataframe for prediction
        vehicle_datapoints = [
            VehicleDatapoint(
                year=r[0],
                make=r[1],
                model=r[3],
                price=r[4],
                mileage=r[2],
                location=r[5]
            ) for r in records[:100]
        ]
        
        # Get the estimates and records
        estimate = str(self.make_a_model_and_predict(records, year, mileage))
        records = vehicle_datapoints
        
        # Before returning async send it off to redis
        self.redis_session.set(
            name=redis_key,
            value=pickle.dumps((estimate, records))
        )

        return estimate, records

    @staticmethod
    def make_a_model_and_predict(records, year, mileage):
        # Prepare raw data into pandas df
        predict_for = pd.DataFrame([np.array([year, mileage])])

        # Transforming cells with empty strings as nan for further processing
        df = pd.DataFrame(records).replace("", np.nan)

        # Transforming the df by filling nan values with mean of the nan's column
        # We're picking 3 columns of interest - year, mileage, price
        xy_year_mileage_and_price = SimpleImputer(strategy='mean', missing_values=np.nan).fit_transform(df[[0, 2, 4]])

        # Input
        x_year_mileage = pd.DataFrame(xy_year_mileage_and_price[:, 0:2])

        # Output
        y_price = pd.DataFrame(xy_year_mileage_and_price[:, 2:3])

        # Declare model and degree
        pof = PolynomialFeatures(degree=2)

        # Convert the native feature space into the polynomial
        # feature space to use linear regression on.
        x_poly_year_mileage = pof.fit_transform(x_year_mileage)

        # Perform Regression
        lr = linear_model.LinearRegression()
        lr.fit(x_poly_year_mileage, y_price)

        # Naive Benchmarking without test set.
        benchmark_price_predict = lr.predict(pof.fit_transform(x_year_mileage))
        rmse = math.sqrt(mean_squared_error(y_price, benchmark_price_predict))
        average_off_by = np.sum(np.abs(y_price - benchmark_price_predict))/y_price.shape[0]
        print("RMSE = {rmse}".format(rmse=rmse))
        print("Avg. Off By = {aob}".format(aob=average_off_by))

        # Transform and Predict
        benchmark_price_predict = lr.predict(pof.fit_transform(predict_for))
        
        # get prediction as float
        unpacked_prediction = float(benchmark_price_predict[0][0])

        # If prediction is likely unrealistic, then return mean of prices
        if unpacked_prediction < 0 or unpacked_prediction > float(np.max(y_price[0])):
            avg_price = float(np.sum(y_price[0])/y_price.shape[0])
            return avg_price

        return unpacked_prediction

    def get_closest_make_models(self, make: str, model: str):
        """
        Get the closest make + models from the database
        """
        return self.db.make_select_query(
            query=self.SELECT_QUERY_TEMPLATE.format(make=make, model=model)
        )
