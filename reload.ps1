 docker-compose -f .\docker\docker-compose.yml run web yarnpkg --non-interactive
 docker-compose -f .\docker\docker-compose.yml run web python manage.py collectstatic --noinput
 docker-compose -f .\docker\docker-compose.yml run web python manage.py migrate
 docker-compose -f .\docker\docker-compose.yml run web pip install -r requirements.txt