:- set_prolog_flag(answer_write_options,[max_depth(0), spacing(next_argument)]).
:- set_prolog_flag(stack_limit, 32 000 000 000).
:- set_prolog_flag(last_call_optimisation, true).
:- consult('images.pl').
%:- consult('infra.pl').
:- dynamic(placedImages/3).
:- dynamic(image/3).
:- dynamic(node/3).
:- dynamic(link/4).
:- dynamic(maxReplicas/1).
:- table transferTime/4.
    
declace(Placement, Cost, Time) :-
    imagesToPlace(Images), networkNodes(Nodes), maxReplicas(Max),
    statistics(cputime, Start),
    once(crPlacement(Images, Nodes, Max, Placement, Cost)),
    statistics(cputime, End),
    Time is End - Start.

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

/* Determines either a NewPlacement  of Images onto Nodes */
crPlacement(Images, Nodes, Max, NewPlacement, Cost) :- 
    placedImages(Placement, Alloc, _), %dif(Placement,[]),  
    reasoningStep(Images, Nodes, Placement, [], OkPlacement, Alloc, KOImages),
    placement(KOImages, Nodes, Max, OkPlacement, NewPlacement, Cost).
crPlacement(Images, Nodes, Max, InitialPlacement, Cost) :- 
    placement(Images, Nodes, Max, [], InitialPlacement, Cost).

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

placement(Placement, Cost) :-
    imagesToPlace(Images), networkNodes(Nodes), maxReplicas(Max),
    placement(Images, Nodes, Max, [], Placement, Cost).

/* Iterative deepening */
placement([], _, _, POk, POk, Cost) :-
    cost(POk, Cost), allocatedStorage(POk,Alloc),
    storePlacement(POk, Alloc, Cost).  
placement([I|Mages], Nodes, Max, PartialPlacement, Placement, Cost) :-
    id([I|Mages], Nodes, PartialPlacement, Placement, 1, Max), 
    cost(Placement, Cost),
    allocatedStorage(Placement,Alloc),
    storePlacement(Placement, Alloc, Cost).

/* calls image placement by iteratively increasing the number of maximum allowed replicas from M to Max */
id(Images, Nodes, PartialPlacement, Placement, M, Max) :-
    M =< Max, 
    imagePlacement(Images, Nodes, PartialPlacement, Placement, M).
id(Images, Nodes, PartialPlacement, Placement, M, Max) :-
    M =< Max, NewM is M+1,
    id(Images, Nodes, PartialPlacement, Placement, NewM, Max).
    
imagePlacement([I|Is], Nodes, OldPlacement, NewPlacement, Max) :-
    replicaPlacement(I,Nodes,OldPlacement,TmpPlacement,Max), 
    imagePlacement(Is,Nodes,TmpPlacement,NewPlacement,Max).
imagePlacement([],_,P,P,_).

replicaPlacement(I, Nodes, P, P, _) :- transferTimesOk(I, Nodes, P), !.
replicaPlacement(I, Nodes, Placement, NewPlacement, M) :-
    % \+ transferTimesOk(I, Nodes, Placement),
    M > 0, NewM is M - 1,
    image(I, Size, _),
    member(N, Nodes),
    node(N, _, _),
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
    dif(Src, Dest), 
    image(Image, Size, _),
    node(Src, _, _),
    node(Dest, _, _),
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
    findall(S, member((N,S), Alloc), OldAllocs),
    sum_list(OldAllocs, OldAlloc),
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



