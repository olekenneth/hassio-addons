ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8
RUN apk add python3

RUN mkdir /app
COPY . /app
RUN sh /app/create-galleries.sh

WORKDIR /share

CMD [ "python3", "-u", "-m", "http.server", "8099" ]
