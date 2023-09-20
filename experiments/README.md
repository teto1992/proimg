# How to Run the Experiments
Run `./generate_datasets.sh`: it generates 40 folders named 25, 50, 75 ... up to 1000 (included) with step 25. Each folder contains 20 files. 
For now, it only generates networks following the barabasi albert structure. 
The name of each file contains the random seed used (from 0 to 9, included) and the m (1 or 3, relevant for barabasi albert).
Moreover, it generates other 20 files in the current folder needed to run the experiments.
Each of these file runs, for every folder, the instance generated with seed i.

The images and the replicas are the same for all the experiments and are stored in the current folder at `images.lp`.
You can modify these by changing the values stored in the `images_string` sting into `generate_networks.py`.

Run each file with `.sh` extension in the current folder.
