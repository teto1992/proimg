:- consult('config.pl').

declace(Placement, Cost, Time) :-
    imagesToPlace(Images), networkNodes(Nodes), maxReplicas(Max),
    statistics(cputime, Start),
    once(crPlacement(Images, Nodes, Max, Placement, Cost)),
    statistics(cputime, End),
    Time is End - Start.

% Sorts images by size in descending order
imagesToPlace(Images) :-
    findall((S,I), image(I,S,_), X),
    sort(0, @>, X, SortedImagesDescending),
    findall(I, member((S,I), SortedImagesDescending), Images).

% Sorts candidates by cost in ascending order
networkNodes(Nodes) :- 
    findall(cand(C,N), node(N,_,C), Tmp),
    sort(0, @<, Tmp, SortedTmpDes),
    findall(N, member(cand(C,N), SortedTmpDes), Nodes).

% Determines a Placement of Images onto Nodes, possibly "repairing" an initial Placement
crPlacement(Images, Nodes, Max, NewPlacement, Cost) :- 
    placedImages(Placement, Alloc, _), dif(Placement,[]),  
    reasoningStep(Images, Nodes, Placement, [], OkPlacement, Alloc, KOImages),
    placement(KOImages, Nodes, Max, OkPlacement, NewPlacement, Cost).
crPlacement(Images, Nodes, Max, InitialPlacement, Cost) :- 
    placement(Images, Nodes, Max, [], InitialPlacement, Cost).

/* Identifies images to be replaced (i.e. new images or images with problems on storage or transfer times) */
reasoningStep([I|Is], Nodes, P, POk, NewPOk, Alloc, KO) :-
    findall(at(I,N), member(at(I,N), P), INs),
    append(INs, POk, TmpPOk),
    image(I, Size, _),
    checkTransferTimes(I, Nodes, TmpPOk),
    checkStorage(I, Size, TmpPOk, Alloc), 
    reasoningStep(Is, Nodes, P, TmpPOk, NewPOk, Alloc, KO).
reasoningStep([I|Is], Nodes, P, POk, NewPOk, Alloc, [I|KO]) :-
    reasoningStep(Is, Nodes, P, POk, NewPOk, Alloc, KO).
reasoningStep([], _, _, POk, POk, _, []).

placement(Placement, Cost) :-
    imagesToPlace(Images), networkNodes(Nodes), maxReplicas(Max),
    placement(Images, Nodes, Max, [], Placement, Cost).

/* Iterative deepening */
placement([I|Mages], Nodes, Max, PartialPlacement, Placement, Cost) :-
    iterativeDeepening([I|Mages], Nodes, PartialPlacement, Placement, 1, Max), 
    cost(Placement, Cost),
    allocatedStorage(Placement,Alloc),
    storePlacement(Placement, Alloc, Cost).
placement([], _, _, POk, POk, Cost) :-
    cost(POk, Cost), allocatedStorage(POk,Alloc),
    storePlacement(POk, Alloc, Cost).  

/* Calls imagePlacement/5 while increasing the number of maximum allowed replicas from M to Max */
iterativeDeepening(Images, Nodes, PartialPlacement, Placement, M, Max) :-
    M =< Max, 
    imagePlacement(Images, Nodes, PartialPlacement, Placement, M).
iterativeDeepening(Images, Nodes, PartialPlacement, Placement, M, Max) :-
    M =< Max, NewM is M+1,
    iterativeDeepening(Images, Nodes, PartialPlacement, Placement, NewM, Max).
    
/* Places Images one by one */
imagePlacement([I|Is], Nodes, OldPlacement, NewPlacement, Max) :-
    replicaPlacement(I,Nodes,OldPlacement,TmpPlacement,Max), 
    imagePlacement(Is,Nodes,TmpPlacement,NewPlacement,Max).
imagePlacement([],_,P,P,_).

/* Places at most M replicas of I onto Nodes, until transferTimesOk/3 holds */
replicaPlacement(I, Nodes, P, P, _) :- 
    transferTimesOk(I, Nodes, P), !.
replicaPlacement(I, Nodes, Placement, NewPlacement, M) :-
    % \+ transferTimesOk(I, Nodes, Placement), 
    M > 0, NewM is M - 1,
    image(I, Size, _), member(N, Nodes),
    \+ member(at(I,N), Placement),
    storageOk(Placement, N, Size),
    replicaPlacement(I, Nodes, [at(I, N)|Placement], NewPlacement, NewM).

transferTimesOk(I, Nodes, P) :-
    dif(P,[]), checkTransferTimes(I, Nodes,P).    

checkTransferTimes(I, [N|Ns], P) :-
    member(at(I,M),P),
    image(I,_,Max), 
    transferTime(I,M,N,T),
    T < Max, !, % one source is enough
    checkTransferTimes(I, Ns, P).
checkTransferTimes(_, [], _).

transferTime(Image, Src, Dest, T) :-
    dif(Src, Dest), node(Src, _, _), node(Dest, _, _),
    image(Image, Size, _),
    link(Src, Dest, Latency, Bandwidth),
    T is Size * 8 / Bandwidth + Latency / 1000.
transferTime(_, N, N, 0).

checkStorage(I, Size, Placement, Alloc) :-
    findall(N, member(at(I,N), Placement), Nodes), 
    checkStorage(I, Size, Nodes, Placement, Alloc).

checkStorage(I, Size, [N|Ns], Placement, Alloc) :-
    storageOk(Placement, N, Size), checkStorage(I, Size, Ns, Placement, Alloc).
checkStorage(_, _, [], _, _). 

storageOk(Placement, N, Size) :- 
    (placedImages(_, Alloc, _) ; (Alloc = [])),
    node(N, Storage, _),
    findall(S, member((N,S), Alloc), OldAllocs), sumlist(OldAllocs, OldAlloc),
    usedHw(Placement, N, UsedHw),
    Storage + OldAlloc - UsedHw >= Size.

cost(Placement, Cost) :- findall(C, (member(at(_,N), Placement), node(N,_,C)), Costs), sum_list(Costs, Cost).

usedHw(P, N, TotUsed) :- findall(S, (member(at(I,N), P), image(I,S,_)), Used), sum_list(Used, TotUsed).

allocatedStorage(P, Alloc) :- findall((N,S), (member(at(I,N), P), image(I,S,_)), Alloc).

storePlacement(Placement, Alloc, Cost) :-
    ( placedImages(_,_,_) -> retract(placedImages(_,_,_)) ; true),
    assert(placedImages(Placement, Alloc, Cost)).

%%% Utils %%%

loadInfrastructure() :-
    open('infra.pl', read, Str),
    (retractall(node(_,_,_)), retractall(link(_,_,_,_)), retractall(maxReplicas(_)); true),
    readAndAssert(Str).

readAndAssert(Str) :-
    read(Str, X), (X == end_of_file -> close(Str) ; assert(X), readAndAssert(Str)).