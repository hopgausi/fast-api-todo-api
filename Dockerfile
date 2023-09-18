FROM python

RUN pip3 install fastapi[all]

COPY . /opt/app

WORKDIR /opt/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

