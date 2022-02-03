FROM python:3.6.15-bullseye

WORKDIR /operator
COPY . .

#FROM amazonlinux:latest
# RUN ls

RUN pip3 install --upgrade pip
# RUN pip3 install dbus-python
RUN pip3 install --upgrade -r requirements.txt

CMD ["python3","main.py"]
# FROM golang:1.13 as build
# FROM nvidia/cuda:10.0-base-ubuntu16.04

# WORKDIR /test

# COPY . operator
# RUN ls
# COPY operator /usr/bin/operator

# CMD ["operator"]