% :-consult('infra.pl').
% :-consult('images.lp').

maxReplicas(5).

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

% placement/2 returns an image Placement and its Cost.
placement(Placement, Cost) :-
    findall(I, image(I,_,_), Images), maxReplicas(Max), imagePlacement(Images, Placement, Cost, Max).

iterativeDeepening(Placement, Cost) :-
    maxReplicas(Max), iterativeDeepening(Placement, Cost, 1, Max), !. % stops at first solution

iterativeDeepening(Placement, Cost, M, Max) :-
    M =< Max, \+ bestPlacement(Placement, Cost, M), NewM is M+1,
    iterativeDeepening(Placement, Cost, NewM, Max).
iterativeDeepening(Placement, Cost, M, Max) :-
    M =< Max, bestPlacement(Placement, Cost, M).

% bestPlacement/2 returns a cost-optimal image Placement and its Cost,
% with at most Max replicas per image.
bestPlacement(Placement, Cost, Max) :-
    findall(I, image(I,_,_), Images), 
    imagePlacement(Images, Placement, Cost, Max), 
    \+ ( imagePlacement(Images, P2, C2, Max), dif(Placement, P2), C2 < Cost ).

% imagePlacement/3 recursively places (at most Max replica) images on nodes by using replicaPlacement/5.
imagePlacement([I|Is], Placement, Cost, Max) :-
    imagePlacement(Is,P,C,Max), replicaPlacement(I,P,Placement,C,Cost,Max).
imagePlacement([],[],0,_).

% replicaPlacement/5 repeatedly places an image I onto a set of nodes, 
% by extending Placement into NewPlacement until transferTimesOk/2 holds.
% It computes the NewCost of NewPlacement by updating the OldCost of Placement.
replicaPlacement(I, P, P, C, C,_) :- transferTimesOk(I, P).
replicaPlacement(I, Placement, NewPlacement, OldCost, NewCost, M) :-
    \+ transferTimesOk(I, Placement), M>0, NewM is M-1,
    image(I, Size, _), node(N, Storage, C), \+ member(at(I,N), Placement),
    hwOk(Placement,N,Size), TmpCost is C * Size + OldCost,
    replicaPlacement(I,[at(I, N)|Placement],NewPlacement,TmpCost, NewCost, NewM).

% transferTimesOk/2 checks whether the transfer times of an image I towards all Nodes
% are met by placement P.
transferTimesOk(I,P) :-
    dif(P,[]), findall(N, node(N,_,_), Nodes),
    checkTransferTimes(I,Nodes,P).    

checkTransferTimes(I, [N|Ns], P) :-
    member(at(I,M),P), 
    image(I,_,Max), transferTime(I,M,N,T), T < Max,!, % one source is enough
    checkTransferTimes(I, Ns, P).
checkTransferTimes(_, [], _).

transferTime(Image, Src, Dest, T) :-
    image(Image, Size, _), dif(Src, Dest),
    node(Src, _, _), node(Dest, _, _),
    link(Src, Dest, Latency, Bandwidth),
    T is Size * 8 / Bandwidth + Latency.
transferTime(_, N, N, 0).

hwOk(Placement, N, Size) :- usedHw(Placement, N, UsedHw), Storage - UsedHw >= Size.

usedHw(P, N, TotUsed) :- findall(S, (member(at(I,N), P), image(I,S,_)), Used), sum_list(Used, TotUsed).