:- set_prolog_flag(answer_write_options,[max_depth(0), spacing(next_argument)]).
:- set_prolog_flag(stack_limit, 32 000 000 000).
:- set_prolog_flag(last_call_optimisation, true).
:- consult('images.pl').
:- dynamic(placedImages/3).
:- dynamic(image/3).
:- dynamic(node/3).
:- dynamic(link/4).
:- dynamic(maxReplicas/1).

/* Identify KOImages and builds a new Placement with associated cost, by keeping the partial POk as is*/
crStep(P, KOImages, NewPlacement, Cost, Time) :- 
    placedImages(P, Alloc, _), dif(P,[]),  
    imagesToPlace(Images), networkNodes(Nodes),
    statistics(cputime, Start),
        reasoningStep(Images, Nodes, P, [], POk, Alloc, KOImages),
        iterativeDeepening(KOImages, Nodes, POk, NewPlacement, Cost),
    statistics(cputime, End), Time is End - Start.
crStep([], [], Placement, Cost, Time) :- 
    imagesToPlace(Images), networkNodes(Nodes),
    statistics(cputime, Start),
        iterativeDeepening(Images, Nodes, [], Placement, Cost),
    statistics(cputime, End), Time is End - Start.

/* Identify images to be replaced (i.e. new images or images with problems on storage or transfer times) */
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

updatePlacement(Placement, Alloc, Cost) :-
    ( placedImages(_,_,_) -> retract(placedImages(_,_,_)) ; true),
    assert(placedImages(Placement, Alloc, Cost)).

/* Iterative deepening */
placement([], _, POk, POk, Cost) :-
    allocatedStorage(POk,Alloc), cost(POk, Cost), 
    updatePlacement(POk, Alloc, Cost).  
placement(ImagesToPlace, Nodes, PartialPlacement, Placement, Cost) :-
    maxReplicas(Max), 
    iterativeDeepening(ImagesToPlace, Nodes, PartialPlacement, Placement, 1, Max),
    cost(Placement, Cost),
    allocatedStorage(Placement,Alloc),
    updatePlacement(Placement, Alloc, Cost).

iterativeDeepening(Images, Nodes, PartialPlacement, Placement, M, Max) :-
    M =< Max, imagePlacement(Images, Nodes, PartialPlacement, Placement, M).
iterativeDeepening(Images, Nodes, PartialPlacement, Placement, M, Max) :-
    M =< Max, NewM is M+1,
    iterativeDeepening(Images, Nodes, PartialPlacement, Placement, NewM, Max).

% % Computes placement cost
cost(L, Cost):-
    cost_(L, 0, Cost).
cost_([], C, C).
cost_([at(I,N) | T], C0, C):-
    image(I, S ,_),
    node(N, _ ,NC),
    C1 is NC * S + C0,
    cost_(T, C1, C). 
% cost(Placement, Cost) :-
%     findall(C, (member(at(_,N), Placement), node(N,_,C)), Costs), sum_list(Costs, Cost).

% selects the images starting from the the ones with the highest
% associated capacity
imagesToPlace(Images) :-
    findall((S,I), image(I,S,_), X),
    sort(0, @>, X, SortedImagesDescending),
    findall(I, member((S,I), SortedImagesDescending), Images).

% retrieve the candidate nodes
get_id(cand(_,B),B).
networkNodes(Nodes) :- 
    findall(cand(C,N), node(N,_,C), Tmp),
    sort(0, @<, Tmp, SortedTmpDes),
    maplist(get_id, SortedTmpDes, Nodes).

iterativeDeepening(Images, Nodes, Placement, M, Max) :-
    M =< Max,
    imagePlacement(Images, Nodes, Placement, M).
iterativeDeepening(Images, Nodes, Placement, M, Max) :-
    M =< Max,
    NewM is M+1,
    iterativeDeepening(Images, Nodes, Placement, NewM, Max).

imagePlacement(Images, Nodes, Placement, Max) :-
    imagePlacement(Images, Nodes, [], Placement, Max).
