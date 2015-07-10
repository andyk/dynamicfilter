from models import Task, RestaurantPredicate, Restaurant, PredicateBranch
from scipy.special import btdtr
from random import randint, choice
from math import exp

# we need at least half of the answers to be True in order for the value of the predicate to be True
# and same for False's
DECISION_THRESHOLD = 0.5

# the uncertainty level determined by the beta distribution function needs to be less than 0.15
# for us to fix the predicate's value
UNCERTAINTY_THRESHOLD = 0.15

ALPHA = 0.9
GAMMA = 0.1

PRED_CHANGE_THRESHOLD = 0.6
INDEX = 0

def aggregate_responses(predicate):
    """
    Checks if predicate needs to be answered 0 more times. If uncertainty criteria are met,
    combines worker responses into one value for the predicate. Otherwise, adds five to the 
    appropriate predicateStatus so that more answers will be collected.
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

    # How we compute the uncertaintly level changes depending on whether the answer is True or False
    uncertaintyLevelTrue = btdtr(totalYes+1, totalNo+1, DECISION_THRESHOLD)
    uncertaintyLevelFalse = btdtr(totalNo+1, totalYes+1, DECISION_THRESHOLD)

    # if more yes's than no's
    if totalYes > totalNo and uncertaintyLevelTrue < UNCERTAINTY_THRESHOLD:
        #print "predicate value set to true"
        predicate.value = True

    # if more no's than yes's
    elif totalNo > totalYes and uncertaintyLevelFalse < UNCERTAINTY_THRESHOLD:
        predicate.value = False

        # flag for the Restaurant failing a predicate (and thus not passing all the predicates)
        predicateFailed = False

        # iterates through all the fields in this restaurant's model
        for field in predicate.restaurant._meta.fields:
            # verbose_name is the field's name with underscores replaced with spaces
            if field.verbose_name.startswith('predicate') and field.verbose_name.endswith('Status') and getattr(predicate.restaurant, field.verbose_name) == 0:
                predicateFailed = True
                break

        if predicateFailed:
            predicate = markFailed(predicate)

    if predicate.value==None:
        # collect five more responses from workers when there are same 
        # number of yes and no
        predicate.restaurant = incrementStatus(predicate.index, predicate.restaurant)
    predicate.restaurant.save()
    predicate.save()

    # TODO uncomment this if desired
    #printResults()

    return predicate.restaurant

def printResults():
    """
    If there are no more predicates to be evaluated, print the restaurants satisfying all
    predicates to the terminal.
    """
    left = RestaurantPredicate.objects.filter(value=None)
    if len(left)==0:
        print "----------RESULTS-----------"
        print "The following restaurants satisfied all predicates"
        filtered = Restaurant.objects.exclude(hasFailed=True)
        for restaurant in filtered:
            print str(restaurant) + " " + str(restaurant.predicate0Status) + " " + str(restaurant.predicate1Status) + " " + str(restaurant.predicate2Status)
        print "----------------------------"

def markFailed(predicate):
    """
    Set all predicate status fields to -1 to indicate that it needs no further evaluation (because
    it has failed a predicate)
    """
    for field in predicate.restaurant._meta.fields:
        if field.verbose_name.startswith('predicate') and field.verbose_name.endswith('Status'):
            predicate.restaurant.hasFailed = True
    predicate.save()
    return predicate

def updateCounts(pB, task):
    """
    updates the predicate branch's total and "No!" counts relative to the confidence levels
    """
    if task.answer==True:
        pB.returnedTotal += float(task.confidenceLevel)/100.0
    elif task.answer==False:
        pB.returnedTotal += float(task.confidenceLevel)/100.0
        pB.returnedNo += float(task.confidenceLevel)/100.0
    pB.save()

def eddy(ID):
    """
    Uses a random lottery system to determine which eligible predicate should be
    evaluated next.
    """

    # find all the tasks this worker has completed
    completedTasks = Task.objects.filter(workerID=ID)
    # find all the predicates matching these completed tasks
    completedPredicates = RestaurantPredicate.objects.filter(
        id__in=completedTasks.values('restaurantPredicate_id'))

    # all fields for a restaurant referenced by an incomplete predicate
    restaurantFields = RestaurantPredicate.objects.all()[0].restaurant._meta.fields

    # finds number of predicate statuses
    numOfPredicateStatuses = 0
    for field in restaurantFields:
        if field.verbose_name.startswith('predicate') and field.verbose_name.endswith('Status'):
            numOfPredicateStatuses += 1

    # excludes all completed predicates from all restaurant predicates to get only incompleted ones
    incompletePredicates1 = RestaurantPredicate.objects.exclude(id__in=completedPredicates)

    incompletePredicates = incompletePredicates1.filter(restaurant__hasFailed=False).filter(value=None)
    # finds eligible predicate branches
    eligiblePredicateBranches = []
    for i in range(numOfPredicateStatuses):
        for pred in incompletePredicates:
            if pred.index == i:
                eligiblePredicateBranches.append(PredicateBranch.objects.filter(index=i)[0])
                break

    if (len(eligiblePredicateBranches) != 0):
        chosenBranch = runLotteryWeighted(eligiblePredicateBranches)
    else:
        return None

    # generates the restaurant with the highest priority for the specified 
    # predicate branch
    chosenRestaurant = findRestaurant(chosenBranch, ID)
    print chosenRestaurant.name
    # mark chosenRestaurant as being in chosenBranch
    chosenRestaurant.evaluator = chosenBranch.index

    # Find the RestaurantPredicate corresponding to this Restaurant and 
    # PredicateBranch
    chosenPredicate = RestaurantPredicate.objects.filter(restaurant = chosenRestaurant, question = chosenBranch.question)[0]

    return chosenPredicate
    
def decrementStatus(index, restaurant):
    """
    decrease the status by 1 once an answer has been submitted for that predicate
    """
    check = 'predicate' + str(index)

    # iterates through all the fields in restaurant
    for field in restaurant._meta.fields:
        if field.verbose_name.startswith(check) and field.verbose_name.endswith('Status'):
            # gets the number times the predicate still needs to be asked to this restaurant
            currentLeftToAsk = getattr(restaurant, field.verbose_name)
            #sets the field to currentLeftToAsk-1
            setattr(restaurant, field.verbose_name, currentLeftToAsk-1)
            #print "Decremented " + field.verbose_name + " to status of " + str(currentLeftToAsk-1)
    restaurant.save()

def incrementStatus(index, restaurant):
    """
    increases the status by 2 because the answer is not certain
    """
    statusName = 'predicate' + str(index) + 'Status'

    if getattr(restaurant, statusName)==0:
        setattr(restaurant, statusName, 2)

    restaurant.save()
    return restaurant

# def findTotalTickets(pbSet):
#     """
#     Finds the total number of "tickets" held by a set of PredicateBranches, by 
#     turning selectivity into a useful integer.
#     Selectivity = (no's)/(total evaluated)
#     """
#     totalTickets = 0

