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
python3 -m proimg INFRASTRUCTURE IMAGES
```

where `INFRASTRUCTURE` and `IMAGES` are paths to files describing the input network topology and available container images. Check out `example_inputs` for the input atom schema.

# TODO

- [ ] Non-atom format (YAML, JSON?) for network topologies, images?
- [ ] Non-verbose output
- [ ] Fixed-precision arithmetic 
- [ ] ... 
