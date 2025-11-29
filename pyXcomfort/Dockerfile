ARG BUILD_FROM
FROM $BUILD_FROM

# Set working directory
WORKDIR /app

# Install only git (python3 and pip are already in base-python image)
RUN apk add --no-cache git

# Clone and install pyXcomfort
RUN git clone https://github.com/olekenneth/pyXcomfort.git && \
    pip3 install --break-system-packages --no-cache-dir ./pyXcomfort && \
    rm -rf pyXcomfort

# Copy mqtt application
COPY mqtt/ /app/mqtt/

# Copy rootfs structure (S6 services, etc)
COPY rootfs /

# Install application requirements
RUN pip3 install \
    --break-system-packages \
    --no-cache-dir \
    -r /app/mqtt/requirements.txt

# Build arguments
ARG BUILD_ARCH
ARG BUILD_DATE
ARG BUILD_DESCRIPTION
ARG BUILD_NAME
ARG BUILD_REF
ARG BUILD_REPOSITORY
ARG BUILD_VERSION

# Labels
LABEL \
    io.hass.name="${BUILD_NAME}" \
    io.hass.description="${BUILD_DESCRIPTION}" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.type="addon" \
    io.hass.version=${BUILD_VERSION} \
    maintainer="Ole-Kenneth" \
    org.opencontainers.image.title="${BUILD_NAME}" \
    org.opencontainers.image.description="${BUILD_DESCRIPTION}" \
    org.opencontainers.image.vendor="Home Assistant Community Add-ons" \
    org.opencontainers.image.authors="Ole-Kenneth" \
    org.opencontainers.image.licenses="GPL-3.0" \
    org.opencontainers.image.url="https://github.com/olekenneth/hassio-addons" \
    org.opencontainers.image.source="https://github.com/${BUILD_REPOSITORY}" \
    org.opencontainers.image.documentation="https://github.com/${BUILD_REPOSITORY}/blob/main/README.md" \
    org.opencontainers.image.created=${BUILD_DATE} \
    org.opencontainers.image.revision=${BUILD_REF} \
    org.opencontainers.image.version=${BUILD_VERSION}
