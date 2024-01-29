### Clock In

#### Running (development)
- Install Docker: `curl -sSL https://get.docker.com/ | sh`
- Install Docker Compose: `curl -L "https://github.com/docker/compose/releases/download/1.17.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && chmod +x /usr/local/bin/docker-compose`
- Copy `example.env` to `.env` and modify.
- Run all services: `docker-compose up`
- Ensure that `DB_HOST` in `.env` is set to the name of the container running mariadb. It it likely to be `clock-in-mariadb-1` or `clockin_mariadb_1`

To run `manage.py` commands:
- `docker exec -it $CONTAINER_NAME bash` where `$CONTAINER_NAME` is the name of the django container (probably `clock-in-backend-1` or `clockin_backend_1` and then run `python3 ./manage.py` from there.

