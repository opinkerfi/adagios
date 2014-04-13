# Adagios is a web based Nagios configuration interface
#
# Copyright (C) 2014, Pall Sigurdsson <palli@opensource.is>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
