# `proimg`
Declarative container image placer to cloud-edge networks.

1. launch the `experiments.py` script to generate a sample infrastructure
2. launch either `asp_main.lp` or `lp_main.pl` to find image placements

# Installing
```bash
python3 -m build
pip3 install dist/*.whl
```

# Usage
```bash
usage: __main__.py [-h] [-d] [-o OUTPUT] infrastructure images

positional arguments:
  infrastructure        File describing network architecture.
  images                File with images to be placed.

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug
  -o OUTPUT, --output OUTPUT
                        Save optimal solution to file as a JSON.
```

# TODO

- [ ] Non-atom format (YAML, JSON?) for network topologies, images?
- [ ] Non-verbose output
- [ ] Fixed-precision arithmetic 
- [ ] ... 
