import sys
import pathlib

import clingo
import argparse

ENCODING = (pathlib.Path(__file__).parent / 'encoding.lp').as_posix()

class Context:
	def __init__(self, precision=None):
		# TODO: Unità di misura, cifre aritmetica
		self.precision = precision

	@staticmethod
	def compute_transfer_time(size, bandwith, latency):
		r = float(size.number) * float(8.0) / float(bandwith.number) + float(latency.number)
		return clingo.Number(int(r))

# TODO: Parsing available images into atoms?
# TODO: Parsing infrastructure into atoms? 

def parse_args():
	p = argparse.ArgumentParser(usage="python3 -m proimg infrastructure images")
	p.add_argument('infrastructure', type=str, help='File describing network architecture.')
	p.add_argument('images', type=str, help='File with images to be placed.')
	p.add_argument('-v', '--verbose', action='store_true')
	args = p.parse_args()

	return args

def on_model(model):
	print(f"Found a solution with cost {model.cost}. Optimal? {model.optimality_proven}")
	if not model.optimality_proven:
		return True

	proj = [sym for sym in model.symbols(atoms=True) if sym.match("placement", 2)]
	print("\n".join("{}.".format(x) for x in proj))	

	return False

if __name__ == '__main__':
	args = parse_args()

	ctl = clingo.Control(["--models=1", "--opt-mode=optN"])
	ctl.load(ENCODING)
	ctl.load(args.infrastructure)
	ctl.load(args.images)

	ctl.ground(context=Context())
	ctl.solve(on_model=on_model)
