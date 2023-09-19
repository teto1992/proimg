:-consult('input.pl').

placement(Placement, Cost) :-
    findall(I, image(I,_,_), Images), maxReplicas(Max), imagePlacement(Images, Placement, Cost, Max).

iterativeDeepening(Placement, Cost) :-
    maxReplicas(Max), iterativeDeepening(Placement, Cost, 1, Max), !,
    allocatedStorage(Placement,Alloc), assert(placedImages(Placement, Alloc, Cost)). % stops at first solution

iterativeDeepening(Placement, Cost, M, Max) :-
    M =< Max, \+ bestPlacement(Placement, Cost, M), NewM is M+1,
    iterativeDeepening(Placement, Cost, NewM, Max).
iterativeDeepening(Placement, Cost, M, Max) :-
    M =< Max, bestPlacement(Placement, Cost, M).

bestPlacement(Placement, Cost, Max) :-
    findall(I, image(I,_,_), Images), 
    imagePlacement(Images, Placement, Cost, Max), 
    \+ ( imagePlacement(Images, P2, C2, Max), dif(Placement, P2), C2 < Cost ).

imagePlacement([I|Is], Placement, Cost, Max) :-
    imagePlacement(Is,P,C,Max), replicaPlacement(I,P,Placement,C,Cost,Max).
imagePlacement([],[],0,_).

replicaPlacement(I, P, P, C, C,_) :- transferTimesOk(I, P).
replicaPlacement(I, Placement, NewPlacement, OldCost, NewCost, M) :-
    \+ transferTimesOk(I, Placement), M>0, NewM is M-1,
    image(I, Size, _), node(N, _, C), \+ member(at(I,N), Placement),
    storageOk(Placement, [], N, Size),
    TmpCost is C * Size + OldCost,
    replicaPlacement(I,[at(I, N)|Placement],NewPlacement,TmpCost, NewCost, NewM).

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

storageOk(Placement, Alloc, N, Size) :- 
    node(N, Storage, _), findall(S, member((N,S), Alloc), OldAllocs), sum_list(OldAllocs, OldAlloc),
    usedHw(Placement, N, UsedHw), Storage + OldAlloc - UsedHw >= Size.

usedHw(P, N, TotUsed) :- findall(S, (member(at(I,N), P), image(I,S,_)), Used), sum_list(Used, TotUsed).

allocatedStorage(P, Alloc) :- findall((N,S), (member(at(I,N), P), image(I,S,_)), Alloc).