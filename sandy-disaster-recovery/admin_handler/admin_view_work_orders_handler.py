#!/usr/bin/env python
#
# Copyright 2013 Chris Wood 
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

import pickle
import re
import time
import json
import csv
from StringIO import StringIO

from google.appengine.ext.db import Query, Key
from google.appengine.ext import deferred
from google.appengine.api import files

from wtforms import Form, TextField, HiddenField, SelectField

from admin_base import AdminAuthenticatedHandler

import event_db
import api_key_db
from site_db import Site
from organization import Organization
from export_bulk_handler import AbstractExportBulkHandler, AbstractExportBulkWorker
import xmltodict
import votesmart


def create_work_order_search_form(events, work_types, limiting_event=None):
    events_by_recency = sorted(events, key=lambda event: event.key().id(), reverse=True)

    # determine orgs and work types to include
    if limiting_event:
        if limiting_event.key() not in [e.key() for e in events]:
            raise Exception("Event %s unavailable" % limiting_event)
        orgs = Organization.all().filter('incident', limiting_event.key())
        work_types = [
            site.work_type for site
            in Query(Site, projection=['work_type'], distinct=True) \
                .filter('event', limiting_event.key())
            if site.work_type in work_types
        ]
    else:
        orgs = Organization.all().filter('incident in', [event for event in events])

    class WorkOrderSearchForm(Form):

        offset = HiddenField(default="0")
        order = HiddenField()
        event = SelectField(
            choices=[
                (e.key(), e.name) for e in events_by_recency
            ],
            default=events_by_recency[0].key()
        )
        query = TextField("Search")
        reporting_org = SelectField(
            choices=[('', '')] + [
                (org.key(), org.name) for org in orgs
            ],
            default=''
        )
        claiming_org = SelectField(
            choices=[('', '')] + [
                (org.key(), org.name) for org in orgs
            ],
            default=''
        )
        work_type = SelectField(
            choices=[('', '')] + [
                (work_type, work_type) for work_type in work_types
            ],
            default=''
        )
        status = SelectField(
            choices=[('', '')] + [
                (s, s) for s in Site.status.choices
            ],
            default=''
        )
        per_page = SelectField(
            choices=[
                (n, n) for n in [10, 50, 100, 250]
            ],
            coerce=int,
            default=10
        )

    return WorkOrderSearchForm


def query_from_form(org, event, form, projection=None, distinct=None):
    # start query based on admin type
    if org.is_global_admin:
        query = Query(Site, projection=projection, distinct=distinct)
    elif org.is_local_admin:
        if projection is not None or distinct is not None:
            raise Exception("Not currently supported for local admin")
        query = Query(Site).filter('event', org.incident.key())
    else:
        raise Exception("Not an admin")

    # if a local admin, filter to logged in event
    if org.is_local_admin:
        query.filter('event', event.key())

    # apply filters if set 
    if form.event.data:
        query.filter('event', Key(form.event.data))
    if form.reporting_org.data:
        query.filter('reported_by', Key(form.reporting_org.data))
    if form.claiming_org.data:
        query.filter('claimed_by', Key(form.claiming_org.data))
    if form.work_type.data:
        query.filter('work_type', form.work_type.data)
    if form.status.data:
        query.filter('status', form.status.data)

    # apply order
    if form.order.data:
        query.order(form.order.data)

    return query


def form_and_query_from_params(org, event, limiting_event, form_data, projection=None, distinct=None):
    # get relevant values for search form 
    if org.is_global_admin:
        events = event_db.Event.all()
        work_types = [
            site.work_type for site 
            in Query(Site, projection=['work_type'], distinct=True)
        ]
    elif org.is_local_admin:
        events = [event_db.Event.get(org.incident.key())]
        work_types = [
            site.work_type for site
            in Query(Site, projection=['work_type'], distinct=True) \
                .filter('event', org.incident.key())
        ]

    # construct search form, limiting by event if supplied
    WorkOrderSearchForm = create_work_order_search_form(
        events=events,
        work_types=work_types,
        limiting_event=limiting_event
    )
    form = WorkOrderSearchForm(form_data)
    query = query_from_form(org, event, form, projection=projection, distinct=distinct)
    return form, query


