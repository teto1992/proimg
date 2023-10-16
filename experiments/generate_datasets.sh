INITSIZE=25
ENDSIZE=500
STEPSIZE=100

for i in `eval echo {$INITSIZE..$ENDSIZE..$STEPSIZE}`; do
	mkdir $i
    echo $i
done

python3 generate_networks.py $INITSIZE $ENDSIZE $STEPSIZE 0

python3 generate_runner_scripts.py $INITSIZE $ENDSIZE $STEPSIZE 0
