import csv
import webapp2
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext import db
import site_db
import event_db
from datetime import datetime
import logging

fields = ["claimed_by", "reported_by", "modified_by", "case_number", "days", "name", "request_date", "address", "city", "county", "state", "zip_code", "latitude", "longitude", "latitude_blur", "longitude_blur", "cross_street", "phone1", "phone2", "work_type", "older_than_60", "special_needs", "roof_clearing", "dig_out_car", "ice_removal", "driveway_clearing", "walkway_clearing", "stair_clearing", "ramp_clearing", "deck_clearing", "leaking", "structural_problems", "roof_collapse", "needs_food", "needs_clothing", "needs_shelter", "needs_fuel", "needs_tarp", "tree_debris", "needs_visual", "other_needs", "notes", "other_hazards", "claim_for_org", "status", "assigned_to", "total_volunteers", "hours_worked_per_volunteer", "initials_of_resident_present", "status_notes", "prepared_by", "do_not_work_before"]

class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        upload_files = self.get_uploads('file')  # 'file' is file upload field in the form
        blob_info = upload_files[0]
        process_csv(blob_info)

        blobstore.delete(blob_info.key())  # optional: delete file after import
        self.redirect("/")


def process_csv(blob_info):
    blob_reader = blobstore.BlobReader(blob_info.key())
    blob_iterator = BlobIterator(blob_reader)
    reader = csv.reader(blob_iterator)
    count = 0
    for row in reader:
        count += 1
        if count != 1:
            logging.info(len(fields))
            logging.info(len(row))
            claimed_by,reported_by,modified_by,case_number,name,request_date,do_not_work_before,address,city,county,state,zip_code,latitude,longitude,blurred_latitude,blurred_longitude,cross_street,phone1,phone2,time_to_call,work_type,rent_or_own,work_without_resident,member_of_assessing_organization,first_responder,older_than_60,special_needs,severity,damage_notes,flood_height,floors_affected,carpet_removal,hardwood_floor_removal,drywall_removal,appliance_removal,heavy_item_removal,standing_water,mold_remediation,pump_needed,work_requested,notes,nonvegitative_debris_removal,vegitative_debris_removal,debris_blocking,house_roof_damage,outbuilding_roof_damage,tarps_needed,help_install_tarp,num_trees_down,num_wide_trees,trees_blocking,habitable,electricity,electrical_lines,unsafe_roof,other_hazards,claim_for_org,status,assigned_to,total_volunteers,hours_worked_per_volunteer,initials_of_resident_present,status_notes,prepared_by = row
            claiming_org = None
            reporing_org = None

            if "NECHAMA" in claimed_by:
              claiming_org = 3419001

            if "Texas" in claimed_by:
              claiming_org = 5664902681198592

            if "NECHAMA" in reported_by:
              reporing_org = 3419001

            if "Texas" in reported_by:
              reporing_org = 5664902681198592


            site = site_db.Site(name=name,
                                claimed_by = claiming_org,
                                reported_by = reporing_org,
                                modified_by = None,
                                request_date= datetime.strptime(request_date, '%Y-%m-%d %H:%M:%S'),
                                case_number = case_number,
                                do_not_work_before = do_not_work_before,
                                address = address,
                                city = city,
                                county = county,
                                state = state,
                                zip_code = zip_code,
                                latitude = latitude,
                                longitude = longitude,
                                blurred_latitude = blurred_latitude,
                                blurred_longitude = blurred_longitude,
                                cross_street = cross_street,
                                phone1 = phone1,
                                phone2 = phone2,
                                time_to_call = time_to_call,
                                work_type = work_type
                                rent_or_own = rent_or_own
                                work_without_resident = work_without_resident
                                member_of_assessing_organization = member_of_assessing_organization
                                first_responder = first_responder
                                older_than_60 = older_than_60
                                special_needs = special_needs
                                severity = severity
                                damage_notes = damage_notes
                                flood_height = flood_height
                                floors_affected = floors_affected
                                carpet_removal = carpet_removal
                                hardwood_floor_removal = hardwood_floor_removal
                                drywall_removal = drywall_removal
                                appliance_removal = appliance_removal
                                heavy_item_removal = heavy_item_removal
                                standing_water = standing_water
                                mold_remediation = mold_remediation
                                pump_needed = pump_needed
                                work_requested = work_requested
                                notes = notes
                                nonvegitative_debris_removal = nonvegitative_debris_removal
                                vegitative_debris_removal = vegitative_debris_removal
                                debris_blocking = debris_blocking
                                house_roof_damage = house_roof_damage
                                outbuilding_roof_damage = outbuilding_roof_damage
                                tarps_needed = tarps_needed
                                help_install_tarp = help_install_tarp
                                num_trees_down = num_trees_down
                                num_wide_trees = num_wide_trees
                                trees_blocking = trees_blocking
                                habitable = habitable
                                electricity = electricity
                                electrical_lines = electrical_lines
                                unsafe_roof = unsafe_roof
                                other_hazards = other_hazards
                                claim_for_org = claim_for_org
                                status = status
                                assigned_to = assigned_to
                                total_volunteers = total_volunteers
                                hours_worked_per_volunteer = hours_worked_per_volunteer
                                initials_of_resident_present = initials_of_resident_present
                                status_notes = status_notes
                                prepared_by = prepared_by


            #if address:
                #org = site_db.Site.get_by_id(3419001)
                #site = site_db.Site(name=name,
                              #request_date= datetime.strptime(request_date, '%Y-%m-%d %H:%M:%S'),
                              #total_volunteers = total_volunteers,
                              #hours_worked_per_volunteer = hours_worked_per_volunteer,
                              #initials_of_resident_present = initials_of_resident_present,
                              #status_notes = status_notes,
                              #prepared_by = prepared_by,
                              #do_not_work_before = do_not_work_before,
                              #address = address,
                              #city = city,
                              #county = county,
                              #state = state,
                              #zip_code = zip_code,
                              #latitude = float(latitude),
                              #longitude = float(longitude),
                              #blurred_latitude = float(latitude_blur),
                              #blurred_longitude = float(longitude_blur),
                              #cross_street = cross_street,
                              #phone1 = phone1,
                              #phone2 = phone2,
                              #work_type = work_type,
                              #older_than_60 = older_than_60,
                              #special_needs = special_needs,
                              #roof_clearing = roof_clearing,
                              #dig_out_car = dig_out_car,
                              #ice_removal = ice_removal,
                              #driveway_clearing = driveway_clearing,
                              #walkway_clearing = walkway_clearing,
                              #stair_clearing = stair_clearing,
                              #ramp_clearing = ramp_clearing,
                              #deck_clearing = deck_clearing,
                              #leaking = leaking,
                              #structural_problems = structural_problems,
                              #roof_collapse = roof_collapse,
                              #needs_food = needs_food,
                              #needs_clothing = needs_clothing,
                              #needs_shelter = needs_shelter,
                              #needs_fuel = needs_fuel,
                              #needs_tarp = needs_tarp,
                              #tree_debris = tree_debris,
                              #needs_visual = needs_visual,
                              #other_needs = other_needs,
                              #notes = notes,
                              #other_hazards = other_hazards,
                              #status = 'Open, unassigned',
                              #assigned_to = assigned_to,
                              #reported_by = org,
                              #claimed_by = org
                              #)

                q = db.Query(event_db.Event)
                q.filter("name =", "Texas-Oklahoma floods")
                event = q.get()
                event_db.AddSiteToEvent(site, event.key().id())
class BlobIterator:
    """Because the python csv module doesn't like strange newline chars and
    the google blob reader cannot be told to open in universal mode, then
    we need to read blocks of the blob and 'fix' the newlines as we go"""

    def __init__(self, blob_reader):
        self.blob_reader = blob_reader
        self.last_line = ""
        self.line_num = 0
        self.lines = []
        self.buffer = None

    def __iter__(self):
        return self

    def next(self):
        if not self.buffer or len(self.lines) == self.line_num + 1:
            self.buffer = self.blob_reader.read(1048576)  # 1MB buffer
            self.lines = self.buffer.splitlines()
            self.line_num = 0

            # Handle special case where our block just happens to end on a new line
            if self.buffer[-1:] == "\n" or self.buffer[-1:] == "\r":
                self.lines.append("")

        if not self.buffer:
            raise StopIteration

        if self.line_num == 0 and len(self.last_line) > 0:
            result = self.last_line + self.lines[self.line_num] + "\n"
        else:
            result = self.lines[self.line_num] + "\n"

        self.last_line = self.lines[self.line_num + 1]
        self.line_num += 1

        return result
