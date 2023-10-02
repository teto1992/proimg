:- consult('input.pl').
:- dynamic(placedImages/3).
:- dynamic(image/3).
:- dynamic(node/3).
:- dynamic(link/4).
:- dynamic(maxReplicas/1).

crStep([], [], Placement, Cost) :-
    \+ placedImages(_,_,_), iterativeDeepening(quick, Placement, Cost).
crStep(P, KOImages, NewPlacement, Cost) :- 
    placedImages(P, Alloc, _), imagesToPlace(Images), candidateNodes(Nodes), 
    reasoningStep(Images, Nodes, P, [], POk, Alloc, KOImages),
    crID(KOImages, Nodes, POk, NewPlacement, Cost).
    
reasoningStep([I|Is], Nodes, P, POk, NewPOk, Alloc, KO) :-
    findall(at(I,N), member(at(I,N), P), INs), append(INs, POk, TmpPOk),
    image(I, Size, _), checkTransferTimes(I, Nodes, TmpPOk), checkStorage(I, Size, TmpPOk, Alloc), !, 
    reasoningStep(Is, Nodes, P, TmpPOk, NewPOk, Alloc, KO).
reasoningStep([I|Is], Nodes, P, POk, NewPOk, Alloc, [I|KO]) :-
    % \+ (image(I,Size, _), checkTransferTimes(I,Nodes,Placement), checkStorage(I, Placement, Alloc)),
    reasoningStep(Is, Nodes, P, POk, NewPOk, Alloc, KO).
reasoningStep([], _, _, POk, POk, _, []).

placement(Placement, Cost) :-
    findall(I, image(I,_,_), Images), findall(N, node(N,_,_), Nodes),
    maxReplicas(Max), imagePlacement(Images, Nodes, Placement, Cost, Max).

crID(KOImages, Nodes, PartialPlacement, NewPlacement, Cost) :-
    maxReplicas(Max), imagePlacement(KOImages, Nodes, PartialPlacement, NewPlacement, 0, _, Max),
    cost(NewPlacement, Cost), allocatedStorage(NewPlacement,Alloc),
    retract(placedImages(_,_,_)), assert(placedImages(NewPlacement, Alloc, Cost)).
crID([],_,P,P,Cost) :-  
    allocatedStorage(P,Alloc),
    retract(placedImages(_,_,_)), assert(placedImages(P, Alloc, Cost)).

iterativeDeepening(Mode, Placement, Cost) :-
    imagesToPlace(Images), candidateNodes(Nodes), maxReplicas(Max), 
    time(iterativeDeepening(Mode, Images, Nodes, Placement, _, 1, Max)), !,
    cost(Placement, Cost), allocatedStorage(Placement,Alloc), 
    assert(placedImages(Placement, Alloc, Cost)).

cost(P, Cost) :- 
    findall(CS, (member(at(I,N), P), image(I,S,_), node(N,_,C), CS is C*S), Costs), sum_list(Costs, Cost).

imagesToPlace(Images) :-
    findall((S,I), image(I,S,_), X), sort(X, TmpImages), findall(I, member((S,I), TmpImages), Y), reverse(Y, Images). 

candidateNodes(Nodes) :- 
    findall(cand(C,N), node(N,_,C), Tmp), sort(Tmp, TmpNodes), findall(N, member(cand(_,N),TmpNodes), Nodes).

iterativeDeepening(quick, Images, Nodes, Placement, Cost, M, Max) :-
    M =< Max, \+ imagePlacement(Images, Nodes, Placement, Cost, M), NewM is M+1,
    iterativeDeepening(quick, Images, Nodes, Placement, Cost, NewM, Max).
iterativeDeepening(quick, Images, Nodes, Placement, Cost, M, Max) :-
    M =< Max, imagePlacement(Images, Nodes, Placement, Cost, M).

iterativeDeepening(best, Images, Nodes, Placement, Cost, M, Max) :-
    M =< Max, \+ bestPlacement(Images, Nodes, Placement, Cost, M), NewM is M+1,
    iterativeDeepening(best, Images, Nodes, Placement, Cost, NewM, Max).
iterativeDeepening(best, Images, Nodes, Placement, Cost, M, Max) :-
    M =< Max, bestPlacement(Images, Nodes, Placement, Cost, M).

bestPlacement(Images, Nodes, Placement, Cost, Max) :- 
    imagePlacement(Images, Nodes, Placement, Cost, Max), 
    \+ ( imagePlacement(Images, Nodes, P2, C2, Max), dif(Placement, P2), C2 < Cost ).

imagePlacement(Images, Nodes, Placement, Cost, Max) :-
    imagePlacement(Images, Nodes, [], Placement, 0, Cost, Max).
   
imagePlacement([I|Is], Nodes, OldPlacement, NewPlacement, OldCost, NewCost, Max) :-
    replicaPlacement(I,Nodes,OldPlacement,TmpPlacement,OldCost,TmpCost,Max), 
    imagePlacement(Is,Nodes,TmpPlacement,NewPlacement,TmpCost,NewCost,Max).
imagePlacement([],_,P,P,C,C,_).

replicaPlacement(I, Nodes, P, P, C, C, _) :- transferTimesOk(I, Nodes, P).
replicaPlacement(I, Nodes, Placement, NewPlacement, OldCost, NewCost, M) :-
    \+ transferTimesOk(I, Nodes, Placement), M>0, NewM is M-1,
    image(I, Size, _), member(N,Nodes), node(N, _, C), \+ member(at(I,N), Placement),
    storageOk(Placement, N, Size),
    TmpCost is C * Size + OldCost,
    replicaPlacement(I, Nodes, [at(I, N)|Placement], NewPlacement, TmpCost, NewCost, NewM).

transferTimesOk(I, Nodes, P) :- dif(P,[]), checkTransferTimes(I, Nodes,P).    

checkTransferTimes(I, [N|Ns], P) :-
    member(at(I,M),P), image(I,_,Max), 
    transferTime(I,M,N,T), T < Max, !, % one source is enough
    checkTransferTimes(I, Ns, P).
checkTransferTimes(_, [], _).

transferTime(Image, Src, Dest, T) :-
    image(Image, Size, _), dif(Src, Dest),
    node(Src, _, _), node(Dest, _, _),
    link(Src, Dest, Latency, Bandwidth),
    T is Size * 8 / Bandwidth + Latency.
transferTime(_, N, N, 0).

checkStorage(I, Size, Placement, Alloc) :-
    findall(N, member(at(I,N), Placement), Nodes), 
    checkStorage(I, Size, Nodes, Placement, Alloc).

checkStorage(I, Size, [N|Ns], Placement, Alloc) :-
    storageOk(Placement, N, Size), 
    checkStorage(I, Size, Ns, Placement, Alloc).
checkStorage(_, _, [], _, _). 

storageOk(Placement, N, Size) :- 
    (placedImages(_, Alloc, _) ; (\+ placedImages(_,_,_), Alloc = [])),
    node(N, Storage, _), findall(S, member((N,S), Alloc), OldAllocs), sum_list(OldAllocs, OldAlloc),
    usedHw(Placement, N, UsedHw), Storage + OldAlloc - UsedHw >= Size.

usedHw(P, N, TotUsed) :- findall(S, (member(at(I,N), P), image(I,S,_)), Used), sum_list(Used, TotUsed).

allocatedStorage(P, Alloc) :- findall((N,S), (member(at(I,N), P), image(I,S,_)), Alloc).