# mini_app_template
Django boilerplate for creating fast an app!

## Branches
Two starting points, so a new product can begin from the one closest to its spec:

| Branch | What it has | Start here when |
|---|---|---|
| `one_model_app` | Auth (login/logout), Bootstrap sidebar layout, CRUD of a single `Service` model | The product is one main entity |
| `multi_model_app` | Everything above + roles, signup, dashboard with stats and an appointment-booking domain | The product has users with different roles and related entities |

### Example domain in `multi_model_app`
A service agenda: clients sign up and book services; admins confirm or cancel the bookings.
Each model is there to show one relationship pattern that can be renamed to fit another domain:

| Model | Relationship | Pattern it shows |
|---|---|---|
| `User` | `role` field (admin / client) | Role-based access (`@admin_required`, `user.is_admin`) |
| `Category` ↔ `Service` | N-N (`ManyToManyField`) | Checkbox form field, `prefetch_related`, `annotate(Count)` |
| `Appointment` → `User` | 1-N, `on_delete=CASCADE` | Ownership: each client only sees their own records (`visible_to`) |
| `Appointment` → `Service` | 1-N, `on_delete=PROTECT` | Deleting a service with bookings is blocked and reported to the user |
| `Appointment` | N-N between users and services, with its own data | Status workflow, double-booking rule (form + DB `UniqueConstraint`) |

## Authors
- dcordovao

## Initial setup
### 1. Setup the environment variables
The environment variables are in `dev.env` that is used by docker-compose.yml and `prod.env` that is used by `docker-compose.prod.yml`.
Make sure to edit them and change at least the `POSTGRES_PASSWORD` and `DJANGO_SECRET_KEY`

### 2. Build the containers
First you need to install Docker and Docker compose in your machine:
[Install Docker](https://docs.docker.com/engine/install/)
Then build the docker containers. Open your terminal and write:
```bash
$ docker-compose up --build
```
This will run all the build scripts that create the necessary environment for the app to run. Nothing will be installed in your computer. Instead Docker will create containers that run Linux and install all the necessary libraries and dependencies and run the app in there.

### 3. Initialize the app
I have prepared a script called `initapp` that will initialize the app for you. To run it open a new terminal and type:
```bash
$ docker ps
```
This will list all containers that are currently running. We need the `CONTAINER ID` for `app`.
Then type the following (replace `CONTAINER ID` with the id your container has.):
```bash
docker exec -it <CONTAINER ID> ./manage.py initapp
```
This will initialize the database, create tables for caching and create an admin user with whom you can access the admin panel.
> The admin user will be initialized with these credentials:
> username: admin
> password: admin

You can create an admin user with other credentials like so:
```bash
docker exec -it <CONTAINER ID> ./manage.py initapp --username=admin --password=mysuperstrongpassword
```

## Running in production:
### Configure the webserver
Execute the script that will install dummy certificates so that ngix can start:
```bash
chmod +x webserver/scripts/init_letsencrypt.sh
sudo ./webserver/scripts/init_letsencrypt.sh
```

### Building the container
Use the `docker-compose.prod.yml` instead and follow the instructions of step "3. Initialize the app":
```bash
$ docker-compose -f docker-compose.prod.yml up --build
```
