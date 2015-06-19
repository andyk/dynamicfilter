from django import forms
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.db import models

from .models import Restaurant, RestaurantPredicate, Task, PredicateBranch
from .forms import WorkerForm, IDForm

from scipy.special import btdtr
import random

DECISION_THRESHOLD = 0.5
UNCERTAINTY_THRESHOLD = 0.15

def index(request):
    # Filler ID number value
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = IDForm(request.POST)
        
        # check whether it's valid:
        if form.is_valid():
            IDnumber = request.POST.get('workerID', 777)
            
            # redirect to a new URL:
            return HttpResponseRedirect('/dynamicfilterapp/answer_question/id=' + IDnumber)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = IDForm()

    return render(request, 'dynamicfilterapp/index.html', {'form': form})

def answer_question(request, IDnumber):
    """
    Displays and processes input from a form where the user can answer a question about a
    predicate.
    """
    # if this is a POST request we need to process the form data
    if request.method == 'POST':

        # create a form instance and populate it with data from the request:
        form = WorkerForm(request.POST)
        toBeAnswered = RestaurantPredicate.objects.filter(id=request.POST.get('pred_id'))[0]
        print toBeAnswered.restaurant._meta.get_all_field_names()

        # check whether it's valid:
        if form.is_valid():

            # get time to complete in number of milliseconds, or use flag value if there's no elapsed_time
            timeToComplete = request.POST.get('elapsed_time', 42)

            # Convert entered answer to type compatible with NullBooleanField
            form_answer = None

            # if worker answered Yes
            if form.cleaned_data['answerToQuestion'] == "True":
                form_answer = True

            # if worker answered No
            elif form.cleaned_data['answerToQuestion'] == "False":
                form_answer = False

            # create a new Task with relevant information and store it in the database
            task = Task(restaurantPredicate = toBeAnswered, answer = form_answer, confidenceLevel=form.cleaned_data['confidenceLevel'],
                workerID = IDnumber, completionTime = timeToComplete)
            task.save()

             # get the PredicateBranch associated with this predicate
            pB = PredicateBranch.objects.filter(question=toBeAnswered.question)[0]

            # update the predicate branch's counts
            if task.answer==True:
                pB.returnedTotal += 1
            elif task.answer==False:
                pB.returnedTotal += 1
                pB.returnedNo += 1
            pB.save()

            decrementStatus(toBeAnswered.index, toBeAnswered.restaurant)

            aggregate_responses(toBeAnswered)     

            toBeAnswered.evaluator = None
            
            toBeAnswered.save()

            # redirect to a new URL:
            return HttpResponseRedirect('/dynamicfilterapp/completed_question/id=' + IDnumber)

    # if a GET (or any other method) we'll create a blank form
    else:
        toBeAnswered = eddy(request, IDnumber)
        #print "toBeAnswered: " + str(toBeAnswered)
        # if there are no predicates to be answered by the worker with this ID number
        if toBeAnswered == None:
            return HttpResponseRedirect('/dynamicfilterapp/no_questions/id=' + IDnumber)
        form = WorkerForm()

    return render(request, 'dynamicfilterapp/answer_question.html', {'form': form, 'predicate': toBeAnswered, 'workerID': IDnumber })

def checkPredicateStatus(array):
    """
    Checks through the bits of a predicateStatus in order to see if it contains nonzero values
    """
    for integer in array:
        if integer != 0:
            return False
    return True

def completed_question(request, IDnumber):
    """
    Displays a page informing the worker that their answer was recorded, with a link to
    answer another question.
    """
    return render(request, 'dynamicfilterapp/completed_question.html', {'workerID': IDnumber})

def no_questions(request, IDnumber):
    """
    Displays a page informing the worker that no questions need answering by them.
    """
    return render(request, 'dynamicfilterapp/no_questions.html', {'workerID': IDnumber})

def aggregate_responses(predicate):
    """
    Checks if predicate needs to be answered 0 more times. 
    Combines worker responses into one value for the predicate.
    """
    # retrieves the number of yes answers and number of no answers for the 
    # predicate relative to the answers' confidence levels
    yes = Task.objects.filter(restaurantPredicate=predicate, answer = True)
    no = Task.objects.filter(restaurantPredicate=predicate, answer = False)

    # initialize the number of yes's and no's to 0
    totalYes = 0.0
    totalNo = 0.0

    # for all predicates answered yes
    for pred in yes:
        # increase total number of yes by the confidence level indicated
        totalYes += pred.confidenceLevel/100.0
        # increase total number of no by 100 - confidence level indicated
        totalNo += 1 - pred.confidenceLevel/100.0

    # for all predicates answered no
    for pred in no:
        # increase total number of no by 100 - the confidence level 
        # indicated
        totalYes += 1 - pred.confidenceLevel/100.0
        # increase total number of no by confidence level indicated
        totalNo += pred.confidenceLevel/100.0

    uncertaintyLevel = btdtr(totalYes+1, totalNo+1, DECISION_THRESHOLD)

    if totalYes > totalNo:
        uncertaintyLevel = btdtr(totalYes+1, totalNo+1, DECISION_THRESHOLD)
        if uncertaintyLevel < UNCERTAINTY_THRESHOLD:
            predicate.value = True
    elif totalNo > totalYes:
        uncertaintyLevel = btdtr(totalNo+1, totalYes+1, DECISION_THRESHOLD)
        if uncertaintyLevel < UNCERTAINTY_THRESHOLD:
            predicate.value = False
            predicate.restaurant.predicate0Status = -1
            predicate.restaurant.predicate1Status = -1
            predicate.restaurant.predicate2Status = -1
    
    if predicate.value==None:
        # collect three more responses from workers when there are same 
        # number of yes and no
        incrementStatusByFive(predicate.index, predicate.restaurant)

    predicate.save()

