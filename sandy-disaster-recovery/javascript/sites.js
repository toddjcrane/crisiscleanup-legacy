/**
 * Copyright 2012-2013 Jeremy Pack, Chris Wood
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 **/

goog.require('goog.ui.ac');
goog.require('goog.dom');
goog.require('goog.events.EventType');
goog.require('goog.json');
goog.require('goog.net.XhrIo');
goog.require('goog.string');
goog.require('goog.ui.Dialog');
goog.require('goog.ui.Dialog.ButtonSet');
goog.require('goog.ui.Option');
goog.require('goog.ui.Select');
goog.require('goog.style');
goog.require('goog.dom.forms');

goog.provide('sandy.sites');

var sites = [];
var siteMap = {};
var terms = [];
var loadedCases = {};

sandy.sites.loadSitesById = function (id, callBack) {
    //todo id can be array?
    sandy.sites.loadSites('/api/site_ajax?id=' + id, callBack);
};


sandy.sites.addSearchTerm = function (site) {
    if (site.case_number && site.name) {
        var term = site.case_number + ": <" + site.name + ">";
        if (site.address) {
            term += " " + site.address;
        }
        if (site.city) {
            term += " " + site.city;
        }
        if (site.state) {
            term += " " + site.state;
        }
        if (site.zip_code) {
            term += " " + site.zip_code;
        }
        if (site.reported_by) {
            term += " (" + site.reported_by.name + ") ";
        }
        if (site.claimed_by) {
            term += " (" + site.claimed_by.name + ") ";
        }
        if (site.notes) {
            term += " " + site.notes;
        }
        if (site.status_notes) {
            term += " " + site.status_notes;
        }
        if (site.damage_notes) {
            term += " " + site.damage_notes;
        }
        terms.push(term);
        siteMap[term] = site;
    }
};


sandy.sites.loadSites = function (url, callBack) {
    goog.net.XhrIo.send(url, function (e) {
        var xhr = e.target;
        var empty = true;
        var status = xhr.getStatus();
        if (status == 200) {
            var newSites = xhr.getResponseJson();
            if (newSites.length === 0) return false;
            sites = [];
            for (var i = 0; i < newSites.length; ++i) {
                if (sandy.sites.loadedCases[newSites[i].case_number]) continue;
                sandy.sites.loadedCases[newSites[i].case_number] = true;
                sites.push(newSites[i]);
            }

            for (i = 0; i < sites.length; ++i) {
                sandy.sites.addSearchTerm(sites[i]);
            }

            if (callBack) {
                callBack();
            }
        }
    });
};

sandy.sites.loadSitesBatch = function (sites_status, page, url, callBack) {
    goog.net.XhrIo.send(url, function (e) {
        var xhr = e.target;
        var empty = true;
        var status = xhr.getStatus();
        if (status == 200) {
            var newSites = xhr.getResponseJson();
            if (newSites.length === 0) return false;
            sites = [];
            for (var i = 0; i < newSites.length; ++i) {
                if (loadedCases[newSites[i].case_number]) continue;
                        loadedCases[newSites[i].case_number] = true;
                sites.push(newSites[i]);
            }

            if (sites.length > 0) {
                empty = false;
            }

            for (i = 0; i < sites.length; ++i) {
                try {
                    sandy.sites.addSearchTerm(sites[i]);
                } catch (err) {
                    txt="Error description: " + err.message + "\n\n";
                    goog.net.XhrIo.send('/js-logs?message=' + txt,
                    function (e) {
                        var xhr = e.target;
                        var status = xhr.getStatus();
                        if (status != 200) {
                            return;
                        }

                    });
                }

            }

            if (callBack) {
                callBack();
            }
        }
        if (!empty) {
            var new_page = page + 1;
            var new_url = '/api/site_ajax?status=' + sites_status + '&id=all&page=' + new_page;
            sandy.sites.loadSitesBatch(sites_status, new_page, new_url, callBack);
        }
    });
};

sandy.sites.loadSitesForCounty = function (county, status) {
    sandy.sites.loadSites('/api/site_ajax?status=' + status + '&id=all&county=' + county);
};

sandy.sites.batchLoadSites = function (status, page, callBack) {
    var url = '/api/site_ajax?status=' + status + '&id=all&page=' + page;
    sandy.sites.loadSitesBatch(status, page, url, callBack);
};

sandy.sites.tryBatchLoadSites = function (status, page, callBack) {
    try {
        sandy.sites.batchLoadSites(status, 0, callBack);
    } catch (err) {
        txt="Error description: " + err.message + "\n\n";
        goog.net.XhrIo.send('/js-logs?message=' + txt,
        function (e) {
            var xhr = e.target;
            var status = xhr.getStatus();
            if (status != 200) {
                return;
            }
        });
    }
};
