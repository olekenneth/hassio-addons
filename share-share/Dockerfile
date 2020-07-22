ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

RUN mkdir /app
WORKDIR /app
RUN apk add python3

CMD [ "python3", "-u", "http.server", "8080" ]
