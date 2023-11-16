if [ -z $VIRTUAL_ENV ]; then
    . ./activate
fi
sudo $(which python3) pysv/subscriber_sync.py $1

