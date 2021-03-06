#!/usr/bin/env python
#
# Copyright 2012 Andy Gimma
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# System libraries.
from wtforms import Form, BooleanField, TextField, validators, PasswordField, ValidationError, RadioField, SelectField

import cgi
import jinja2
import logging
import os
import urllib2
import wtforms.validators
import HTMLParser
import json



# Local libraries.
import base
import event_db
import site_db
import site_util
import cache
import form_db
import event_db
import form_types_db

from datetime import datetime
import settings

from google.appengine.ext import db
import organization
import primary_contact_db
import random_password
import incident_csv_db

jinja_environment = jinja2.Environment(
loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
template = jinja_environment.get_template('admin_create_incident_csv.html')
#CASE_LABELS = settings.CASE_LABELS
#COUNT = 26
GLOBAL_ADMIN_NAME = "Admin"
cache_time = 60 * 60
HTML_PARSER = HTMLParser.HTMLParser()
PROPERTIES_LIST = []
PROPERTIES_TYPES_LIST = []

class AdminCreateIncidentCSVHandler(base.AuthenticatedHandler):
    def AuthenticatedGet(self, org, event):
        global_admin = False
        local_admin = False
        
        if org.name == GLOBAL_ADMIN_NAME:
            global_admin = True
        if org.is_admin == True and global_admin == False:
            local_admin = True
        if global_admin == False and local_admin == False:
            self.redirect("/")
            return
            
	query_string = "SELECT * FROM Event"
	events = db.GqlQuery(query_string)
        self.response.out.write(template.render(
        {
	  "event_results": events,
        }))
        return
        
        
    def AuthenticatedPost(self, org, event):
	global_admin = False
        local_admin = False
        
        if org.name == GLOBAL_ADMIN_NAME:
            global_admin = True
        if org.is_admin == True and global_admin == False:
            local_admin = True
        if global_admin == False and local_admin == False:
            self.redirect("/")
            return
      
	incident_id = self.request.get("choose_incident")
	incident_csv = str(self.request.get("incident_csv"))
	incident_csv = incident_csv.replace(" ", "")
	
	incident_csv_list = incident_csv.split(',')
	
	
	#incident_csv_list = []
	#for i in incident_csv.split():
	  #incident_csv_list.append(i)
	event = event_db.Event.get_by_id(int(incident_id))

	i = incident_csv_db.IncidentCSV(incident = event.key(), incident_csv = incident_csv_list)
	incident_csv_db.PutAndCache(i, 600)
	
	self.redirect("/admin")

	# split incident_csv into a list
	# save that list to incident_csv_db