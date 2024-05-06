#!/bin/bash
cd /usr/local/nginx/html/ && ./server &
/usr/local/nginx/sbin/nginx -g "daemon off;"
echo "gva ALL start!!!"
tail -f /dev/null
