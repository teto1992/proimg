% node(Node, Storage, CostPerGB)
node(n1, 150, 1).
node(n2, 80, 2).
node(n3, 150, 1).

% link(Node1, Node2, Latency, Bandwidth)
link(n1, n3, 60, 5).
link(n3, n1, 20, 4).
link(n1, n2, 10, 50).
link(n2, n1, 10, 100).

% image(Image, Size)
image(alpine, 50).
image(prova, 20). 

maxTransferTime(alpine,300).
maxTransferTime(prova, 60).
