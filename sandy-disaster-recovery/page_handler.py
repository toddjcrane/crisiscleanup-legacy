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
import jinja2
import os
import json

# Local libraries.
import base
import key
import page_db

jinja_environment = jinja2.Environment(
loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
template = jinja_environment.get_template('page.html')

class PageHandler(base.RequestHandler):

    def get(self):
	logged_in = False
        org, event = key.CheckAuthorization(self.request)
        if org and key:
	  logged_in = True

        # get page block params
        template_params = page_db.get_page_block_dict()

        # add version dictionary params
        try:
            with open('version.json') as version_json_fd:
                version_d = json.load(version_json_fd)
        except:
            version_d = None
        template_params.update({'version_d': version_d})

        template_params['logged_in'] = logged_in
        self.response.out.write(template.render(template_params))

