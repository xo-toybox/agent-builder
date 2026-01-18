#!/bin/bash
cd "$(dirname "$0")"

[ -f .tmp/backend.pid ] && kill $(cat .tmp/backend.pid) 2>/dev/null && rm .tmp/backend.pid
[ -f .tmp/frontend.pid ] && kill $(cat .tmp/frontend.pid) 2>/dev/null && rm .tmp/frontend.pid
