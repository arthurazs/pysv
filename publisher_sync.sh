if [ -z $VIRTUAL_ENV ]; then
    . ./activate
fi
sudo $(which python3) pysv/publisher_sync.py $1

