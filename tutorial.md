# **Project Security Metrics Dashboard Tutorial**

This is a walkthrough of the Security Metrics Dashboard. The goal of this dashboard is to provide an aggregate of helpful metrics to help you determine the security posture of a software package.

# Sample Project: Kubernetes

To start, we will take a look at the dashboard for the Kubernetes project found [here](https://metrics.openssf.org/grafana/d/default/metric-dashboard?orgId=1&var-PackageURL=pkg:github%2Fkubernetes%2Fkubernetes&var-PackagePath=github%2Fkubernetes%2Fkubernetes). If you click that link you will be taken to the following page:

![Alt text](/images/kubernetes_dashboard.png?raw=true "Kubernetes Dashboard")


# Breaking Down the metrics

### Project Overview

The Project Overview section is broken into the following three components:

![Alt text](/images/kubernetes_dashboard_general_overview.png?raw=true "Kubernetes Dashboard")
<br><br>

| Summary                 | License                     | Additional Information |
| ----------------------- | --------------------------- | -------------------- |
| The purpose of the package, primarily sourced from GitHub. |The license the project was released under. This is important as this outlines boundaries for the use and/or distribution of the package.|Any important additional information regarding the project.|


### Detected URLs

The Detected URLs section contains a list of relevant URLs detected that relate to the package, including the following:

![Alt text](/images/kubernetes_dashboard_urls.png?raw=true "Kubernetes Dashboard Detected URLs")
<br><br>

| Repository                 | Project Home Page                     | OpenSSF Best Practices Assessment | Is it Maintained? |
| ----------------------- | --------------------------- | -------------------- |
|The package's source code repository. |The package's primary website/homepage.|Detailed breakdown of package's adherence to security analysis, reporting, policies and other security practices.|Median resolution time and percentage of open issues of the package.||


### Security Reviews

This section contains an aggregated list of security reviews hosted by the Open Source Security Foundation. The [Security Reviews](https://github.com/ossf/security-reviews) project is a work in progress and most packages (kubernetes included) do not yet have reviews posted. When information is here, it will consist of the date, severity, and link to each review. A sample security review can be found at this [link](https://github.com/ossf/security-reviews/blob/main/reviews/linux-kernel/linux-kernel-vuln-remediation.md).

### OpenSSF Project Criticality

The OpenSSF Project Criticality section contains a collection of metrics pulled from the OpenSSF's [Criticality Score](https://github.com/ossf/criticality_score) project. This project generates a score (on a scale of 0-100), which defines the influence and importance of a project, for a given package.

The criticality score, along with the metrics used to determine the score (and the date all of this information was recorded) is detailed below:

![Alt text](/images/kubernetes_dashboard_criticality.png?raw=true "Kubernetes Dashboard Detected URLs")
<br><br>

|# Watchers|# Contributers|Project Age|# Recent Releases|Months Since Last Update|# Dependents|
| ----------------------- | --------------------------- | -------------------- |
|Number of watchers this project has received on GitHub|Number of contributors with commits|Years since this project was first created|Number of releases in the last year|Time since the project was last updated (in months)|Number of project mentions in the commit messages|

### OpenSSF Best Practices Badge Program

The OpenSSF Best Practices Badge Program section contains a collection of metrics pulled from the Linux Foundation Core Infrastructure Initiative (CII). This project provides a detailed breakdown of each package's performance of important practices such as security analysis, reporting, and policies. The information is used to generate a badge level for a given package.

The best practices badge level, along with the metrics used to determine the badge level (and the date all of this information was recorded) is detailed below:

![Alt text](/images/kubernetes_dashboard_best_practices.png?raw=true "Kubernetes Dashboard Detected URLs")
<br><br>

|Static Analysis|Dynamic Analysis|Security Error Awareness|Only Strong Crypto|2FA Required|Secure Design Knowledge|Vulnerability Reporting|
| ----------------------- | --------------------------- | -------------------- |
|The project uses static analysis and fixes any bugs found.|The project uses dynamic analysis and fixes any bugs found.|At least one of the project's primary developers knows of common kinds of errors that lead to vulnerabilities in this kind of software, as well as at least one method to counter or mitigate each of them.|The project uses basic good cryptographic practices.|The project requires use of two-factor authentication.|The project has at least one primary developer who knows how to design secure software.|The project publishes the process for reporting vulnerabilities on the project site.|

### OpenSSF Scorecard

The OpenSSF Scorecard section contains a set of security health metrics for each package that are automatically detected via the [Security Scorecards](https://github.com/ossf/scorecard) project. These metrics are also compiled to generate an overall score (on a scale of 0-100).

A breakdown of these security metrics is detailed below:

![Alt text](/images/kubernetes_dashboard_scorecard.png?raw=true "Kubernetes Dashboard Detected URLs")
<br><br>

|Active|CI Tests|Code Review|Multiple Orgs. Contributing|Frozen Deps|Fuzzing|Packaging|Pull Requests|SAST|SECURITY.md|Signed Releases|Signed Tags|
| ----------------------- | --------------------------- | -------------------- |
|Did the project get any commits in the last 90 days?|Does the project run tests in CI, e.g. GitHub Actions, Prow?|Does the project require code review before code is merged?|Does the project have contributors from at least two different organizations?|Does the project declare and freeze dependencies?|Does the project use fuzzing tools, e.g. OSS-Fuzz?|Does the project build and publish official packages from CI/CD, e.g. GitHub Publishing?|Does the project use Pull Requests for all code changes?|Does the project use static code analysis tools, e.g. CodeQL, SonarCloud?|Does the project contain a security policy?|Does the project cryptographically sign releases?|Does the project cryptographically sign release tags?|

### Other Metrics

Finally, additional metrics that are useful to understand the overall security posture of a software package are included here.

![Alt text](/images/kubernetes_dashboard_other.png?raw=true "Kubernetes Dashboard Detected URLs")
<br><br>

|Security Reviews|
| ----------------------- |
|✓ → no severe reviews <br> ✘ → at least one severe review <br> ? → no reviews|
