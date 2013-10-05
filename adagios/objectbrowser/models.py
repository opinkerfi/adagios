from django.db import models

# Create your models here.


class Attribute(models.Model):

    """This class stores info on how attributes are viewed in django"""
    attribute_name = models.CharField(max_length=200)
    attribute_friendlyname = models.CharField(max_length=200)
    attribute_type = models.CharField(max_length=200)
