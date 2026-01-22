FROM python:3.11-slim

WORKDIR /opt/base
COPY app/requirements.txt /opt/base/requirements.txt
RUN pip install --no-cache-dir -r /opt/base/requirements.txt
