#!/usr/bin/env bash
# Starts the server
# service postgresql restart
declare -A ENV_VARS
File_Lines=()

# read environment variables from file (.env.local)
readarray -t File_Lines < <(cat .env.local)
for ((i = 0; i < "${#File_Lines[@]}"; i++)) do
    line="${File_Lines[i]}"
    ENV_VARS["$(echo "$line" | cut -d ':' -f1)"]="$(echo "$line" | cut -d ' ' -f2-)"
done

env DB_DIALECT_DRIVER="${ENV_VARS['DB_DIALECT_DRIVER']}" \
    DB_USER="${ENV_VARS['DB_USER']}" \
    DB_PWORD="${ENV_VARS['DB_PWORD']}" \
    DB_HOST="${ENV_VARS['DB_HOST']}" \
    DB_PORT="${ENV_VARS['DB_PORT']}" \
    DB_NAME="${ENV_VARS['DB_NAME']}" \
    APP_ENV="${ENV_VARS['APP_ENV']}" \
    APP_MAX_SIGNIN_TRIES="${ENV_VARS['APP_MAX_SIGNIN_TRIES']}" \
    IMG_CDN_PUB_KEY="${ENV_VARS['IMG_CDN_PUB_KEY']}" \
    IMG_CDN_PRI_KEY="${ENV_VARS['IMG_CDN_PRI_KEY']}" \
    IMG_CDN_URL_EPT="${ENV_VARS['IMG_CDN_URL_EPT']}" \
    GOOGLE_MAIL_SENDER="${ENV_VARS['GOOGLE_MAIL_SENDER']}" \
    WEB_CLIENT_DOMAIN="${ENV_VARS['WEB_CLIENT_DOMAIN']}" \
    APP_SECRET_KEY="${ENV_VARS['APP_SECRET_KEY']}" \
    python3 -m api.v1.server
