if [ -z $VIRTUAL_ENV ]; then
    . ./activate
fi
sudo PYTHONTRACEMALLOC=1 $(which python3) pysv/publisher_async.py $1

