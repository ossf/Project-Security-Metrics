FROM grafana/grafana

USER root
# RUN sed -i 's/;root_url.*/root_url = %(protocol)s:\/\/%(domain)s:%(http_port)s\/grafana\//' /etc/grafana/grafana.ini

WORKDIR /

COPY docker/grafana/entrypoint.sh .
RUN dos2unix entrypoint.sh && chmod +x entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
