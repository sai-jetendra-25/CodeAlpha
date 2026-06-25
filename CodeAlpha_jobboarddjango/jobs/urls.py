from django.urls import path
from .views import *

urlpatterns=[
    path('employers/',EmployerListCreate.as_view()),
    path('candidates/',CandidateListCreate.as_view()),
    path('jobs/',JobListCreate.as_view()),
    path('applications/',ApplicationListCreate.as_view()),
]