#     # award tickets based on computed selectivity
#     for pb in pbSet:
#         selectivity = float(pb.returnedNo)/float(pb.returnedTotal)
#         totalTickets += int(selectivity*1000)

#     return int(totalTickets)

# def runLottery(pbSet):
#     """
#     runs the lottery algorithm
#     """
#     #retrieves total num of tickets in valid predicates branches
#     totalTickets = findTotalTickets(pbSet)
#     if totalTickets==0:
#         print "Total tickets is zero"
#         return None

#     # generate random number between 1 and totalTickets
#     rand = randint(1, totalTickets)

#     # check if rand falls in the range corresponding to each predicate
#     lowBound = 0
#     selectivity = float(pbSet[0].returnedNo)/pbSet[0].returnedTotal
#     highBound = selectivity*1000
    
#     # an empty PredicateBranch object NOT saved in the database
#     chosenBranch = PredicateBranch()

#     # loops through all valid predicate branches
#     for j in range(len(pbSet)):

#         # if rand is in this range, then go to this predicateBranch
#         if lowBound <= rand <= highBound:
#             chosenBranch = pbSet[j]
#             break
#         else:
#             # move on to next range of predicateBranch
#             lowBound = highBound
#             nextPredicateBranch = pbSet[j+1]
#             nextSelectivity = float(nextPredicateBranch.returnedNo)/nextPredicateBranch.returnedTotal
#             highBound += nextSelectivity*1000

#     return chosenBranch

