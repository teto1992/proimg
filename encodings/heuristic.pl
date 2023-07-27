:-consult('infra.pl').
:-consult('images.pl').

:- set_prolog_flag(table_space, 16000000000).

:- table transferTime/4.

maxReplicas(100).

iterativeDeepening(Placement, Cost) :-
    maxReplicas(Max), candidateNodes(Nodes), iterativeDeepening(Nodes, Placement, Cost, 1, Max), !. % stops at first solution

iterativeDeepening(Nodes, Placement, Cost, M, Max) :-
    M =< Max, \+ quickPlacement(Nodes, Placement, Cost, M), NewM is M+1,
    iterativeDeepening(Nodes, Placement, Cost, NewM, Max).
iterativeDeepening(Nodes, Placement, Cost, M, Max) :-
    M =< Max, quickPlacement(Nodes, Placement, Cost, M).

quickPlacement(Nodes, Placement, Cost, Max) :-
    findall(I, image(I,_,_), Images), 
    imagePlacement(Images, Nodes, Placement, Cost, Max).

candidateNodes(Nodes) :- findall(cand(C,N), node(N,_,C), Tmp), sort(Tmp, Nodes).

imagePlacement([I|Is], Nodes, Placement, Cost, Max) :-
    imagePlacement(Is,Nodes,P,C,Max), replicaPlacement(I,Nodes,P,Placement,C,Cost,Max).
imagePlacement([],_,[],0,_).

replicaPlacement(I, Nodes, Placement, NewPlacement, OldCost, NewCost, M) :-
    \+ transferTimesOk(I, Placement), M>0, NewM is M-1,
    image(I, Size, _), member(cand(_,N), Nodes), node(N, Storage, C), \+ member(at(I,N), Placement),
    usedHw(Placement, N, UsedHw), Storage - UsedHw >= Size,
    TmpCost is C * Size + OldCost,
    replicaPlacement(I,Nodes,[at(I, N)|Placement],NewPlacement,TmpCost, NewCost,NewM).
replicaPlacement(I, _, P, P, C, C, _) :- transferTimesOk(I, P).

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

usedHw(P, N, TotUsed) :- findall(S, (member(at(I,N), P), image(I,S,_)), Used), sum_list(Used, TotUsed).