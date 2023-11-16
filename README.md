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

pysv should be ran as sudo, it also expects an interface name, _e.g._, `lo`

```bash
git clone https://github.com/arthurazs/pysv
cd pysv
python3.10 -m venv .venv
. .venv/bin/activate

pip install .
sh publisher_sync.sh lo
```

If you wish to install async functionality:
```bash
pip install .[async]
```

If you wish to install development tools:
```bash
pip install .[dev]
```

If you wish to install both:
```bash
pip install .[async,dev]
```
