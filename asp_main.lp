#script(python)
import clingo

def compute_transfer_time(size, bandwith, latency):
	r = float(size.number) / float(bandwith.number) + float(latency.number)
	return clingo.Number(int(r))
#end.

% node(ID, Capacity, Cost)
% Capacity: Total storage in MBs
% Cost: Penalty on transfering 1MB from this node
node(n1, 150, 1).
node(n2, 80, 2).
node(n3, 150, 1).

% edge(Src, Dst, Lat, Bdt)
% Src, Dst: Node Src can transfer data to node Dst
edge(n1, n3, 60, 5).
edge(n3, n1, 20, 4).
edge(n1, n2, 10, 50).
edge(n2, n1, 10, 100).

% img(ID, S, MaxTransferTime). 
% 
img(alpine, 50, 300).
img(prova, 20, 60).

% Each image is deployed to at least one node
1 { placement(Img, NodeID): node(NodeID, _, _)} :- img(Img, _, _). 

% Compute transfer times
transfer_time(Img, Src, Src, 0) :- placement(Img,Src). %node(Src, _, _), img(Img, _, _).
transfer_time(Img, Src, Dst, @compute_transfer_time(S,B,L)) :- placement(Img,Src), img(Img, S, _), edge(Src, Dst, L, B).

% There exists a node X such that Img is deployed on X and X can transfer to Dst within thresholds
transfer_ok(Img,Dst)     :- transfer_time(Img, X, Dst,T), img(Img,_,MaxTransferTime), T <= MaxTransferTime.
:- img(Img,_,_), node(Dst, _, _), not transfer_ok(Img, Dst).

% Storage threshold
:- TS = #sum{Size, Img : img(Img, Size, _), placement(Img, X)}, node(X, Cap, _), TS > Cap.

% Minimize transfer costs 
:~ placement(Img, X), node(X, _, Cost), img(Img, Size, _). [Cost * Size @ 1, Img, X]

#show.
#show placement/2.
%#show transfer_time/4.
