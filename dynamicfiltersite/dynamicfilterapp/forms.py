# -*- coding: utf-8 -*-
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import pre_save
from django import forms
from models import Restaurant, RestaurantPredicate, PredicateBranch, WorkerID

class WorkerForm(forms.Form):
    """
    Form for a crowd worker to enter a vote on an item-predicate pair.
    """
    # each choice corresponds to a float: sign indicates yes/no, value indicates confidence
    WORKER_ANSWER_CHOICES = (
        (1, "Yes (totally sure)"),
        (0.8, "Yes (fairly sure)"),
        (0.6, "Yes (somewhat sure)"),
        (0, "I don't know."),
        (-0.6, "No (somewhat sure)"),
        (-0.8, "No (fairly sure)"),
        (-1.0, "No (totally sure)"),
    )

    # Set up two fields for worker's answer and feedback
    answerToQuestion = forms.ChoiceField(choices=WORKER_ANSWER_CHOICES, widget=forms.Select(), label="Answer Choices:")
    feedback = forms.CharField(widget=forms.Textarea, label='Comments/Concerns/Feedback:', required=False)

class RestaurantAdminForm(forms.ModelForm):
    """
    For for admin to add Restaurants to the database. Extends ModelForm.
    """
    class Meta:
        # Tells Django which model is being created and which fields to display
        model = Restaurant
        fields = '__all__'
        exclude = ['text', 'hasFailed', 'evaluator', 'queueIndex']

    def __init__(self, *args, **kwargs):
        super(RestaurantAdminForm, self).__init__(*args, **kwargs)
        
    def save(self, commit=True):
        """
        Upon saving a new Restaurant into the database, create the corresponding RestaurantPredicates and PredicateBranches if they
        don't already exist.
        """
        # Save (create or update) the Restaurant generated by this form
        instance = super(RestaurantAdminForm, self).save(commit=False)

        instance.queueIndex = len(Restaurant.objects.all())

        instance.save()
        
        # Create RestaurantPredicates if they don't exist yet
        # For now, hard-coded to these ten questions
        RestaurantPredicate.objects.get_or_create(index=0, restaurant=instance, 
            question="Does this restaurant have a parking lot?")
        RestaurantPredicate.objects.get_or_create(index=1, restaurant=instance, 
            question="Does this restaurant have a drive-through?")
        RestaurantPredicate.objects.get_or_create(index=2, restaurant=instance, 
            question="Does this restaurant have drinks for those under 21?")
        RestaurantPredicate.objects.get_or_create(index=3, restaurant=instance, 
            question="Does this restaurant have more than 20 items on its menu?")
        RestaurantPredicate.objects.get_or_create(index=4, restaurant=instance, 
            question="Does this restaurant serve Chinese food?")
        RestaurantPredicate.objects.get_or_create(index=5, restaurant=instance, 
            question="Is this restaurant open until midnight?")
        RestaurantPredicate.objects.get_or_create(index=6, restaurant=instance, 
            question="Would a typical meal at this restaurant cost more than $30?")
        RestaurantPredicate.objects.get_or_create(index=7, restaurant=instance, 
            question="Does this restaurant serve breakfast?")
        RestaurantPredicate.objects.get_or_create(index=8, restaurant=instance, 
            question="Does this restaurant have its own website?")
        RestaurantPredicate.objects.get_or_create(index=9, restaurant=instance, 
            question="Does this restaurant have a romantic atmosphere?")

        # Create PredicateBranches if they don't exist yet
        for predicate in RestaurantPredicate.objects.all():
            PredicateBranch.objects.get_or_create(index=predicate.index, 
                question=predicate.question)

        return instance


class IDForm(forms.ModelForm):
    """
    Form for worker to enter ID number before going to the "Answer a Question" page. Not needed for experiments
    run on Mechanical Turk, since ID information is recorded automatically there. (Mainly for site testing purposes.)
    Uses the WorkerID model to validate input as a positive integer.
    """

    class Meta:
        # Tells Django which model is being created and which fields to display
        model = WorkerID
        fields = ['workerID'] 