def eddy(request, ID):
    """
    Uses a random lottery system to determine which eligible predicate should be
    evaluated next.
    """
    debug = True
    #if debug: print "------FINDING ELIGIBLE BRANCHES FOR LOTTERY-----"

    # find all the tasks this worker has completed
    completedTasks = Task.objects.filter(workerID=ID)
    # find all the predicates matching these completed tasks
    completedPredicates = RestaurantPredicate.objects.filter(
        id__in=completedTasks.values('restaurantPredicate_id'))
       
    # Find all PredicateBranches with open space and that haven't been completed
    # by this worker
    allPredicateBranches = PredicateBranch.objects.exclude(
        question__in=completedPredicates.values('question'))
    
    #if debug: print "------STARTING LOTTERY------"
    #print "size of all predicate branches: " + str(len(allPredicateBranches))
    chosenBranch = runLottery(allPredicateBranches)
    
    if chosenBranch==None:
        return None
    #print "chosen branch: " + str(chosenBranch)
    # generates the restaurant with the highest priority for the specified 
    # predicate branch
    chosenRestaurant = findRestaurant(chosenBranch)
    
    #  mark chosenRestaurant as being in chosenBranch
    chosenRestaurant.evaluator = chosenBranch.index

    # Find the RestaurantPredicate corresponding to this Restaurant and 
    # PredicateBranch
    chosenPredicate = RestaurantPredicate.objects.filter(restaurant = 
        chosenRestaurant, question = chosenBranch.question)[0]
    #print "Predicate to answer: " + str(chosenPredicate)

    return chosenPredicate
    
def decrementStatus(index, restaurant):
    if index==0 and restaurant.predicate0Status > 0:
        restaurant.predicate0Status += -1
    elif index==1 and restaurant.predicate1Status > 0:
        restaurant.predicate1Status += -1
    elif index==2 and restaurant.predicate2Status > 0:
        restaurant.predicate2Status += -1
    restaurant.save()

def incrementStatusByFive(index, restaurant):
    if index==0:
        restaurant.predicate0Status += 5
    elif index==1:
        restaurant.predicate1Status += 5
    elif index==2:
        restaurant.predicate2Status += 5
    restaurant.save()

def findTotalTickets(pbSet):
    """
    Finds the total number of "tickets" held by a set of PredicateBranches, by 
    turning selectivity into a useful integer.
    Selectivity = (no's)/(total evaluated)
    """
    totalTickets = 0

    # award tickets based on computed selectivity
    for pb in pbSet:
        selectivity = float(pb.returnedNo)/float(pb.returnedTotal)
        totalTickets += int(selectivity*1000)
        #print "total so far: " + str(totalTickets)

    #print "TOTAL TICKETS: " + str(totalTickets)

    return int(totalTickets)

def runLottery(pbSet):
    #TODO check that there are possible predicates
    totalTickets = findTotalTickets(pbSet)
    if totalTickets==0:
        return None

    # generate random number between 1 and totalTickets
    rand = random.randint(1, totalTickets)

    # check if rand falls in the range corresponding to each predicate
    lowBound = 0
    selectivity = float(pbSet[0].returnedNo)/pbSet[0].returnedTotal
    highBound = selectivity*1000
    
    # an empty PredicateBranch object NOT saved in the database
    chosenBranch = PredicateBranch()
    # loops through all predicate branches to see in which predicate branch rand
    # falls in
    #print "-------Check ranges --------"
    for j in range(len(pbSet)):
        #print "random number: " + str(rand)
        #print "range: " + str(lowBound) + " to " + str(highBound)
        if lowBound <= rand <= highBound:
            chosenBranch = pbSet[j]
            break
        else:
            lowBound = highBound
            nextPredicateBranch = pbSet[j+1]
            nextSelectivity = float(nextPredicateBranch.returnedNo)/nextPredicateBranch.returnedTotal
            highBound += nextSelectivity*1000

    return chosenBranch
    
def findRestaurant(predicateBranch):
    """
    Finds the restaurant with the highest priority for a specified predicate 
    branch. Hard-coded to three predicates for now.
    """
    if predicateBranch.index==0:
        return Restaurant.objects.order_by('-predicate0Status')[0]
    elif predicateBranch.index==1:
        return Restaurant.objects.order_by('-predicate1Status')[0]
    elif predicateBranch.index==2:
        return Restaurant.objects.order_by('-predicate2Status')[0]
