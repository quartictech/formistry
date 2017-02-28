FROM python:3-onbuild

COPY requirements.txt /formistry/
RUN pip install --no-cache-dir -r /formistry/requirements.txt
COPY *.py /formistry/

EXPOSE 8080
CMD [ "python", "/formistry/formistry.py" ]
