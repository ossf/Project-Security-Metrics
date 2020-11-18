# Security Metrics

The purpose of this project is to collect, organize, and provide interesting security metrics
for open source projects to stakeholders, including users.

This project is in early development and we welcome community support. For more information or
to get involved, please see our [workgroup](https://github.com/ossf/wg-identifying-security-threats)
page.

## Development

Steps to setting up a local development environment.

1. Clone the repository (`git clone https://github.com/ossf/Project-Security-Metrics`).
1. Ensure that you have [Docker Compose](https://docs.docker.com/compose/) installed.
1. Copy `docker/web/.env.dev.web-example` to `docker/web/.env.dev.web` and modify the values
   in that file for your local environment.
1. Do the same thing for `docker/db/.env.dev.db-example` and `docker/worker/.env.dev.worker-example`.
1. Run `start.ps1`.
1. Open https://127.0.0.1:8000

We use Docker Compose to configure multiple containers:

* Web: This is a Django web server that serves requests.
* Nginx: This is a web server that sits in front of Web.
* Db: This is a PostgreSQL database that stores data.
* Worker: This is a worker role that performs various tasks.
* Web Worker: This is a worker role that uses the Web image to perform certain tasks.
* Redis: This is a local caching server.
* Azurite: This is a local Azure Storage emulator (for the work queue).

When running this service, the Web container runs code from the host system, so you can
develop code and have it immediately reflect within the web application.

The database, cache, and queue are all persistent.

To refresh static files, perform database migrations, or update packages, run `reload.ps1`.

To stop the service, run `stop.ps1`. If you want to remove all persistent data, run
`docker-compose -f .\docker\docker-compose.yml down -v`.