# The first instruction is what image we want to base our container on
# We Use an official Python runtime as a parent image
FROM python:3.8

# The enviroment variable ensures that the python output is set straight
# to the terminal with out buffering it first
ENV PYTHONUNBUFFERED 1

ENV DJANGO_ENV dev
ENV DOCKER_CONTAINER 1

# create root directory for - RIVM GraphQL Service
RUN mkdir /rivm_gql_service

# COPY the contents for this Django project into the container at /rivm_gql_service
COPY . /rivm_gql_service/

# Set the working directory to /rivm_gql_service
WORKDIR /rivm_gql_service

# Install python packages specified in requirements.txt
RUN pip install -r /rivm_gql_service/requirements.txt

EXPOSE 8000