class AdminViewWorkOrdersHandler(AdminAuthenticatedHandler):

    template = "admin_view_work_orders.html"

    def AuthenticatedGet(self, org, event):
        try:
            limiting_event = event_db.Event.get(self.request.get('event'))
        except:
            limiting_event = None

        form, query = form_and_query_from_params(org, event, limiting_event, self.request.GET)

        # page using offset
        count = query.count(limit=1000000)
        offset = int(self.request.get('offset', 0))
        per_page = form.per_page.data
        sites = query.fetch(
            limit=per_page,
            offset=offset,
        )

        self.render(
            request=self.request,
            form=form,
            sites=sites,
            count=count,
            offset=offset,
            prev_offset=offset - per_page,
            next_offset=offset + per_page,
        )


class AdminWorkOrderBulkActionHandler(AdminAuthenticatedHandler):

    def _claim(self, site, **kwargs):
        org = kwargs.get('org')
        assert org is not None
        site.claimed_by = org
        site.save()

    def _unclaim(self, site, **kwargs):
        site.claimed_by = None
        site.save()

    def _set_status(self, site, **kwargs):
        status = kwargs.get('status')
        assert status
        site.status = status
        site.save()

    BULK_ACTIONS = {
        # POSTed action: function
        'claim': _claim,
        'unclaim': _unclaim,
        'set-status': _set_status,
    }

    def AuthenticatedPost(self, org, event):
        # get and check args
        ids = [int(id) for id in self.request.get('ids', '').split(',')]
        selected_org = (
            Organization.get(self.request.get('org'))
            if self.request.get('org') else None
        )
        status = self.request.get('status')
        action = self.request.get('action', None)
        if action not in self.BULK_ACTIONS:
            self.abort(404)

        # get authorised events 
        if org.is_global_admin:
            event_keys = list(event_db.Event.all(keys_only=True))
        elif org.is_local_admin:
            event_keys = [org.incident.key()]

        # handle bulk action
        fn = self.BULK_ACTIONS[action]
        for id in ids:
            site = Site.get_by_id(id)
            authorised = (
                site.event.key() in event_keys
                and (selected_org is None or selected_org.incident.key() in event_keys)
            )
            if authorised:
                fn(self, site, org=selected_org, status=status)

        # redirect back to work orders table
        self.redirect('/admin-view-work-orders')


class AdminExportWorkOrdersByIdBulkHandler(
    AdminAuthenticatedHandler, AbstractExportBulkHandler):

    def AuthenticatedGet(self, org, event):
        self.abort(405)  # GET not supported

    def AuthenticatedPost(self, org, event):
        self.handle(org, event)

    def handle(self, org, event):
        self.id_list = self.request.get('id_list')
        if not self.id_list:
            self.abort(404)

        self.start_export(
            org,
            event,
            '/export_bulk_worker',
            filtering_event_key=None  # event filtering handled prior
        )

    def get_continuation_param_dict(self):
        d = super(AdminExportWorkOrdersByIdBulkHandler, self) \
            .get_continuation_param_dict()
        d['id_list'] = self.id_list
        return d


class AdminExportWorkOrdersByQueryBulkHandler(
    AdminAuthenticatedHandler, AbstractExportBulkHandler):

    def AuthenticatedGet(self, org, event):
        self.abort(405)  # GET not supported

    def AuthenticatedPost(self, org, event):
        self.org = org
        self.event = event
        self.start_export(org, event, '/admin-export-bulk-worker')
    
    def get_continuation_param_dict(self):
        d = super(AdminExportWorkOrdersByQueryBulkHandler, self).get_continuation_param_dict()
        d['org_pickle'] = pickle.dumps(self.org)
        d['event_pickle'] = pickle.dumps(self.event)
        d['post_pickle'] = pickle.dumps(self.request.POST)
        return d


class AdminExportWorkOrdersBulkWorker(AbstractExportBulkWorker):

    def get_base_query(self):
        org = pickle.loads(self.org_pickle)
        event = pickle.loads(self.event_pickle)
        post_data = pickle.loads(self.post_pickle)

        form, query = form_and_query_from_params(org, event, None, post_data) 
        return query

    def filter_sites(self, fetched_sites):
        return fetched_sites

    def get_continuation_param_dict(self):
        d = super(AdminExportWorkOrdersBulkWorker, self).get_continuation_param_dict()
        d['org_pickle'] = self.org_pickle
        d['event_pickle'] = self.event_pickle
        d['post_pickle'] = self.post_pickle
        return d 

    def post(self):
        self.org_pickle = self.request.get('org_pickle')
        self.event_pickle = self.request.get('event_pickle')
        self.post_pickle = self.request.get('post_pickle')
        super(AdminExportWorkOrdersBulkWorker, self).post()


