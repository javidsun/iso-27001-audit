FROM quay.io/keycloak/keycloak:26.5.2

USER root

# Install curl using whichever package manager exists in the base image.
RUN set -eux; \
    if command -v microdnf >/dev/null 2>&1; then \
        microdnf install -y curl && microdnf clean all; \
    elif command -v dnf >/dev/null 2>&1; then \
        dnf -y install curl && dnf clean all; \
    elif command -v yum >/dev/null 2>&1; then \
        yum -y install curl && yum clean all; \
    elif command -v apt-get >/dev/null 2>&1; then \
        apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*; \
    else \
        echo "ERROR: no supported package manager found to install curl" >&2; \
        exit 1; \
    fi

USER 1000