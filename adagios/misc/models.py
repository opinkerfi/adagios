from django.db import models

# Create your models here.


class TestModel(models.Model):
    testField = models.CharField(max_length=100)
    testField2 = models.CharField(max_length=100)


class BusinessProcess(models.Model):
    processes = models.ManyToManyField("self", unique=False, blank=True)
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100, blank=True)
    notes = models.CharField(max_length=1000, blank=True)
    #graphs = models.ManyToManyField(BusinessProcess, unique=False, blank=True)
    #graphs = models.ManyToManyField(BusinessProcess, unique=False, blank=True)


class Graph(models.Model):
    host_name = models.CharField(max_length=100)
    service_description = models.CharField(max_length=100)
    metric_name = models.CharField(max_length=100)
