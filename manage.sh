user="$USER"
group="$(id -gn)"
container_name="${WEB_CONTAINER_NAME:-clockin-backend-1}"
docker exec -it "$container_name" bash -c "python3 ./manage.py $@"
sudo chown -R $user:$group app
