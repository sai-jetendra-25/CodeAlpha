from rest_framework import generics
from .models import *
from .serializers import *

class EmployerListCreate(generics.ListCreateAPIView):
    queryset=Employer.objects.all()
    serializer_class=EmployerSerializer

class CandidateListCreate(generics.ListCreateAPIView):
    queryset=Candidate.objects.all()
    serializer_class=CandidateSerializer

class JobListCreate(generics.ListCreateAPIView):
    queryset=Job.objects.all()
    serializer_class=JobSerializer

class ApplicationListCreate(generics.ListCreateAPIView):
    queryset=Application.objects.all()
    serializer_class=ApplicationSerializer
