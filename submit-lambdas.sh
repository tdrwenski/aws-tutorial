#!/bin/bash

# launch function
zip launch-function.zip launch-function.py
aws s3 cp launch-function.zip s3://hpcic-tutorials/slackbot/launch-function.zip
rm launch-function.zip

# notify function
mkdir -p notify-package
python3 -m pip install requests -t notify-package
cp notify-function.py notify-package/
zip -r notify-function.zip notify-package
aws s3 cp notify-function.zip s3://hpcic-tutorials/slackbot/notify-function.zip
rm -rf notify-package
rm notify-function.zip