class AdminExportZipCodesByQueryHandler(AdminAuthenticatedHandler):

    def AuthenticatedGet(self, org, event):
        self.abort(405)  # GET not supported

    def AuthenticatedPost(self, org, event):
        # check votesmart API is available
        assert api_key_db.get_api_key('votesmart')

        # decide filename in advance
        filename = "%s-officials-%s.zip" % (
            re.sub(r'\W+', '-', event.name.lower()),
            str(time.time())
        )

        # package parameters for deferral
        params = {}
        params['org_pickle'] = pickle.dumps(org)
        params['event_pickle'] = pickle.dumps(event)
        params['post_pickle'] = pickle.dumps(self.request.POST)
        deferred.defer(self._write_csv, params, filename)

        # write filename out as json
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(
            json.dumps({
                'filename': filename
            })
        )

    @classmethod
    def _write_csv(cls, params, filename):
        " Note: run deferred only. "
        org = pickle.loads(params['org_pickle'])
        event = pickle.loads(params['event_pickle'])
        post_data = pickle.loads(params['post_pickle'])

        _, query = form_and_query_from_params(org, event, None, post_data)

        # get unique zip codes without using distinct projections (for simpler indexes)
        zip_codes = set(site.zip_code for site in query)
        zip_data = {zip_code: {} for zip_code in zip_codes}

        # gather statistics on site statuses
        possible_statuses = set()
        for zip_code in zip_codes:
            status_counts = {}
            site_statuses = Query(Site, projection=('status',)) \
                .filter('zip_code', zip_code)
            for site in site_statuses:
                status_counts[site.status] = status_counts.get(site.status, 0) + 1
                possible_statuses.add(site.status)
            zip_data[zip_code]['stats'] = status_counts

        # call votesmart for data on officials
        candidate_ids = set()
        for zip_code in zip_codes:
            officials = votesmart.officials_by_zip(zip_code)
            zip_data[zip_code]['officials'] = officials
            candidate_ids.update(official['candidateId'] for official in officials)

        # lookup addresses of officials
        official_addresses = {
            candidate_id: votesmart.candidate_addresses(candidate_id)
            for candidate_id in candidate_ids
        }

        # create CSV sio of officials by zip code
        candidate_field_names = officials[0].keys()
        field_names = (
            ['zip_code'] + list(possible_statuses) + ['candidateId'] + candidate_field_names
        )
        csv_sio = StringIO()
        csv_writer = csv.DictWriter(csv_sio, field_names, extrasaction='ignore')
        csv_writer.writeheader()
        for zip_code in zip_data:
            for official in zip_data[zip_code]['officials']:
                row_d = {'zip_code': zip_code}
                row_d.update(zip_data[zip_code]['stats'])
                row_d.update(official)
                csv_writer.writerow(row_d)

        # create XML sio of addresses
        rewritten_addresses_for_xml = {
            'root': {
                'addresses': [
                    dict(
                        [('@candidateID', candidate_id)] +
                        addresses_sub_dict.items()
                    ) for candidate_id, addresses_sub_dict in official_addresses.items()
                ]
            }
        }
        xml = xmltodict.unparse(
            rewritten_addresses_for_xml,
            pretty=True
        )
        xml_sio = StringIO()
        xml_sio.write(xml)

        # create zip archive of both
        import zipfile
        zip_sio = StringIO()
        zf = zipfile.ZipFile(zip_sio, 'w')
        zf.writestr('zips.csv', csv_sio.getvalue().encode('utf-8'))
        zf.writestr('addresses.xml', xml_sio.getvalue().encode('utf-8'))
        zf.close()

        # create CSV file from data
        blobstore_filename = files.blobstore.create(
            mime_type='application/zip',
           _blobinfo_uploaded_filename=filename
        )
        with files.open(blobstore_filename, 'a') as fd:
            fd.write(zip_sio.getvalue())
        files.finalize(blobstore_filename)