def runLotteryWeighted(pbSet):
    """
    runs the lottery algorithm
    """
    global INDEX

    changeBranch = True
    pastBranchExists = False

    totalTickets = 0
    tickets = {}
    highestBranch = pbSet[0]

    highestSelectivity = 0
    otherSelectivities = 0

    multiplyingFactor = 2

    for branch in pbSet:
        t = (float(branch.returnedNo)/branch.returnedTotal)*1000
        tickets[branch] = t
        totalTickets += t
        # print "t: " + str(t)
        if t > (float(highestBranch.returnedNo)/highestBranch.returnedTotal)*1000:
            highestBranch = branch
            highestSelectivity = float(highestBranch.returnedNo)/highestBranch.returnedTotal

    for branch in pbSet:
        if branch != highestBranch:
            otherSelectivities += float(branch.returnedNo)/branch.returnedTotal

    #multiplying factor
    multiplyingFactor = 8 - (highestSelectivity - otherSelectivities)

    for pb in pbSet:
        if pb.index == INDEX:
            pastBranchExists = True
            predBranch = pb
            break

    if pastBranchExists:
        if float(highestBranch.returnedNo)/float(highestBranch.returnedTotal) - float(predBranch.returnedNo)/float(predBranch.returnedTotal) < 0.10/exp(len(Task.objects.all())/50) :
            changeBranch = False

    if changeBranch:
        totalTickets += tickets[highestBranch]*(multiplyingFactor-1)
        tickets[highestBranch] *= multiplyingFactor
    else:
        tickets[predBranch] *= 2
        totalTickets += tickets[predBranch]/2

    # generate random number between 1 and totalTickets
    rand = randint(1, int(totalTickets))
    # print "rand: " + str(rand) + " " + str(totalTickets)
    # check if rand falls in the range corresponding to each predicate
    
    lowBound = 0
    highBound = tickets[pbSet[0]]
    # print tickets
    # an empty PredicateBranch object NOT saved in the database
    chosenBranch = PredicateBranch()
    # loops through all valid predicate branches
    for j in range(len(pbSet)):
        # print "low: " + str(lowBound) + " to high: " + str(highBound)
        # if rand is in this range, then go to this predicateBranch
        if lowBound <= rand <= highBound:
            chosenBranch = pbSet[j]
            break
        else:
            # move on to next range of predicateBranch
            lowBound = highBound
            nextPredicateBranch = pbSet[j+1]
            highBound += tickets[nextPredicateBranch]
    
    # theBranch = PredicateBranch()
    # selectivity = 0

    # if (len(pbSet.all().filter(index=INDEX)) > 0):
    #     predBranch = pbSet.objects.all().filter(index=INDEX)[0]

    #     # pick predicate branch with max selectivity
    #     for branch in PredicateBranch.objects.all():
    #         if float(branch.returnedNo)/float(branch.returnedTotal) > selectivity:
    #             theBranch = branch
    #             selectivity = float(branch.returnedNo)/float(branch.returnedTotal)

    #     # compare it with past branch and see if it surpasses a certain threshold
    #     if float(theBranch.returnedNo)/float(theBranch.returnedTotal) - float(predBranch.returnedNo)/float(predBranch.returnedTotal) < 0.15/exp(len(Task.objects.all())/50) :
    #         chosenBranch = PredicateBranch.objects.all().filter(index=INDEX)[0]

    # INDEX = chosenBranch.index

    # wantToPrint = ""
    # for branch in PredicateBranch.objects.all():
    #     wantToPrint += str(float(branch.returnedNo)/float(branch.returnedTotal)) + " "

    # print wantToPrint
    # print chosenBranch.index 

    if chosenBranch.index != INDEX:
        print "changed to " + str(chosenBranch.index)

    INDEX = chosenBranch.index

    return chosenBranch

def runLotteryDynamicallyWeighted(pbSet):
    """
    runs the lottery algorithm
    """
    totalTickets = 0
    tickets = {}
    highestBranch = pbSet[0]
    for branch in pbSet:
        t = (float(branch.returnedNo)/branch.returnedTotal)*1000
        tickets[branch] = t
        totalTickets += t
        if t > (float(highestBranch.returnedNo)/highestBranch.returnedTotal)*1000:
            highestBranch = branch

    # if len(Task.objects.all()) < 100:
    #     tickets[highestBranch] *= (1+len(Task.objects.all())/25*.25)
    # else:
    tickets[highestBranch] *= 2


    # generate random number between 1 and totalTickets
    rand = randint(1, int(totalTickets))

    # check if rand falls in the range corresponding to each predicate
    lowBound = 0
    highBound = tickets[pbSet[0]]
    
    # an empty PredicateBranch object NOT saved in the database
    chosenBranch = PredicateBranch()
    # loops through all valid predicate branches
    for j in range(len(pbSet)):

        # if rand is in this range, then go to this predicateBranch
        if lowBound <= rand <= highBound:
            chosenBranch = pbSet[j]
            break
        else:
            # move on to next range of predicateBranch
            lowBound = highBound
            nextPredicateBranch = pbSet[j+1]
            highBound += tickets[nextPredicateBranch]

    return chosenBranch


