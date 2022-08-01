# Security Metrics

The purpose of this project is to collect, organize, and provide interesting security metrics
for open source projects to stakeholders, including users.

This project is in early development and we welcome community support. For more information or
to get involved, please see our [workgroup](https://github.com/ossf/wg-identifying-security-threats)
page.

## Installing a Local Development Environment

Setting up a basic development environment is straightforward:

1. Clone the repository (`git clone https://github.com/ossf/Project-Security-Metrics`).
1. Ensure that you have [Docker Compose](https://docs.docker.com/compose/) installed.
1. Copy `docker/web/.env.dev.web-example` to `docker/web/.env.dev.web` and modify the values
   in that file for your local environment.
1. Do the same thing for `docker/db/.env.dev.db-example` and `docker/worker/.env.dev.worker-example`.
1. Run `start.ps1`.
1. Open https://127.0.0.1:8000

The first configuration file has a template at `docker/db/.env.dev.db-example`, which should
be copied or renamed to `docker/db/.env.dev.db`. There is only one field in that file
that you need to change, the password for your local PostgreSQL database.

The second configuration file has a template at `docker/web/.env.dev.web-example`, which
similarly should be copied or renamed to `docker/web/.env.dev.web`. Open this file in your
favorite text editor and update the `SECRET_KEY`, `DJANGO_SUPERUSER_PASSWORD` and
`DB_PASSWORD` fields. Use the same value for `DB_PASSWORD` as you specified in the first
configuration file.

When you're done, you can try building and running the Docker application. From the root
of the repository, run:

`docker-compose -f docker/docker-compose.yml build`

This should take 5-10 minutes to complete (perhaps more, depending on bandwidth and the
images that Docker needs to pull).

Now you can run the application with:

`docker-compose -f docker/docker-compose.yml up`

**NOTE**: You might see some errors the first or second time you run this. I know about
them, but haven't had cycles to fix them yet. Press Ctrl-C to exit the application,
and then re-run `docker-compose -f docker/docker-compose.yml run`. In my testing,
"third time's the charm". I hope this to be fixed shortly.

## First Time Usage

Open a web browser to [http://localhost:8000](http://localhost:8000). You should see an 
error message from Django. (This is also a bug that hasn't been fixed yet.)

Now open a web browser to [http://localhost:8000/grafana/](http://localhost:8000/grafana/).
That last slash is important. You should be asked to login. Do so using `admin/admin` and then
change the password to whatever you'd like. Now you'll have an empty Grafana instance.

Click on the gear icon on the left and select `Data Sources` / `Add data source`. Choose
PostgreSQL and use the following details:

* Host: `db`
* Database: `metricdb` (unless you changed it in `.env.dev.db` above)
* User: `metricuser` (unless you changed it in `.env.dev.db` above)
* Password: Use what you specified in `.env.dev.db` above.
* SSL Mode: `disable`.
* Version: 12 (though it might work set as other versions too).

Click `Save & Test`.

Now we just need to import the current dashboard configuration. Click on the icon with
four squares (above the gear icon) on the left and select `Manage Dashboards`. Press
`Import`.

Now open a new browser tab and access
[this URL](https://metrics.openssf.org/grafana/d/default/metric-dashboard?editview=dashboard_json&orgId=1).
You can get to it by accessing [metrics.openssf.org](https://metrics.openssf.org), opening
a dashboard, clicking on the share icon on the top, then `Export` and `View JSON`. Copy the JSON
content and paste it into your local instance and click `Save`.

Now you have Grafana set up, but you don't have any data yet. Open a command prompt and check
to see what the name of the containers are:

```
PS C:\dev> docker ps -a
CONTAINER ID   IMAGE            COMMAND                  CREATED       STATUS       PORTS                    NAMES
cf11aee4c908   docker_nginx     "/docker-entrypoint.…"   9 hours ago   Up 9 hours   0.0.0.0:8000->80/tcp     docker_nginx_1
cd8978797dd9   docker_web       "/usr/src/app/entryp…"   9 hours ago   Up 9 hours   8000/tcp                 docker_web_1
010bd148d19a   redis:alpine     "docker-entrypoint.s…"   9 hours ago   Up 9 hours   6379/tcp                 docker_redis_1
f64a3ccd0ac4   docker_grafana   "/entrypoint.sh"         9 hours ago   Up 9 hours   3000/tcp                 docker_grafana_1
7c431e863842   postgres         "docker-entrypoint.s…"   9 hours ago   Up 9 hours   0.0.0.0:5432->5432/tcp   docker_db_1
```

We need to kick off a reload job on the web server:

```
PS C:\dev> docker exec -it docker_web_1 /bin/bash
root@cd8978797dd9:/usr/src/app/src/management# /etc/cron.daily/openssf-reload-all

OpenSSF: Starting data reload.
[25/Apr/2021 21:25:06] INFO [load_bestpractices_data.handle:25] Gathering all best practice data.
[25/Apr/2021 21:25:06] DEBUG [connectionpool._new_conn:971] Starting new HTTPS connection (1): bestpractices.coreinfrastructure.org:443
[25/Apr/2021 21:25:06] DEBUG [connectionpool._new_conn:971] Starting new HTTPS connection (1): bestpractices.coreinfrastructure.org:443
...
```

Now grab a snack, or let it run overnight. For me, this initial load took approximately 7 hours
to complete. (This is absurdly long, and something that we'll need to fix.)

Once the process has started, you can immediately access the site. The main URL
(http://localhost:8000) should work, and Grafana should have some projects populated.

## Actualy doing development work

The Django application is set up to run from the host machine, so you can immediately edit
files and see them reflected in the running application. For example, change some text
in the `src/management/app/templates/app/index.html` file and then access http://localhost:8000.
If you change the model, you'll need to either reload the application or execute the command
in the running container like we did above.

If you change an import job, then you'll need to ensure it's properly plumbed together, which
means:

* Creating the import job in `src/management/app/management/commands/`
* Adding the job to `docker/web/cron.daily`.

## Reporting Issues

There are definitely bugs in this documentation and in the individual components. Please
report them as a GitHub issue and we'll get it fixed/improved.
