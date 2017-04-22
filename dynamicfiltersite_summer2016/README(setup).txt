Install PostgresSQL. Look at PostgreSQL installation instructions in order to install PostgreSQL.

(for mac) Install psycopg2. this is the python library to talk to posgtgres. Install with : pip install psycopg2

Install Django. Look at Introduction to Django (tutorial) to download and install Django properly. There is also a tutorial so that you can learn how to use Django. It's also most likely a good idea to go through the whole tutorial.

Django is a web dev framework/platform that uses python to interact with databases.

NOTE: you only need to do the folliwng steps to setup the database (via the django migration functionality) and run the webapp if you want to interact w/ the webapp directly. if you are only running simulations, you don't need to do this, as the simulations use the django test framework which sets up a test_xxx (e.g. test_dynamicfilter4 database and tables and runs the webapp using that. 

After you get Django working you have to populate the database, the webapp will
puke w/ errors if you don't populate the database before running the webapp. Do this via:
    `python manage.py migrate` -- Note that this may not be necessary to run the simulations, just to run the webapp in the terminal.

Then run the postgres server with : postgres -D /usr/local/var/postgres 

Set up the *webapp* user with the correct permisisons in the databsase:
    `create user webapp;` <-- (not positive if this is the correct syntax)
    `alter user webapp SUPERUSER CREATEROLE CREATEDB REPLICATION BYPASSRLS;`


Run the Django project with : python2.7 manage.py runserver
Access website at:
http://127.0.0.1:8000/dynamicfilterapp/ for user's perspective
http://127.0.0.1:8000/admin/ for admin's perspective

If you see the error below, you probably forgot to start the postgres server

    | django.db.utils.OperationalError: could not connect to server: Connection refused
    | 	Is the server running on host "localhost" (::1) and accepting
    | 	TCP/IP connections on port 5432?
    | could not connect to server: Connection refused
    | 	Is the server running on host "localhost" (127.0.0.1) and accepting
    | 	TCP/IP connections on port 5432?


If you see the error below, you probably forgot to load the database.

    | DoesNotExist at /dynamicfilterapp/
    | IP_Pair matching query does not exist.
    | Request Method:	GET
    | Request URL:	http://127.0.0.1:8000/dynamicfilterapp/
    | Django Version:	1.9.12
    | Exception Type:	DoesNotExist
    | Exception Value:	
    | IP_Pair matching query does not exist.
    | Exception Location:	/usr/local/lib/python2.7/site-packages/django/db/models/query.py in get, line 387
    | Python Executable:	/usr/local/opt/python/bin/python2.7


# OTHER README FILES:
You can also find a readme file on the general layout of the app inside the dynamicfilterapp directory.
Another readme file is inside the simulation_files directory which describes the contents of that directory and how to generate specific visualization files.
