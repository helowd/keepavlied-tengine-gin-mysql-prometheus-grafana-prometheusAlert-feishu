FROM tengine:3.0.0

WORKDIR /opt/go-gin-web

ENV LANG=en_US.utf8

COPY deploy/docker/entrypoint.sh .
COPY deploy/docker/build/ /usr/local/nginx/html/
COPY web/.docker-compose/nginx/conf.d/nginx.conf /usr/local/nginx/conf/conf.d/default.conf

RUN set -ex \
    && echo "LANG=en_US.utf8" > /etc/locale.conf \
    && chmod +x ./entrypoint.sh \
    && echo "start" > /dev/null

EXPOSE 80 443

ENTRYPOINT ["/opt/go-gin-web/entrypoint.sh"]
