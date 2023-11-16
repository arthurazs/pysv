if [ -z $VIRTUAL_ENV ]; then
    . scripts/activate
fi
sudo PYTHONTRACEMALLOC=1 $(which python3) pysv/subscriber_async.py $1

