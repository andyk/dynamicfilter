This is the README file for the test.py file.

Run tests by typing this into the terminal: python2.7 manage.py test dynamicfilterapp.tests.SimulationTest.test_controller
The python2.7 indicates the version of python installed in your computer. It may 
work by just typing python.

Near the top of the file, there are four boolean values. Each of these can be 
toggled to True or False whenever you want depending on what you want to record 
as a csv file.

fastTrackRecord will keep track of how many votes have been fast-tracked by eddy2.

percentRecord will record what percent of items have been processed as each task 
is recorded

itemsNotEvalRecord will keep track of how many items were not evaluated by each 
predicate for each algorithm.

selVSambRecord will record the entropy values, actual selectivities, estimated 
selectivities, and difference between the two selectivities and write it to a 
csv file. It will also produce a scatterplot of entropy values vs. difference in 
selectivities and then find the best fit line.

Test_Controller
----------------
recordAggregateStats is generally always on. It keeps track of the number of 
tasks each simulation took and the accuracy of the simulation. It does this for 
each algorithm.

createDataSet creates a dataset to help simulate the optimal algorithm. It 
contains the entropy, estimated selectivities, cost, and answer set, and rank 
values for each Rest-Pred pair. Once you generate this once, you don't need to 
run optimal algorithm again because you can use this dataset and run a separate 
script (which needs to be made) to just add costs as you go down the ordered 
dataset by rank.

After that boolean value, you will see four other boolean values labelled 
according to their algorithm names with "Ind" at the end. If you turn these 
three on, this records a csv file for each individual run. This run keeps track 
of what happens at each individual vote.

The last four boolean values then say "run" with the algorthm name at the end. 
You can turn this on or off whenever you want to run whichever algorithm. This 
saves a huge amount of time because for batches of 100s simulations of subjective 
or ambiguous sets of predicates, each run takes a non-negligible amount of time.

After the boolean values are any number of parameter sets. What is inside the 
set is described in the comments of the python file.

Run_Simulation
---------------
This is where basically everything happens asides from picking the rest-pred. 
This is the main portion of what tests our simulation's algorithms. Another 
important part is that is records all the data. The percent done, number of 
items not evaluated, and selectivities vs ambiguity data is also recorded here 
and written out to a csv file.

Many_Simulations
----------------
this method contains the for loop which will loop over Run_simulations as many 
times as we call it to do. It also will produce a scatterplot of entropy values 
vs. selectivity differences and find a best fit curve for that scatterplot. In 
the picture, it will also mention the R^2 value. The closer R^2 = 1, the better 
the curve. R^2 = 0 means that the curve explains none of the variability in the 
graph. R^2 = 1 means that the curve explains all the variability in the graph.

Write_results
-------------
when called, it writes data out to a csv file.

Reset_simulation
----------------
resets the database to original values

Clear_database
--------------
takes out everything from the database to prepare for another run