import os

from flask import Flask, render_template, redirect, request
from prediction import Prediction
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

@app.route('/', methods=['GET'])
def get_estimate_home():
    """
    Returns the home page of the application
    that asks the user to enter the configuration
    of a vehicle and get an estimate. This is the
    first page that the user lands on.
    """
    return render_template('car_value_estimator.html')


@app.route('/', methods=['POST'])
def get_estimate_on_form_submit():
    """
    On form submit, from GET /
    the form data is submitted here to fetch relevant
    records from the database and fit a regression model
    to estimate the price. If there are less than <5> nearest records
    available, then a "cannot estimate page" is returned so that
    we do not give the users an awful prediction. 5 is a tunable number
    and can be tuned in the .env file.
    """

    # Store the form data into a temporary dictionary
    data = {
        'year': request.form['year'],
        'model': request.form['model'],
        'make': request.form['make'],
        'mileage': request.form['mileage'],
    }

    # Validation for bad user input
    if not(is_non_negative_float(data["mileage"]) and is_non_negative_float(data["year"])):
        return render_template('bad_input.html')

    # Get a list of similar records, make a prediction using
    # a regression model and return atmost 100 records used to predict.
    result = Prediction().get_estimate_and_at_most_100_records(
        make=data["make"],
        model=data["model"],
        mileage=float(data["mileage"]),
        year=float(data["year"])
    )

    # Not all predictions can be fulfilled due to there always existing
    # insufficient data / bad input in such cases where an estimate
    # cannot be made, we render a cannot estimate page.
    if result is None:
        return render_template('cannot_estimate.html')

    # Unpacking tuple
    estimate, entries = result

    # Round it to make the UX better.
    rounded_estimate = round(float(estimate))

    # Render the estimate as well as at most 100 entries.
    return render_template('car_value_estimate.html', estimate=rounded_estimate, entries=entries)


@app.route('/estimate', methods=['POST'])
def go_back_to_home():
    """
    Redirects to the home page. This controller is useful
    for the re-estimation button, where the user can go back from
    the estimate page back to the home page to redo an estimation.
    """
    return redirect("/", code=302)


def is_non_negative_float(element: any) -> bool:
    if element is None:
        return False
    try:
        return float(element) >= 0
    except ValueError:
        return False


if __name__ == '__main__':
    app.run('0.0.0.0', debug=False, port=int(os.getenv("APP_SERVER_PORT")))
