:- consult('input.pl').
:- dynamic(placedImages/3).
:- dynamic(image/3).
:- dynamic(node/3).
:- dynamic(link/4).
:- dynamic(maxReplicas/1).

/* Identify KOImages and builds a new Placement with associated cost, by keeping the partial POk as is*/
crStep(P, KOImages, NewPlacement, Cost) :- 
    placedImages(P, Alloc, _), dif(P,[]), !,
    imagesToPlace(Images),
    candidateNodes(Nodes),
    reasoningStep(Images, Nodes, P, [], POk, Alloc, KOImages),
    crID(KOImages, Nodes, POk, NewPlacement, Cost).
% useful for standalone executions    
crStep([], [], Placement, Cost) :- 
    iterativeDeepening(quick, Placement, Cost).

/* Identify images to be replaced (i.e. new images or images with problems on storage or transfer times) */
reasoningStep([], _, _, POk, POk, _, []).
reasoningStep([I|Is], Nodes, P, POk, NewPOk, Alloc, KO) :-
    findall(at(I,N), member(at(I,N), P), INs),
    append(INs, POk, TmpPOk),
    image(I, Size, _),
    checkTransferTimes(I, Nodes, TmpPOk),
    checkStorage(I, Size, TmpPOk, Alloc), 
    reasoningStep(Is, Nodes, P, TmpPOk, NewPOk, Alloc, KO).
reasoningStep([I|Is], Nodes, P, POk, NewPOk, Alloc, [I|KO]) :-
    reasoningStep(Is, Nodes, P, POk, NewPOk, Alloc, KO).

/* iterative deepening for the continuos reasoning */
crID(KOImages, Nodes, PartialPlacement, NewPlacement, Cost) :-
    maxReplicas(Max),
    imagePlacement(KOImages, Nodes, PartialPlacement, NewPlacement, 0, _, Max),
    cost(NewPlacement, Cost),
    allocatedStorage(NewPlacement,Alloc),
    ( placedImages(_,_,_) -> retract(placedImages(_,_,_)) ; true),
    assert(placedImages(NewPlacement, Alloc, Cost)).
crID([],_,P,P,Cost) :-  
    allocatedStorage(P,Alloc),
    ( placedImages(_,_,_) -> retract(placedImages(_,_,_)) ; true),
    assert(placedImages(P, Alloc, Cost)).

/*Places images one by one without exceeding MaxReplicas for each image*/
iterativeDeepening(Mode, Placement, Cost) :-
    imagesToPlace(Images),
    candidateNodes(Nodes),
    maxReplicas(Max), 
    iterativeDeepening(Mode, Images, Nodes, Placement, _, 1, Max),
    cost(Placement, Cost),
    allocatedStorage(Placement,Alloc),
    ( placedImages(_,_,_) -> retract(placedImages(_,_,_)) ; true),
    assert(placedImages(Placement, Alloc, Cost)).

% Computes the cost of a palcement (list of at/2 atoms)
% stored in L
cost(L, Cost):-
    cost_(L, 0, Cost).
cost_([], C, C).
cost_([at(I,N) | T], C0, C):-
    image(I, S ,_),
    node(N, _ ,NC),
    C1 is NC * S + C0,
    cost_(T, C1, C). 

% selects the images starting from the the ones with the highest
% associated capacity
imagesToPlace(Images) :-
    findall((S,I), image(I,S,_), X),
    sort(0, @>, X, SortedImagesDescending),
    findall(I, member((S,I), SortedImagesDescending), Images).

% retrieve the candidate nodes
get_id(cand(_,B),B).
candidateNodes(Nodes) :- 
    findall(cand(C,N), node(N,_,C), Tmp),
    sort(0, @<, Tmp, SortedTmpDes),
    maplist(get_id, SortedTmpDes, Nodes).

iterativeDeepening(quick, Images, Nodes, Placement, Cost, M, Max) :-
    M =< Max,
    imagePlacement(Images, Nodes, Placement, Cost, M).
iterativeDeepening(quick, Images, Nodes, Placement, Cost, M, Max) :-
    M =< Max,
    NewM is M+1,
    iterativeDeepening(quick, Images, Nodes, Placement, Cost, NewM, Max).

iterativeDeepening(best, Images, Nodes, Placement, Cost, M, Max) :-
    M =< Max,
    bestPlacement(Images, Nodes, Placement, Cost, M).
