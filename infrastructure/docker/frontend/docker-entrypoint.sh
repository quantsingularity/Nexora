#!/bin/sh
# Inject runtime environment variables into the built React app
# This replaces the placeholder __REACT_APP_API_URL__ set at build time

set -e

PLACEHOLDER="__REACT_APP_API_URL__"
ACTUAL="${REACT_APP_API_URL:-/api}"

for f in /usr/share/nginx/html/static/js/*.js; do
    sed -i "s|${PLACEHOLDER}|${ACTUAL}|g" "$f"
done

echo "Nexora frontend: API URL set to ${ACTUAL}"
