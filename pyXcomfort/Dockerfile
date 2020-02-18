ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

RUN mkdir /app
RUN mkdir /app/mqtt
WORKDIR /app
RUN apk add git
RUN apk add python3
RUN git clone https://github.com/olekenneth/pyXcomfort.git

COPY mqtt/ /app/mqtt/

RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir ./pyXcomfort
RUN pip3 install --no-cache-dir -r mqtt/requirements.txt


CMD [ "python3", "-u", "-m", "mqtt" ]
