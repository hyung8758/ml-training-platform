#!/usr/bin/env bash
# Generate a ClearML fixed_users bcrypt password hash without exposing the password.
# Run on the ClearML Server host as a user permitted to access Docker.

set -euo pipefail

container_name="${CLEARML_APISERVER_CONTAINER:-clearml-apiserver}"

if ! command -v docker >/dev/null 2>&1; then
  echo 'docker is required but was not found.' >&2
  exit 1
fi

if ! docker inspect --format '{{.State.Running}}' "$container_name" 2>/dev/null \
  | grep -qx 'true'; then
  echo "ClearML API container is not running: ${container_name}" >&2
  exit 1
fi

read -rsp 'ClearML Web password: ' password
printf '\n' >&2
read -rsp 'Repeat password: ' password_confirm
printf '\n' >&2

if [[ -z "$password" || "$password" != "$password_confirm" ]]; then
  unset password password_confirm
  echo 'Password is empty or does not match.' >&2
  exit 1
fi
unset password_confirm

printf '%s' "$password" \
  | docker exec -i "$container_name" python3 -c '
import base64
import bcrypt
import sys

print(base64.b64encode(bcrypt.hashpw(sys.stdin.buffer.read(), bcrypt.gensalt())).decode())
'
unset password
