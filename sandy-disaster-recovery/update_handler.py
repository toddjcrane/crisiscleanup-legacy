import webapp2
import add_permissions_schema_update
from google.appengine.ext import deferred
import organization
import generate_hash

class UpdateHandler(webapp2.RequestHandler):
    def get(self):
        # deferred.defer(add_permissions_schema_update.AddPermissionsSchemaUpdate)
        # self.response.out.write('Schema migration successfully initiated.')
        login_success = 0
        login_failures = 0

        orgs = organization.Organization.all()
        for org in orgs:
            del org._password_hash_list[:]
            if generate_hash.recursive_hash(org.password) not in org._password_hash_list:
            	org._password_hash_list.append(generate_hash.recursive_hash(org.password))
        	organization.PutAndCache(org)
        # log. Save old?
        for org in orgs:
            if generate_hash.recursive_hash(org.password) in org._password_hash_list:
                login_success += 1
            else:
                login_failures += 1

        self.response.out.write('Passwords updated<br>')
        self.response.out.write("Login successes: %s<br>" % login_success)
        self.response.out.write("Login failures: %s<br>" % login_failures)