imagePlacement([],_,P,P,_).
imagePlacement([I|Is], Nodes, OldPlacement, NewPlacement, Max) :-
    replicaPlacement(I,Nodes,OldPlacement,TmpPlacement,Max), 
    imagePlacement(Is,Nodes,TmpPlacement,NewPlacement,Max).

replicaPlacement(I, Nodes, P, P, _) :-
    transferTimesOk(I, Nodes, P).%, !. % green cut
replicaPlacement(I, Nodes, Placement, NewPlacement, M) :-
    \+ transferTimesOk(I, Nodes, Placement),
    M > 0, NewM is M - 1,
    image(I, Size, _),
    member(N, Nodes),
    node(N, _, _),
    \+ member(at(I,N), Placement),
    storageOk(Placement, N, Size),
    replicaPlacement(I, Nodes, [at(I, N)|Placement], NewPlacement, NewM).

transferTimesOk(I, Nodes, P) :-
    dif(P,[]), checkTransferTimes(I, Nodes,P).    

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
    T is Size * 8 / Bandwidth + Latency.  % Latency in ms, Bandwidth Megabit per second, Size in MB

checkStorage(I, Size, Placement, Alloc) :-
    findall(N, member(at(I,N), Placement), Nodes), 
    checkStorage(I, Size, Nodes, Placement, Alloc).

checkStorage(_, _, [], _, _). 
checkStorage(I, Size, [N|Ns], Placement, Alloc) :-
    storageOk(Placement, N, Size), checkStorage(I, Size, Ns, Placement, Alloc).

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

% % Computes the hardware used by the node Node in the placement P
% % and unifies this value with TotUsed
% usedHw(P, N, TotUsed) :- findall(S, (member(at(I,N), P), image(I,S,_)), Used), sum_list(Used, TotUsed).

% % Computes the allocated storage for the current placement Placemetn
% allocatedStorage(P, Alloc) :- findall((N,S), (member(at(I,N), P), image(I,S,_)), Alloc).

loadInfrastructure() :-
    open('infra.pl', read, Str),
    (retractall(node(_,_,_)), retractall(link(_,_,_,_)), retractall(maxReplicas(_)); true),
    readAndAssert(Str).

readAndAssert(Str) :-
    read(Str, X), (X == end_of_file -> close(Str) ; assert(X), readAndAssert(Str)).

/*Places images one by one without exceeding MaxReplicas for each image*/
iterativeDeepening(Mode, Placement, Cost) :-
    imagesToPlace(Images),
    networkNodes(Nodes),
    maxReplicas(Max), 
    iterativeDeepening(Mode, Images, Nodes, Placement, 1, Max),
    cost(Placement, Cost),
    allocatedStorage(Placement,Alloc),
    updatePlacement(Placement, Alloc, Cost).

iterativeDeepening(best, Images, Nodes, PartialPlacement, Placement, M, Max) :-
    M =< Max, bestPlacement(Images, Nodes, PartialPlacement, Placement, M).
iterativeDeepening(best, Images, Nodes, PartialPlacement, Placement, M, Max) :-
    M =< Max,
    NewM is M + 1,
    iterativeDeepening(best, Images, Nodes, PartialPlacement, Placement, NewM, Max).

bestPlacement(Images, Nodes, Placement, M) :-
    bestPlacement(Images, Nodes, [], Placement, M).
bestPlacement(Images, Nodes, PartialPlacement, Placement, Max) :- 
    imagePlacement(Images, Nodes, PartialPlacement, Placement, Max), cost(Placement, Cost),
    \+ ( imagePlacement(Images, Nodes, PartialPlacement, P2, Max), dif(Placement, P2), cost(P2,C2), C2 < Cost ).

iterativeDeepening(best, Images, Nodes, Placement, M, Max) :-
    M =< Max,
    bestPlacement(Images, Nodes, Placement, M).
iterativeDeepening(best, Images, Nodes, Placement, M, Max) :-
    M =< Max,
    NewM is M + 1,
    iterativeDeepening(best, Images, Nodes, Placement, NewM, Max).