# Security Metrics

The purpose of this project is to collect, organize, and provide interesting security metrics
for open source projects to stakeholders, including users.

This project is in early development and we welcome community support. For more information or
to get involved, please see our [workgroup](https://github.com/ossf/wg-identifying-security-threats)
page.

## Developement

Steps to setting up a local development environment. The main components are:

* Database - PostgreSQL (for storing data)
* Azure Function (for handling the ingestion to the database)
* Grafana (to view the results)
* Collectors (doing things, and then calling the Azure Function).

To start, clone this repository locally.

### Database

Install PostgreSQL server (tested on PostgreSQL 12) and create a user and a database. 
You can intialize the database with the following script:

```
-- Table: public.metrics

-- DROP TABLE public.metrics;

CREATE TABLE public.metrics
(
    id bigint NOT NULL DEFAULT nextval('metrics_id_seq1'::regclass),
    package_url text COLLATE pg_catalog."default" NOT NULL,
    key text COLLATE pg_catalog."default" NOT NULL,
    value text COLLATE pg_catalog."default",
    "timestamp" timestamp without time zone NOT NULL,
    properties jsonb,
    CONSTRAINT metrics_pkey PRIMARY KEY (id)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.metrics
    OWNER to grafana;
-- Index: package_url_key_idx

-- DROP INDEX public.package_url_key_idx;

CREATE INDEX package_url_key_idx
    ON public.metrics USING btree
    (package_url COLLATE pg_catalog."default" ASC NULLS LAST, key COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
```

### Azure Function

Install [.NET 5](https://dotnet.microsoft.com/download/dotnet/5.0) and the 
[Azure Functions Core Tools](https://www.npmjs.com/package/azure-functions-core-tools).

From the `src/ingestion` directory, run `dotnet build` and then from the
`src/ingestion/MetricAPI` directory, run `func start --csharp`. You should see
`AddMetric: [POST] http://localhost:7071/api/AddMetric` after a few seconds. This will be
the value of `METRIC_API_ENDPOINT`.

Stop the function, and then modify the `src/ingestion/MetricAPI/local.settings.json` file, filling
in the values from what you specified when you created the database.

```
   "DATABASE_CONNECTION_STRING": "Server=localhost;Database=<DATABASE>;Port=5432;User Id=<USERNAME>;Password=<PASSWORD>;Ssl Mode=Require;",
```

Restart the function, and then add a sample record to ensure things are working properly:

```
curl -X POST -d '[{"package_url":"pkg:npm/test","operation":"replace","key":"testkey","values":[{"value":"hello"}]}]' "$METRIC_API_ENDPOINT"
```

Check the database table to ensure that a row has been inserted into the metrics table.

### Grafana

Now we need to install Grafana, which you can download from
[grafana.com/grafana/download](https://grafana.com/grafana/download). You can install the 
open source version, and login to the site.

We can now link Grafana to PostgreSQL. Click on the gear icon in Grafana, create a new data source
(PostgreSQL), and fill in the host (localhost), database, user, and password. Click `Save & Test`.

Now access the [JSON model](https://openssf-security-dashboard-dev1.westus2.cloudapp.azure.com/d/R8Sxg4xMz/project-security-metrics?editview=dashboard_json&orgId=1)
of the current dashboard. You can copy this JSON and paste it into the settings / JSON model 
page in your local Grafana instance. It's possible that you'll need to
[install](https://grafana.com/docs/grafana/latest/plugins/installation/) a few plugins in order
for the new dashboard to render properly:

* Button Panel
* Dynamic text
* GitHub
* JSON API
* Pie Chart
* Traffic Lights

### Collectors

Finally, we can run the collectors. First, ensure that you have Python 3 installed (tested
with Python 9, but any recent 3.x version should work).

Create a Python virtual environment (`python -mvenv venv`) and activate it
(`venv\Scripts\activate` on Windows, `source venv/bin/activate` on Linux). Then install
the Python requirements (`pip install -r requirements.txt`).

Now create a .env file

```
LIBRARIES_API_KEY=XXXXXXXXXXXX
METRIC_API_ENDPOINT=http://localhost:7071/api/AddMetric    (from above)
GITHUB_API_TOKEN=XXXXXXXXXXXX
```

You can get a LIBRARIES_API_KEY from libraries.io from the [settings](https://libraries.io/account)
page. and the GITHUB_API_TOKEN from GitHub.

## Running It

Well you made it this far, it's now time to run something through the system:

```
python run_jobs.py --analyze pkg:npm/left-pad
```

Check to ensure that some data is collected and is available in the dashboard. (You'll need
to refresh the page.)

To refresh all data, you'll need to run `python run_jobs.py --analyze-all`.

## Reporting Issues

There are definitely bugs in this documentation and in the individual components. Please
report them as a GitHub issue and we'll get it fixed/improved.
