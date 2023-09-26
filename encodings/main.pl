:-consult('input.pl').

placement(Placement, Cost) :-
    findall(I, image(I,_,_), Images), findall(N, node(N,_,_), Nodes),
    maxReplicas(Max), imagePlacement(Images, Nodes, Placement, Cost, Max).

iterativeDeepening(Mode, Placement, Cost) :-
    imagesToPlace(Images), candidateNodes(Nodes), maxReplicas(Max), 
    time(iterativeDeepening(Mode, Images, Nodes, Placement, Cost, 1, Max)), !,
    allocatedStorage(Placement,Alloc), %index(Images, Placement, Index),
    assert(placedImages(Placement, Alloc, Cost)).

% crStep([at(alpine, n12), at(alpine, n6), at(alpine, n0), at(alpine, n3), at(busybox, n12), at(busybox, n6), at(busybox, n0), at(busybox, n3)], OkP, KOs).
crStep(KOImages) :- 
    findall(N, node(N,_,_), Nodes), imagesToPlace(Images),
    placedImages(Placement, _, _), 
    reasoningStep(Images, Nodes, Placement, [], KOImages).

reasoningStep([I|Is], Nodes, Placement, OldKO, NewKO) :-
   ok(I, Nodes, Placement), reasoningStep(Is, Nodes, Placement, OldKO, NewKO).
reasoningStep([I|Is], Nodes, Placement, OldKO, NewKO) :-
   \+ ok(I, Nodes, Placement), reasoningStep(Is, Nodes, Placement, [I|OldKO], NewKO).
reasoningStep([], _, _, KO, KO).

ok(I, [N|Nodes], Placement) :-
    member(at(I,M),Placement), node(M,_,_),
    image(I,_,Max), transferTime(I,M,N,T), T =< Max, !, % one source is enough
    ok(I, Nodes, Placement).
ok(_, [], _).

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
    storageOk(Placement, [], N, Size),
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

storageOk(Placement, Alloc, N, Size) :- 
    node(N, Storage, _), findall(S, member((N,S), Alloc), OldAllocs), sum_list(OldAllocs, OldAlloc),
    usedHw(Placement, N, UsedHw), Storage + OldAlloc - UsedHw >= Size.

usedHw(P, N, TotUsed) :- findall(S, (member(at(I,N), P), image(I,S,_)), Used), sum_list(Used, TotUsed).

allocatedStorage(P, Alloc) :- findall((N,S), (member(at(I,N), P), image(I,S,_)), Alloc).

index(Images, Placement, Index) :- 
    findall(N, node(N,_,_), Nodes), index(Images, Nodes, Placement, [], Index).

index([I|Is], Nodes, Placement, OldIndex, NewIndex) :-
    source(I, Nodes, Placement, OldIndex, TmpIndex), index(Is, Nodes, Placement, TmpIndex, NewIndex).
index([], _, _, I, I).

source(I, [N|Nodes], P, OldIndex, NewIndex) :-
    member(at(I,M),P), 
    image(I,_,Max), transferTime(I,M,N,T), T =< Max, !, % one source is enough
    updateIndex(I,N,M,OldIndex,TmpIndex),
    source(I, Nodes, P, TmpIndex, NewIndex).
source(_, [], _, Index, Index).

updateIndex(I,N,M,Index,[i(N, [src(I,M)])|Index]) :-
    \+ member(i(N,_),Index).
updateIndex(I,N,M,OldIndex,NewIndex) :-
    member(i(N,Sources),OldIndex),
    select(i(N,Sources),OldIndex, i(N,[src(I,M)|Sources]), NewIndex).