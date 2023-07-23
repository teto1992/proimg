#script(python)
import clingo

def compute_transfer_time(size, bandwith, latency):
	r = float(size.number) * float(8.0) / float(bandwith.number) + float(latency.number)
	return clingo.Number(int(r))
#end.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
image(alpine, 5, 300).
image(busybox, 5, 300).

node(n0,16,3).
node(n1,2,2).
node(n2,8,3).
node(n3,128,2).
node(n4,8,5).
node(n5,128,3).
node(n6,16,4).
node(n7,4,1).
node(n8,256,1).
node(n9,2,1).
node(n10,8,4).
node(n11,8,2).
node(n12,32,5).
node(n13,16,2).
node(n14,256,3).
node(n15,32,4).
node(n16,16,4).
node(n17,64,4).
node(n18,4,2).
node(n19,32,2).
link(n0,n1,100,1000).
link(n0,n2,25,200).
link(n0,n3,150,1000).
link(n0,n5,150,1000).
link(n0,n6,150,20).
link(n0,n7,50,1000).
link(n0,n8,5,20).
link(n0,n9,5,200).
link(n0,n10,10,100).
link(n1,n4,100,50).
link(n1,n5,100,100).
link(n1,n17,10,10).
link(n2,n4,5,50).
link(n2,n7,5,20).
link(n2,n8,25,200).
link(n2,n10,50,50).
link(n3,n4,10,20).
link(n3,n11,100,100).
link(n4,n5,50,20).
link(n4,n6,150,20).
link(n4,n8,25,20).
link(n4,n18,50,200).
link(n4,n19,25,20).
link(n5,n6,5,100).
link(n5,n9,100,10).
link(n5,n11,50,20).
link(n5,n14,10,1000).
link(n5,n15,50,50).
link(n6,n7,150,500).
link(n6,n9,150,20).
link(n6,n10,100,100).
link(n6,n12,25,50).
link(n6,n13,10,200).
link(n6,n15,5,20).
link(n6,n16,10,1000).
link(n6,n18,10,10).
link(n6,n19,100,20).
link(n7,n12,50,1000).
link(n7,n13,25,100).
link(n7,n14,150,50).
link(n7,n15,100,50).
link(n8,n11,10,1000).
link(n9,n12,150,1000).
link(n9,n16,50,100).
link(n11,n13,100,100).
link(n11,n16,50,50).
link(n12,n14,150,100).
link(n12,n17,150,20).
link(n14,n18,25,200).
link(n16,n17,10,500).
link(n17,n19,5,50).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% broken_node/1       - unavailable nodes
% broken_link/2       - unavailable links
% current_placement/2 - an Img is currently deployed on a Node

% Each image is deployed to at least one node (among the non-broken ones)
1 { placement(Img, NodeID): node(NodeID, _, _), not broken_node(NodeID) } :- image(Img, _, _). 

% Compute transfer times
transfer_time(Img, Src, Src, 0) :- placement(Img,Src). 
transfer_time(Img, Src, Dst, @compute_transfer_time(S,B,L)) :- placement(Img,Src), image(Img, S, _), link(Src, Dst, L, B), not broken_link(Src, Dst).

% There exists a node X such that Img is deployed on X and X can transfer to Dst within thresholds
transfer_ok(Img,Dst)     :- transfer_time(Img, X, Dst,T), image(Img,_,MaxTransferTime), T <= MaxTransferTime.
:- image(Img,_,_), node(Dst, _, _), not transfer_ok(Img, Dst).

% Storage threshold
:- TS = #sum{Size, Img : image(Img, Size, _), placement(Img, X)}, node(X, Cap, _), TS > Cap.

% Minimize transfer costs for new images to be placed only 
:~ placement(Img, X), not current(Img, X), node(X, _, Cost), image(Img, Size, _). [Cost * Size @ 1, Img, X]

#show.
#show placement/2.
%#show transfer_time/4.
