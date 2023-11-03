image(alpine,3,10).
image(ngnix,65,60).
image(busybox,2,15).
image(ubuntu,28,120).
image(python,46,100).
maxReplicas(6).
max_replicas(Img,R) :- image(Img,_,_), maxReplicas(R).