ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG=C.UTF-8

RUN mkdir -p /app/mqtt

WORKDIR /app

RUN apk add --no-cache \
    git \
    python3 \
    py3-pip

RUN git clone https://github.com/olekenneth/pyXcomfort.git && \
    pip3 install --break-system-packages ./pyXcomfort

COPY mqtt/ /app/mqtt/

RUN python3 -m pip install --break-system-packages -r mqtt/requirements.txt

CMD [ "python3", "-u", "-m", "mqtt" ]
