from django.db import models

class Employer(models.Model):
    company_name=models.CharField(max_length=100)
    email=models.EmailField(unique=True)
    location=models.CharField(max_length=100)

class Candidate(models.Model):
    full_name=models.CharField(max_length=100)
    email=models.EmailField(unique=True)
    phone=models.CharField(max_length=15)
    skills=models.TextField()
    resume=models.FileField(upload_to='resumes/')

class Job(models.Model):
    employer=models.ForeignKey(Employer,on_delete=models.CASCADE)
    title=models.CharField(max_length=100)
    description=models.TextField()
    location=models.CharField(max_length=100)
    salary=models.IntegerField()

class Application(models.Model):
    candidate=models.ForeignKey(Candidate,on_delete=models.CASCADE)
    job=models.ForeignKey(Job,on_delete=models.CASCADE)
    status=models.CharField(max_length=20,default='Applied')
