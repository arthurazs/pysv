# PySV

IEC 61850 SV (Sampled Values) publisher/subscriber in Python.

## Requirements

Ubuntu 20.04.

```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.10-venv
```

## Quickstart

pysv should be run as sudo, it also expects an interface name, _e.g._, `lo`, which can be changed in the `.env` file.

```bash
git clone https://github.com/arthurazs/pysv
cd pysv
python3.10 -m venv .venv
. .venv/bin/activate

pip install .[async]
sudo .venv/bin/python -m pysv -ap  # async publisher
sudo .venv/bin/python -m pysv -as  # async subscriber
sudo .venv/bin/python -m pysv -debug # publisher in C
# sudo nice -n -20 chrt --fifo 99 .venv/bin/python -m pysv -debug  # minimum niceness, maximum priority
```
### Optional quickstart

Instead of using the default file specified in the `.env` file, you can change it through the command line interface:

```bash
sudo .venv/bin/python -m pysv -ap path/to/another_file.csv
```

## TODO

- [ ] Fix ruff issues
- [ ] Use logging instead of print
- [ ] Make the pub/sub sync/async modules customizable
- [ ] Write unit tests

