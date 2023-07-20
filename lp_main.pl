:-consult('input.pl').

% placement/2 returns a cost-optimal image Placement and its Cost.
placement(Placement, Cost) :-
    findall(I, image(I,_), Images), 
    imagePlacement(Images, Placement, Cost), 
    \+ ( imagePlacement(Images, P2, C2), dif(Placement, P2), C2 < Cost ).

% imagePlacement/3 recursively places images on nodes by using replicaPlacement/5.
imagePlacement([I|Is], Placement, Cost) :-
    imagePlacement(Is,P,C), 
    replicaPlacement(I,P,Placement,C,Cost).
imagePlacement([],[],0).

% replicaPlacement/5 repeatedly places an image I onto a set of nodes, 
% by extending Placement into NewPlacement until transferTimesOk/2 holds.
% It computes the NewCost of NewPlacement by updating the OldCost of Placement.
replicaPlacement(I, Placement, NewPlacement, OldCost, NewCost) :-
    \+ transferTimesOk(I, Placement),
    image(I, Size), node(N, Storage, C), \+ member(at(I,N), Placement),
    usedHw(Placement, N, UsedHw), Storage - UsedHw >= Size,
    TmpCost is C * Size + OldCost,
    replicaPlacement(I,[at(I, N)|Placement],NewPlacement,TmpCost, NewCost).
replicaPlacement(I, P, P, C, C) :- transferTimesOk(I, P).

% transferTimesOk/2 checks whether the transfer times of an image I towards all Nodes
% are met by placement P.
transferTimesOk(I,P) :-
    dif(P,[]), findall(N, node(N,_,_), Nodes),
    checkTransferTimes(I,Nodes,P).    

checkTransferTimes(I, [N|Ns], P) :-
    member(at(I,M),P), 
    maxTransferTime(I,Max), transferTime(I,M,N,T), T < Max,!, 
    checkTransferTimes(I, Ns, P).
checkTransferTimes(_, [], _).

transferTime(Image, Src, Dest, T) :-
    image(Image, Size), dif(Src, Dest),
    node(Src, _, _), node(Dest, _, _),
    link(Src, Dest, Latency, Bandwidth),
    T is Size / Bandwidth + Latency.
transferTime(_, N, N, 0).

usedHw(P, N, TotUsed) :-
    findall(S, (member(at(I,N), P), image(I,S)), Used), sum_list(Used, TotUsed).