def runLotteryWithUniform(pbSet):
    totalTickets = 0.0
    rangeRand = 0.0
    tickets = {}
    highestBranch = pbSet[0]

    for branch in pbSet:
        totalTickets += float((1+ALPHA)**(branch.returnedNo))

    for branch in pbSet:
        tickets[branch] = ( (float(1+ALPHA)**(branch.returnedNo))/totalTickets*(1-GAMMA) + GAMMA/len(PredicateBranch.objects.all()) ) * 1000
        rangeRand+= tickets[branch]

    # generate random number between 1 and totalTickets
    rand = randint(1, int(rangeRand))

    # check if rand falls in the range corresponding to each predicate
    
    lowBound = 0
    highBound = tickets[pbSet[0]]
    
    # an empty PredicateBranch object NOT saved in the database
    chosenBranch = PredicateBranch()
    # loops through all valid predicate branches
    for j in range(len(pbSet)):

        # if rand is in this range, then go to this predicateBranch
        if lowBound <= rand <= highBound:
            chosenBranch = pbSet[j]
            break
        else:
            # move on to next range of predicateBranch
            lowBound = highBound
            nextPredicateBranch = pbSet[j+1]
            highBound += tickets[nextPredicateBranch]

    return chosenBranch
    
def findRestaurant(predicateBranch,ID):
    """
    Finds the restaurant with the highest priority for a specified predicate such that the relevant worker
    has not answered the relevant question about the restaurant.
    """
    # find all the tasks this worker has completed
    completedTasks = Task.objects.filter(workerID=ID)

    # find all the predicates for this branch that have been done by the worker
    completedPredicates = RestaurantPredicate.objects.filter(question=predicateBranch.question).filter(
        id__in=completedTasks.values('restaurantPredicate_id')).filter(value=None)

    # get the Restaurants NOT associated with the completed predicates
    rSet = Restaurant.objects.exclude(id__in=completedPredicates.values('restaurant_id')).exclude(hasFailed=True)

    # order the eligible restaurants by priority
    orderByThisStatus = '-predicate' + str(predicateBranch.index) + 'Status'
    prioritized = rSet.order_by(orderByThisStatus)

    return prioritized[0]

# def findRestaurant(predicateBranch,ID):
#     """
#     Finds a random eligible restaurant.
#     """
#     # find all the tasks this worker has completed
#     completedTasks = Task.objects.filter(workerID=ID)

#     # find all the predicates for this branch that have been done by the worker
#     completedPredicates = RestaurantPredicate.objects.filter(question=predicateBranch.question).filter(
#         id__in=completedTasks.values('restaurantPredicate_id')).filter(value=None)

#     # get the Restaurants NOT associated with the completed predicates
#     rSet = Restaurant.objects.exclude(id__in=completedPredicates.values('restaurant_id')).exclude(hasFailed=True).order_by('?')

#     return rSet[0]

#------------------------------------------------------------------------------------------------------------------------------------#
  
    #     if status > 0:
    #         lowestStat = status
    #         break

    # lowestUncertainty = 1.0
    # predicate = RestaurantPredicate.objects.filter(question=predicateBranch.question)[0]
    # for restaurant in prioritized:
    #     status = getattr(restaurant, predStatus)

    #     if status > lowestStat:
    #         break

    #     if status == lowestStat:

    #         yes = Task.objects.filter(restaurantPredicate=predicate, answer = True)
    #         no = Task.objects.filter(restaurantPredicate=predicate, answer = False)

    #         totalYes = 0.0
    #         totalNo = 0.0

    #         for pred in yes:
    #             totalYes += pred.confidenceLevel/100.0
    #             totalNo += 1 - pred.confidenceLevel/100.0

    #         for pred in no:
    #             totalYes += 1 - pred.confidenceLevel/100.0
    #             totalNo += pred.confidenceLevel/100.0

    #         uncertaintyLevelFalse = btdtr(totalNo+1, totalYes+1, DECISION_THRESHOLD)

    #         if uncertaintyLevelFalse < lowestUncertainty:
    #             chosenRestaurant = restaurant
    #             lowestUncertainty = uncertaintyLevelFalse

    # return chosenRestaurant

#--------------------------------------------------------------------------------------------------------------------------------------#

def randomAlgorithm(ID):
    """
    Randomly selects the next predicate from the available choices.
    """
    # get all the tasks this worker has done
    completedTasks = Task.objects.filter(workerID=ID)

    # find all the predicates that haven't been done by this worker
    notCompletedPredicates = RestaurantPredicate.objects.exclude(id__in=completedTasks.values('restaurantPredicate_id')).filter(value=None).exclude(restaurant__hasFailed=True)

    if len(notCompletedPredicates) == 0:
        return None
    else:
        chosenPredicate = choice(notCompletedPredicates)
         # mark chosenRestaurant as being in chosenBranch
        chosenPredicate.restaurant.evaluator = chosenPredicate.index
        return chosenPredicate

