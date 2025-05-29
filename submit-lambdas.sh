#!/bin/bash

# launch function
zip launch-function.zip launch-function.py
aws s3 cp launch-function.zip s3://hpcic-tutorials/slackbot/launch-function.zip
rm launch-function.zip

# notify function
mkdir requests
python3 -m pip install requests -t requests --no-cache-dir
zip -r notify-function.zip notify-function.py requests*
aws s3 cp notify-function.zip s3://hpcic-tutorials/slackbot/notify-function.zip
rm -rf requests*
rm notify-function.zip
