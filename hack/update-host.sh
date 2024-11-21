#!/usr/bin/env bash

set -o pipefail

hass_host="homeassistant.local"
hass_user="root"
dest_dir="/homeassistant/custom_components/"

scp -r -O ./custom_components/catgenie "${hass_user}@${hass_host}:${dest_dir}"

ssh "${hass_user}@${hass_host}" 'ha core restart'
