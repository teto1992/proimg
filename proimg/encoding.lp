%%%%% FACT SCHEMA
% image(ID, Size, MaxTransferTime)
% node(ID, Storage, Cost)
% link(I, J, Latency, Bandwidth)
%%%%%% 

% Each image is deployed to at least one node
1 { placement(Img, NodeID): node(NodeID, _, _)} :- image(Img, _, _). 

% Compute transfer times
transfer_time(Img, Src, Src, 0) :- placement(Img,Src). %node(Src, _, _), image(Img, _, _).
transfer_time(Img, Src, Dst, @compute_transfer_time(S,B,L)) :- placement(Img,Src), image(Img, S, _), link(Src, Dst, L, B).

% There exists a node X such that Img is deployed on X and X can transfer to Dst within thresholds
transfer_ok(Img,Dst)     :- transfer_time(Img, X, Dst,T), image(Img,_,MaxTransferTime), T <= MaxTransferTime.
:- image(Img,_,_), node(Dst, _, _), not transfer_ok(Img, Dst).

% Storage threshold
:- TS = #sum{Size, Img : image(Img, Size, _), placement(Img, X)}, node(X, Cap, _), TS > Cap.

% Minimize transfer costs 
:~ placement(Img, X), node(X, _, Cost), image(Img, Size, _). [Cost * Size @ 1, Img, X]
