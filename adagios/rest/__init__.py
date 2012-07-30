"""
Rest Easy - The simplest rest module on the planet

This Django Module provides GENERIC rest functionality to any module.

How to use:
Add this to your main urls.py
######
    (r'^rest/os', include('rest.urls'), {'module_name':'os'}),
######

You can now access any attribute and call any function of the os module.
"""
