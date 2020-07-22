ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

WORKDIR /share
RUN apk add python3

RUN pip3 install --upgrade pip
RUN pip3 install simple-photo-gallery
RUN sh create-galleries.sh

CMD [ "python3", "-u", "-m", "http.server", "8099" ]
