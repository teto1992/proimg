:-consult('infra.pl').
:-consult('images.pl').

maxReplicas(4).

% placement/2 returns an image Placement and its Cost.
placement(Placement, Cost) :-
    findall(I, image(I,_,_), Images), maxReplicas(Max), imagePlacement(Images, Placement, Cost, Max).

iterativeDeepening(Placement, Cost) :-
    maxReplicas(Max), iterativeDeepening(Placement, Cost, 1, Max), !.

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
replicaPlacement(I, Placement, NewPlacement, OldCost, NewCost, M) :-
    \+ transferTimesOk(I, Placement), M>0, NewM is M-1,
    image(I, Size, _), node(N, Storage, C), \+ member(at(I,N), Placement),
    usedHw(Placement, N, UsedHw), Storage - UsedHw >= Size,
    TmpCost is C * Size + OldCost,
    replicaPlacement(I,[at(I, N)|Placement],NewPlacement,TmpCost, NewCost,NewM).
replicaPlacement(I, P, P, C, C,_) :- transferTimesOk(I, P).

% transferTimesOk/2 checks whether the transfer times of an image I towards all Nodes
% are met by placement P.
transferTimesOk(I,P) :-
    dif(P,[]), findall(N, node(N,_,_), Nodes),
    checkTransferTimes(I,Nodes,P).    

checkTransferTimes(I, [N|Ns], P) :-
    member(at(I,M),P), 
    image(I,_,Max), transferTime(I,M,N,T), T < Max,!, 
    checkTransferTimes(I, Ns, P).
checkTransferTimes(_, [], _).

transferTime(Image, Src, Dest, T) :-
    image(Image, Size, _), dif(Src, Dest),
    node(Src, _, _), node(Dest, _, _),
    link(Src, Dest, Latency, Bandwidth),
    T is Size * 8 / Bandwidth + Latency.
transferTime(_, N, N, 0).

usedHw(P, N, TotUsed) :-
    findall(S, (member(at(I,N), P), image(I,S,_)), Used), sum_list(Used, TotUsed).