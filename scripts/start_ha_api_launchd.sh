#!/bin/bash
# Wrapper for launchd - runs from janet-seed directory
cd "$(dirname "$0")/.."
exec /usr/bin/python3 start_ha_api.py
