#!/usr/bin/env python
#
# Copyright 2013 Andy Gimma
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
import logging
from google.appengine.ext.db import to_dict
from google.appengine.ext import db
from wtforms.ext.appengine.db import model_form
from google.appengine.api import memcache


# Local libraries
import cache
from models import incident_definition
import site_db


class Phase(db.Expando):
  incident = db.ReferenceProperty(incident_definition.IncidentDefinition, 'incident')
  site = db.ReferenceProperty(site_db.Site, "site")
  phase_id = db.StringProperty(default=True)
  
  
  
def PhaseToDict(phase):
  phase_dict = to_dict(phase)
  phase_dict["site_id"] = phase.site.key().id()
  phase_dict["id"] = phase.key().id()
  return phase_dict