# All stages use the same maintained musl/Python ABI. Only the signed SQLite
# runtime package and installed app environment reach the final image.
FROM python:3.12-alpine3.24@sha256:e6dae589c1c05976188fd3bd019afd091445fc533ed2ea29001beddc7368a9c8 AS sqlite-build
RUN apk add --no-cache abuild build-base
WORKDIR /packages-src/runtime/sqlite
COPY packaging/sqlite/APKBUILD ./APKBUILD
# The ephemeral signing key stays in this build stage. The public key verifies
# our locally built package; no untrusted-package install flag is used.
RUN abuild-keygen -a -n \
    && cp /root/.abuild/*.pub /etc/apk/keys/ \
    && abuild -F -P /packages \
    && mkdir /sqlite-output \
    && cp /packages/runtime/*/sqlite-libs-*.apk /sqlite-output/ \
    && cp /root/.abuild/*.pub /sqlite-output/

FROM python:3.12-alpine3.24@sha256:e6dae589c1c05976188fd3bd019afd091445fc533ed2ea29001beddc7368a9c8 AS build
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /build
COPY requirements.lock ./
RUN python -m venv /opt/venv \
    && /opt/venv/bin/python -m pip install --no-cache-dir pip==26.2.2 \
    && /opt/venv/bin/python -m pip install --no-cache-dir --only-binary=:all: -r requirements.lock
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN /opt/venv/bin/python -m pip install --no-cache-dir --no-deps --no-build-isolation . \
    && /opt/venv/bin/python -m pip uninstall --yes pip setuptools wheel

FROM python:3.12-alpine3.24@sha256:e6dae589c1c05976188fd3bd019afd091445fc533ed2ea29001beddc7368a9c8 AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
# Apply fixes available from this supported stable branch, never edge/testing.
# Keep apk's inventory so the FINAL runtime can be scanned accurately.
COPY --from=sqlite-build /sqlite-output /tmp/sqlite-package
RUN cp /tmp/sqlite-package/*.pub /etc/apk/keys/ \
    && apk upgrade --no-cache \
    && apk add --no-cache /tmp/sqlite-package/sqlite-libs-*.apk \
    && rm -rf /tmp/sqlite-package \
    && python -m pip uninstall --yes pip setuptools wheel \
    && addgroup -g 10001 investigator \
    && adduser -D -H -u 10001 -G investigator investigator \
    && mkdir /data \
    && chown 10001:10001 /data
COPY --from=build /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" KI_DATABASE=/data/investigations.db
WORKDIR /app
USER 10001:10001
EXPOSE 8080
CMD ["uvicorn", "kubeinvestigator.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8080", "--no-access-log"]
