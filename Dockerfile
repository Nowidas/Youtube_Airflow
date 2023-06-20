FROM apache/airflow:2.6.2 
ADD requirements.txt . 
RUN pip install -r requirements.txt