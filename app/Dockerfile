# syntax=docker/dockerfile:1
FROM amancevice/pandas
ADD . /code
WORKDIR /code
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["python", "app.py"]