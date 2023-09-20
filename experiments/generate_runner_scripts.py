import argparse


p = argparse.ArgumentParser()
p.add_argument("min_nodes", type=int, default=25)
p.add_argument("max_nodes", type=int, default=1000)
p.add_argument("step_nodes", type=int, default=25)
# 0 -> barabasi albert
# 1 -> Erdos-Renyi
# 2 -> Watts-Strogatz
p.add_argument("structure", type=int, default=0)


args = p.parse_args()

random_seeds : 'list[int]' = list(range(0,10))
m_list = [1,3]

# uno script lancia, per ogni numero di nodi, l'istanza i

for current_m in m_list:
    for seed in random_seeds:
        fp = open(f"run_b_a_{current_m}_{seed}.sh","w")
        for number_of_nodes in range(args.min_nodes, args.max_nodes + 1, args.step_nodes):
            s = f"{number_of_nodes}/b_a_{number_of_nodes}_{current_m}_{seed}.pl"
            rs = f"time python3 ../proimg/__main__.py {s} images.lp\n"
            fp.write(rs)
            print(s)
        fp.close()