iterativeDeepening(best, Images, Nodes, Placement, Cost, M, Max) :-
    M =< Max,
    NewM is M + 1,
    iterativeDeepening(best, Images, Nodes, Placement, Cost, NewM, Max).

bestPlacement(Images, Nodes, Placement, Cost, Max) :- 
    imagePlacement(Images, Nodes, Placement, Cost, Max), 
    \+ ( imagePlacement(Images, Nodes, P2, C2, Max), dif(Placement, P2), C2 < Cost ).

imagePlacement(Images, Nodes, Placement, Cost, Max) :-
    imagePlacement(Images, Nodes, [], Placement, 0, Cost, Max).
imagePlacement([],_,P,P,C,C,_).
imagePlacement([I|Is], Nodes, OldPlacement, NewPlacement, OldCost, NewCost, Max) :-
    replicaPlacement(I,Nodes,OldPlacement,TmpPlacement,OldCost,TmpCost,Max), 
    imagePlacement(Is,Nodes,TmpPlacement,NewPlacement,TmpCost,NewCost,Max).

replicaPlacement(I, Nodes, P, P, C, C, _) :-
    transferTimesOk(I, Nodes, P), !. % green cut
replicaPlacement(I, Nodes, Placement, NewPlacement, OldCost, NewCost, M) :-
    % \+ transferTimesOk(I, Nodes, Placement),
    M > 0,
    NewM is M - 1,
    image(I, Size, _),
    member(N, Nodes),
    node(N, _, C),
    \+ member(at(I,N), Placement),
    storageOk(Placement, N, Size),
    TmpCost is C * Size + OldCost,
    replicaPlacement(I, Nodes, [at(I, N)|Placement], NewPlacement, TmpCost, NewCost, NewM).

transferTimesOk(I, Nodes, P) :-
    dif(P,[]),
    checkTransferTimes(I, Nodes,P).    

checkTransferTimes(_, [], _).
checkTransferTimes(I, [N|Ns], P) :-
    member(at(I,M),P),
    image(I,_,Max), 
    transferTime(I,M,N,T),
    T < Max, !, % one source is enough
    checkTransferTimes(I, Ns, P).

transferTime(_, N, N, 0).
transferTime(Image, Src, Dest, T) :-
    image(Image, Size, _),
    dif(Src, Dest),
    node(Src, _, _),
    node(Dest, _, _),
    link(Src, Dest, Latency, Bandwidth),
    % Latency in ms, Bandwidth Megabit per second, Size in MB
    T is Size * 8 / Bandwidth + Latency.

checkStorage(I, Size, Placement, Alloc) :-
    findall(N, member(at(I,N), Placement), Nodes), 
    checkStorage(I, Size, Nodes, Placement, Alloc).

checkStorage(_, _, [], _, _). 
checkStorage(I, Size, [N|Ns], Placement, Alloc) :-
    storageOk(Placement, N, Size), 
    checkStorage(I, Size, Ns, Placement, Alloc).

storageOk(Placement, N, Size) :- 
    (placedImages(_, Alloc, _) ; (Alloc = [])),
    node(N, Storage, _),
    findall(S, member((N,S), Alloc), OldAllocs),
    sum_list(OldAllocs, OldAlloc),
    usedHw(Placement, N, UsedHw),
    Storage + OldAlloc - UsedHw >= Size.

% Computes the hardware used by the node Node in the placement P
% and unifies this value with TotUsed
usedHw(P, Node, TotUsed):-
    usedHw_(P, Node, 0, TotUsed).
usedHw_([], _, U, U).
usedHw_([at(I,N) | T], N, TempUsed, Used):-
    image(I,S,_),
    TempUsed1 is TempUsed + S,
    usedHw_(T, N, TempUsed1, Used).
usedHw_([at(_,N0) | T], N1, TempUsed, Used):-
    dif(N0,N1),
    usedHw_(T, N1, TempUsed, Used).

% Computes the allocated storage for the current placement Placemetn
allocatedStorage(Placement, Alloc):-
    allocatedStorage_(Placement, [], Alloc).
allocatedStorage_([], L, L).
allocatedStorage_([at(I,N) | T], CP, Alloc):-
    image(I,S,_),
    allocatedStorage_(T, [(N,S) | CP], Alloc).
