#!/bin/bash
IMGFILE=$(mktemp)".png"
ERRFILE=$(mktemp)".log"

xvfb-run -a -s "-screen 0 640x480x16" wkhtmltoimage "$@" "$IMGFILE" >"$ERRFILE" 2>&1

RETCODE=$?
if [ $RETCODE -ne 0 ]; then
    # command failed
    cat $ERRFILE
    exit $RETCODE
fi

md5sum < $IMGFILE

# clean up
rm $IMGFILE 2>/dev/null
rm $ERRFILE 2>/dev/null

# This script must be marked as executable and in urlwatch's PATH! Example:
# sudo chmod +x /usr/local/bin/pyvisualcompare-md5.sh
