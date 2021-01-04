# RIVM GraphQL Service Demo

## Demo code: Key files and frameworks
```
# ./rivm2016/  // Django Project
# ./rivm2016/graphql_config.py // GraphQL query object configuration
# ./rivm2016/rivm2016.gql // GraphQL query object definition

# ./impacts/  // Django app for impacts data models and processing
# ./impacts/gql/ // GraphQL Type Definitions and resolvers for impacts data model
# ./impacts/models.py // Database models
# ./impacts/management/commands/rivm_load_from_csv.py // RIVM CSV loader as a Django admin command
# ./scripts/clean_and_reset_db.py // Script to clean and reset migrations and sqlite database 

# ./data/seeds.json // seed data
# ./data/dummy_impacts.json // dummy data
# ./data/rivm2016.csv // Sample RIVM data CSV file.

# Frameworks, tools & libraries
ariadne // Schema-first python framework for GraphQL processing, https://ariadnegraphql.org/
Django // Core backend framework and WSGI application server
sqlite3 // Database
celery // For asynchronous tasks. (Work in progress, please ignore)

Docker // Containerization - as required in the task
```
# Running the Demo
## Step 1: Docker Setup
```
# Build and bring up docker containers
(shell)$ docker-compose up

# It will build and bring up 4 docker containers
## web - wsgi webserver, http://0.0.0.0:8000
## redis - redis, needed for celery tasks
## celery - celery worker container
## celery-beat - celery scheduled tasks container

```
After a successful 'docker-compose up', you should see following on the console
 ```
.
.
.
metabolic | Django version 3.1.4, using settings 'rivm2016.settings'
metabolic | Starting development server at http://0.0.0.0:8000/
metabolic | Quit the server with CONTROL-C.
```
## Step 2: Checkout the RIVM GraphQL playground
http://127.0.0.1:8000/graphql/
Try a hello Query
```
{ hello }
```
## Step 3: Reset test database and load demo data
#### Run these commands in a separate console terminal
```

# Clean & reset database: deletes migrations, db.sqlite3; runs migrations; loads seed data
(shell)$ docker-compose run web python /metabolic/scripts/clean_and_reset_db.py

# (Optional) To load seed & sample data separately, in json format
(shell)$ docker-compose exec web python manage.py loaddata data/seeds.json

# Import Indicators and Impacts data from sample csv file
(shell)$ docker-compose exec web python manage.py rivm_load_from_csv /metabolic/data/rivm2016.csv

```

## Step 4: Try sample GraphQL query for the impacts data
Copy the following sample GraphQL Query object.
```
{
  impact(entryID: 11, indicatorID: 11) {
    id
    entry {
      id
      productName
      geography {
        shortName
        name
      }
      unit
      quantity
    }
    indicator {
      id
      method
      category
      indicator
      unit
    }
  }
}

```
Paste and run the query at: 
http://127.0.0.1:8000/graphql/ .
````
# curl command equivalent of the above query
curl 'http://127.0.0.1:8000/graphql/' -H 'Accept-Encoding: gzip, deflate, br' -H 'Content-Type: application/json' -H 'Accept: application/json' -H 'Connection: keep-alive' -H 'DNT: 1' -H 'Origin: http://127.0.0.1:8000' --data-binary '{"query":"# Write your query or mutation here\n{\n  impact(entryID: 11, indicatorID: 11) {\n    id\n    entry {\n      id\n      productName\n      geography {\n        shortName\n        name\n      }\n      unit\n      quantity\n    }\n    indicator {\n      id\n      method\n      category\n      indicator\n      unit\n    }\n  }\n}\n"}' --compressed
````
