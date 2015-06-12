from django import forms
from models import Restaurant, RestaurantPredicate

class WorkerForm(forms.Form):

    #choice fields for worker answering predicates
    WORKER_ANSWER_CHOICES = (
        (None, "------"),
        (True, 'Yes'),
        (False, 'No'),
    )

    #how confident a worker is in his/her answer
    CONFIDENCE_LEVELS = (
        (None, '------'),
        ('50', '50%'),
        ('60', '60%'),
        ('70', '70%'),
        ('80', '80%'),
        ('90', '90%'),
        ('100', '100%'),
    )

    #sets up form for answering predicate and worker's confidence level
    answerToQuestion = forms.ChoiceField(choices=WORKER_ANSWER_CHOICES, label='Your answer')
    confidenceLevel = forms.ChoiceField(choices=CONFIDENCE_LEVELS, label='Confidence level')

class RestaurantAdminForm(forms.ModelForm):

	class Meta:
		# Tells Django which model this form is creating and which fields to display
		model = Restaurant
		fields = ['name', 'url', 'text', 'street', 'city',
				'state', 'zipCode', 'country']

	def save(self, commit=True):
		# Save (create or update) the Restaurant generated by this form
		instance = super(RestaurantAdminForm, self).save(commit=False)
		instance.save()
		# Create the three associated predicates if they don't exist  yet
		RestaurantPredicate.objects.get_or_create(restaurant=instance, question="Does this restaurant accept credit cards?")
		RestaurantPredicate.objects.get_or_create(restaurant=instance, question="Is this a good restaurant for kids?")
		RestaurantPredicate.objects.get_or_create(restaurant=instance, question="Does this restaurant serve Choco Pies?")
		return instance


class IDForm(forms.Form):
	workerID = forms.IntegerField(label='Worker ID', min_value=0)