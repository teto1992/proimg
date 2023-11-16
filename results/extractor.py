import sys
import pandas
import statistics

# argv[1]: input file

if len(sys.argv) != 2:
    print("Usage: extractor.py <size>")
    sys.exit()
    
# from each line of the input:
# - split line ,
# - compute the average over the lines
# - extract ASP, heu, cr, and declace time
# - extract # of ASP, heu, cr, and declace failures (cost -1)

# header line:
# step [0],
# asp_time [1],
# heu_time [2],
# cr_time [3],
# declace_time [4],
# asp_cost [5],
# heu_cost [6],
# cr_cost [7],
# declace_cost [8],
# asp_placement [9],
# heu_placement [10],
# cr_placement [11],
# declace_placement [12]

fout = open(f"ba_{sys.argv[1]}_data.txt","w")
for n_img in [4,8,12]:
    filename = f"ba_{sys.argv[1]}n_{n_img}i.csv"
    data = pandas.read_csv(filename)
    # la = data["asp_time"].to_list()
    # print(la)

    lv = ["asp_time","heu_time","cr_time","declace_time","asp_cost","heu_cost","cr_cost","declace_cost"]

    n_fail_asp = 0
    n_fail_heu = 0
    n_fail_cr = 0
    n_fail_declace = 0
    
    print(n_img, end=",")
    print(n_img, end=",",file=fout)

    for val in lv:
        # print(f"val: {val}")
        ld = data[val].to_list()
        l_ok = [d for d in ld if d != -1]
        # use a dict
        if val == "asp_cost":
            n_fail_asp = len(ld) - len(l_ok)
        elif val == "heu_cost":
            n_fail_heu = len(ld) - len(l_ok)
        elif val == "cr_cost":
            n_fail_cr = len(ld) - len(l_ok)
        elif val == "declace_cost":
            n_fail_declace = len(ld) - len(l_ok)
        
        if len(l_ok) > 0:
            res = statistics.mean(l_ok)
        else:
            res = -1 # no valid data point
        
        print(res, end=",")
        print(res, end=",",file=fout)

    print(f"{n_fail_asp},{n_fail_heu},{n_fail_cr},{n_fail_declace}",file=fout)
    print(f"{n_fail_asp},{n_fail_heu},{n_fail_cr},{n_fail_declace}")
    print(f"{n_fail_asp},{n_fail_heu},{n_fail_cr},{n_fail_declace}")
fout.close()