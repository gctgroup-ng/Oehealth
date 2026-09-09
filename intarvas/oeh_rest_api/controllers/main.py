# -*- coding: utf-8 -*-
##############################################################################
#    Copyright (C) 2015 - Present, intarvas (<https://www.intarvas.in>). All Rights Reserved
#    intarvas, Hospital Management Solutions

# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used (executed,
# modified, executed after modifications) if you have purchased a valid license
# from the authors, typically via Odoo Apps, intarvas.in, intarvas.com, or if you have received a written
# agreement from the authors of the Software.
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without copying
# any source code or material from the Software. You may distribute those
# modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the Software
# or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

##############################################################################

import functools
import logging
from odoo import http, tools
from odoo.http import request
from odoo.addons.intarvas.oeh_rest_api.common_methods import invalid_response, valid_response, extract_arguments
import base64
import unicodedata
from datetime import datetime

_logger = logging.getLogger(__name__)

api_expires_in_minutes = 'intarvas.intarvas_rest_api_token_expires_in'

class intarvasRESTAPIToken(http.Controller):
    def __init__(self):

        self._token = request.env['oeh.rest.api.token']
        self._api_expires_in = request.env.ref(api_expires_in_minutes).sudo().value

    @http.route('/intarvas/request/token', methods=['GET'], type='http', auth='none', csrf=False)
    def request_token(self, **post):
        """The token URL is generated to authorize the token:

        Args:
            **post must contain login and password.
        Returns:
            - Data dictionary containing active token code, user type, user id, token expiration date
            and user’s notification receiving status.
            - Returns if failed error message in the body in json format
        Example:
           import requests

           headers = {'content-type': 'text/plain', 'charset':'utf-8'}

           data = {
               'login': 'admin',
               'password': 'admin',
               'db': 'example.com'
               'device_token': 'xxxxxxxxxxxxxxxxxxxxx',
               'device_type': 1 (1 for iOS, 2 for Android)
            }
           base_url = 'http://example.com'
           eq = requests.post(
               '{}/intarvas/request/token'.format(base_url), data=data, headers=headers)
           content = json.loads(req.content.decode('utf-8'))
           headers.update(token=content.get('access_token'))
        """
        user_type = 1   # 1: Patient, 2: Physician, 3: Health Center Admin
        _token = request.env['oeh.rest.api.token']
        db, username, password = post.get(
            'db'), post.get('login'), post.get('password')

        if not all([db, username, password]):
            # throw error message if any information from db, username, password are not provided or incorrect
            error_msg = 'either of the following are missing [db, login, password]'
            return invalid_response('missing error', error_msg)

        # Authenticate the provided credentials with Odoo's default auth method
        try:
            request.session.authenticate(db, username, password)
        except Exception as e:
            # Invalid database:
            info = "The database name or login credentials are not valid. {}".format((e))
            error = 'invalid_database'
            _logger.error(info)
            return invalid_response(error, info)

        uid = request.session.uid

        # odoo login failed:
        if not uid:
            info = "authentication failed"
            error = 'authentication failed'
            _logger.error(info)
            return invalid_response(error, info)

        patient_model = request.env['ir.model'].sudo().search([('model', '=', 'oeh.medical.patient')], limit=1)
        if not patient_model:
            info = "Oops! The model oeh.medical.patient is not available in the registry. " \
                   "Please check if intarvas module is properly installed on your server."
            error = "invalid object model"
            return invalid_response(error, info)

        physician_model = request.env['ir.model'].sudo().search([('model', '=', 'oeh.medical.physician')], limit=1)
        if not physician_model:
            info = "Oops! The model oeh.medical.physician is not available in the registry. " \
                   "Please check if intarvas module is properly installed on your server."
            error = "invalid object model"
            return invalid_response(error, info)

        user_id = False
        oeh_notification_obj = request.env['oeh.medical.notifications']
        user = request.env['res.users'].sudo().browse(int(uid))
        notification_status = True
        if user:
            device_type = 0
            if 'device_type' in post and post.get('device_type'):
                device_type = post.get('device_type')

            if request.env['oeh.medical.patient'].sudo().search([('oeh_patient_user_id', '=', int(user.id))], limit=1):
                user_type = 1
                patient = request.env['oeh.medical.patient'].sudo().search([('oeh_patient_user_id', '=', int(user.id))], limit=1)
                if patient:
                    user_id = patient.id
                    find_patient = oeh_notification_obj.sudo().search([('patient_id', '=', int(patient.id))], limit=1)
                    if find_patient:
                        patient_values = {
                            'device_type': str(device_type),
                        }
                        if 'device_token' in post and post.get('device_token'):
                            patient_values['device_registration_token'] = str(post.get('device_token'))
                        find_patient.sudo().write(patient_values)
                    else:
                        patient_values = {
                            'patient_id': int(patient.id),
                            'device_type': str(device_type),
                            'notification_setting': True,
                        }
                        if 'device_token' in post and post.get('device_token'):
                            patient_values['device_registration_token'] = str(post.get('device_token'))
                        find_patient = oeh_notification_obj.sudo().create(patient_values)

                    notification_status = find_patient.notification_setting
                else:
                    info = "The account is inactive or not found."
                    error = "invalid account"
                    return invalid_response(error, info)
            elif user.has_group('intarvas.group_oeh_medical_physician'):
                user_type = 2
                doctor = request.env['oeh.medical.physician'].sudo().search([('oeh_user_id', '=', int(user.id))], limit=1)
                if doctor:
                    user_id = doctor.id
                    find_doctor = oeh_notification_obj.sudo().search([('physician_id', '=', int(doctor.id))],
                                                                      limit=1)
                    if find_doctor:
                        doctor_values = {
                            'device_type': str(device_type),
                        }
                        if 'device_token' in post and post.get('device_token'):
                            doctor_values['device_registration_token'] = str(post.get('device_token'))
                        find_doctor.sudo().write(doctor_values)
                    else:
                        doctor_values = {
                            'physician_id': int(doctor.id),
                            'device_type': str(device_type),
                            'notification_setting': True,
                        }
                        if 'device_token' in post and post.get('device_token'):
                            doctor_values['device_registration_token'] = str(post.get('device_token'))
                        find_doctor = oeh_notification_obj.sudo().create(doctor_values)

                    notification_status = find_doctor.notification_setting
                else:
                    info = "The account is inactive or not found."
                    error = "invalid account"
                    return invalid_response(error, info)
            elif user.has_group('intarvas.group_oeh_medical_manager'):
                user_type = 3
                user_id = uid
            else:
                info = "The user is not authenticated to access any data because he/she is not related to any intarvas roles."
                error = "user is not authenticated"
                return invalid_response(error, info)

        # Generate new token if none available or get the existing one
        access_token_data = request.env['oeh.rest.api.token'].sudo().search([], order='id DESC', limit=1)
        if not access_token_data:
            access_token, expires_on = _token.sudo().find_or_create_token(create=True)
        else:
            access_token = access_token_data.Token
            expires_on = access_token_data.ExpirationDate
        # Successful response:
        success_response = {
                'uid': user_id,
                'token': access_token,
                'user_type': int(user_type),
                'expires_on': str(expires_on),
                'notification_status': notification_status,
            }
        return valid_response(success_response)


def authenticate_token(func):
    """This method will first authenticate sent token during every API call"""
    @functools.wraps(func)
    def auth_token(self, *args, **kwargs):
        access_token = request.httprequest.headers.get('token')
        if not access_token:
            return invalid_response('token_not_found', 'Missing token in request header')
        access_token_data = request.env['oeh.rest.api.token'].sudo().search([('Token', '=', access_token)], order='id DESC', limit=1)
        if not access_token_data:
            return invalid_response('invalid_token', 'Token is not valid')
        token, expired_on = access_token_data.sudo().find_or_create_token()
        if token != access_token:
            return invalid_response('invalid_token', 'Token seems to have expired or invalid')

        request.session.uid = access_token_data.UserId.id
        request.uid = access_token_data.UserId.id
        return func(self, *args, **kwargs)
    return auth_token


class intarvasRESTAPIController(http.Controller):

    def __init__(self):
        self._model = 'ir.model'

    def get_time_string(self,duration):
        result =''
        currentHours = int(duration // 1)
        currentMinutes =int(round(duration % 1 * 60))
        if(currentHours <= 9):
            currentHours = "0" + str(currentHours)
        if(currentMinutes <= 9):
            currentMinutes = "0" + str(currentMinutes)
        result = str(currentHours)+":"+str(currentMinutes)
        return result

    @authenticate_token
    @http.route(['/intarvas/get-user-details/<user_type>/<user_id>'], type='http', auth="none", methods=['GET'], csrf=False)
    def get_user_details(self, user_type=None,user_id=None, **payload):
        """This method will allow search details of given user id and type

        Args:
            token: must contain in headers to validate the call
            <user_type> must contain user's type [1: Patient, 2: Physician, 3: Health Center Admin]
            <user_id> Logged in User ID
            **payload should contains optional search term to be query to database
            - domain: optional. A search domain. Use an empty list to match all records. [ex: 'domain': "[('supplier','=',True),('parent_id','=', False)]" or 'domain':"[]"]
            - limit: Maximum number of records to return (default: all) [ex: 'limit': 10]
            - fields: list of field names to return (default is all fields) [ ex: fields=['name','country_id'] ].
            - order: record orders based on field name (ex: 'order': 'name asc')
        Returns:
            - Data dictionary containing user’s details based on his/her user type.
              (If logged in user is patient then API will return the response containing fields from patient’s table.
              If logged in user is doctor then API will return data from doctor’s table.)
            - Returns if failed error message in the body in json format
        """
        if not user_type:
            return invalid_response('user_type not found', 'User type not found in request ! ')

        if not user_id:
            return invalid_response('user_id not found', 'User ID not found in request ! ')

        if user_type == '1':
            model_name = 'oeh.medical.patient'
            model = request.env[self._model].sudo().search([('model', '=', model_name)], limit=1)
            payload['fields'] = "['id', 'name', 'dob', 'identification_code', 'image_512', 'age', 'marital_status', 'sex', 'blood_type', 'rh']"
            #payload['domain'] = "[('oeh_patient_user_id', '=', " + str(user_id) + ")]"
        elif user_type == '2':
            model_name = 'oeh.medical.physician'
            model = request.env[self._model].sudo().search([('model', '=', model_name)], limit=1)
            payload['fields'] = "['id', 'name', 'speciality', 'degree_id', 'image_512', 'available_lines']"
            #payload['domain'] = "[('oeh_user_id', '=', " + str(user_id) + ")]"
        else:
            model_name = 'res.users'
            model = request.env[self._model].sudo().search([('model', '=', model_name)], limit=1)
            payload['fields'] = "['id', 'name', 'image_512']"

        payload['domain'] = "[('id', '=', " + str(user_id) + ")]"

        if model:
            domain, fields, offset, limit, order = extract_arguments(
                payload)
            data = request.env[model.model].sudo().search_read(
                domain=domain, fields=fields, offset=offset, limit=limit, order=order)

            data_to_push = []
            for x in data:
                if 'image_512' in x:
                    x['image'] = x.pop('image_512')
                    if not x.get('image') or x.get('image') == 'false':
                        x['image'] = "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"
                for k, v in x.items():
                    # Handle bytes (images) and datetime fields to avoid any errors in response
                    if str(type(v)) == "<class 'bytes'>":
                        try:
                            v = v.decode('utf-8')
                        except AttributeError:
                            pass
                        x[k] = v
                    if str(type(v)) in ("<class 'datetime.datetime'>", "<class 'datetime.date'>"):
                        x[k] = str(v)
                    if str(k) == "degree_id":
                        degree_name = []
                        if v and len(v) > 0:
                            for degree_id in v:
                                degree = request.env['oeh.medical.degrees'].browse(int(degree_id))
                                if degree:
                                    degree_name.append(str(degree.name))
                        else:
                            degree_name = v
                        x[k] = degree_name
                    if str(k) == "speciality":
                        if v and len(v) > 0:
                            x[k] = v[1]
                        else:
                            x[k] = ""
                    if str(k) == "blood_type" or str(k) == "rh":
                        if not v:
                            x[k] = ""
                        else:
                            x[k] = v
                    if str(k) == "available_lines":
                        schedule_list = []
                        if v and len(v) > 0:
                            for schedule_id in v:
                                schedule = request.env['oeh.medical.physician.line'].browse(int(schedule_id))
                                if schedule:
                                    schedule_values = {
                                        'day': schedule.name,
                                        'start_time': self.get_time_string(schedule.start_time),
                                        'end_time': self.get_time_string(schedule.end_time),
                                    }
                                    schedule_list.append(schedule_values)
                        else:
                            schedule_list = v
                        x[k] = schedule_list
                data_to_push.append(x)

            return valid_response(data_to_push)
        return invalid_response('invalid object model', 'The model %s is not available in the registry.' % model_name)

    @authenticate_token
    @http.route(['/intarvas/get-patient-list'], type='http', auth="none", methods=['GET'], csrf=False)
    def get_patient_list(self, **payload):
        """This method will allow to list all patients

        Args:
            token: must contain in headers to validate the call
        Returns:
            - Data dictionary containing list of all patients with required fields.
            - Returns if failed error message in the body in json format
        """
        model_name = 'oeh.medical.patient'
        model = request.env[self._model].sudo().search([('model', '=', model_name)], limit=1)
        payload[
            'fields'] = "['id', 'name', 'dob', 'identification_code', 'image_512', 'age', 'marital_status', 'sex', 'blood_type', 'rh', 'labs_count', 'prescription_count']"

        if model:
            domain, fields, offset, limit, order = extract_arguments(
                payload)
            data = request.env[model.model].sudo().search_read(
                domain=domain, fields=fields, offset=offset, limit=limit, order=order)

            data_to_push = []
            for x in data:
                if 'image_512' in x:
                    x['image'] = x.pop('image_512')
                    if not x.get('image') or x.get('image') == 'false':
                        x['image'] = "iVBORw0KGgoAAAANSUhEUgAAALQAAAC0CAYAAAA9zQYyAAAD7GlDQ1BpY2MAAHjajZTPbxRlGMc/u/POrAk4B1MBi8GJP4CQQrZgkAZBd7vLtlDLZtti25iY7ezb3bHT2fGd2fIjPXHRG6h/gIocPJh4MsFfES7AQQMJQUNsSEw4lPgjRBIuhtTDTHcHaMX39Mzzfp/v9/s875OBzOdV33fTFsx6oaqU8tb4xKSVuUGaZ1hDN2uqduDnyuUhgKrvuzxy7v1MCuDa9pXv//OsqcnAhtQTQLMW2LOQOga6a/sqBOMWsOdo6IeQeRboUuMTk5DJAl31KC4AXVNRPA50qdFKP2RcwLQb1Rpk5oGeqUS+nogjDwB0laQnlWNblVLeKqvmtOPKhN3HXP/PM+u2lvU2AWuDmZFDwFZIHWuogUocf2JXiyPAi5C67If5CrAZUn+0ZsZywDZIPzWtDoxF+PSrJxqjbwLrIF1zwsHROH/Cmxo+HNWmz8w0D1VizGU76J8Enof0zYYcHIr8aNRkoQj0gLap0RqI+bWDwdxIcZnnRKN/OOLR1DvVg2WgG7T3VbNyOPKsnZFuqRLxaxf9sBx70BY9d3go4hSmDIojy/mwMToQ1YrdoRqNa8XktHNgMMbP+255KPImzqpWZSzGXK2qYiniEX9Lbyzm1DfUqoVDwA7Q93MkVUXSZAqJjcd9LCqUyGPho2gyjYNLCYmHROGknmQGZxVcGYmK4w6ijsRjEYWDvQomUrgdY5pivciKXSIr9oohsU/sEX1Y4jXxutgvCiIr+sTedm05oW9R53ab511aSCwqHCF/uru1taN3Ur3t2FdO3XmguvmIZ7nsJzkBAmbayO3J/i/Nf7ehw3FdnHvr2tpL8xx+3Hz1W/qifl2/pd/QFzoI/Vd9QV/Qb5DDxaWOZBaJg4ckSDhI9nABl5AqLr/h0UzgHlCc9k53d27sK6fuyPeG7w1zsqeTzf6S/TN7Pftp9mz294emvOKUtI+0r7Tvta+1b7QfsbTz2gXtB+2i9qX2beKtVt+P9tuTS3Qr8VactcQ18+ZG8wWzYD5nvmQOdfjM9WavOWBuMQvmxva7JfWSvThM4LanurJWhBvDw+EoEkVAFReP4w/tf1wtNoleMfjQ1u4Re0XbpVE0CkYOy9hm9Bm9xkEj1/FnbDEKRp+xxSg+sHX2Kh3IBCrZ53amkATMoHCYQ+ISIEN5LATob/rHlVNvhNbObPYVK+f7rrQGPXtHj1V1XUs59UYYWEoGUs3J2g7GJyat6Bd9t0IKSK270smFb8C+v0C72slNtuCLANa/3Mlt7YanP4Zzu+2Wmov/+anUTxBM79oZfa3Ng35zaenuZsh8CPc/WFr658zS0v3PQFuA8+6/WQBxeNNNGxQAAAAGYktHRAD+AP4A/usY1IIAAAAJcEhZcwAACxMAAAsTAQCanBgAAAAJdnBBZwAAALQAAAC0ABQgh9YAAFKVSURBVHja7b15rGbJdR/2O1V17/22t/Y6+8IZkkOOaFKkSZkUJVGyZS2UZDuS7Dgx7DiAsxhxEhvwFsQ24CSInQWGANsILNiAFQmQbcmKFMmWFFqiRIuLREokh5yF5Axn6+nu6e63fdtdqk7+qDpVdb/3hhyLM3x8r1/NdPd733f3e+rUr37nd04BZ+2snbWzdtbO2lk7a2ftrJ21s3bWztpZO2tn7aydtbN21s7aWTtrZ+2snbWzdtbO2lk7a2ftrJ21s3bWztpZO2tn7aydtbN21s7aWTtrZ+2snbWzdtbO2lk7a2ftrJ21s3bWjq/RcV/ASWnMDADY39tD07ZoAXTWwTYdmq5D21l0lsEOADO6zqJuW9iwnzSlCGVRwGgNAkBEUEqhKjTKwqAoNMpCoyoMyqLAcDQCwnZn7as3ddwXcNbO2mvZzrr9EY2ZQUS4dXMfTdthulxivqwxnS4wm9f4/Jdv4i/9me/S1/dvDef7i/Gybid1a9es5TE7HgOYtG03WjbNwDEKAAYEA0ApIqrK0hXGtARuQLTQSs2qotgbVGa3qordyajaW19b2/8r/+s/q3/oO9+FtckIg6rCaDxCWRjceX4jXuNZ67ezJxKaQIoXr9/CdLbA3t4B3v32N+PmjX29O5sV82VdzaaLSmtVjUdVVVbFWGm1QcznnHMXO8cXreVz7PgcM1/srN1q227NMQ8ZqOD/GCKiwhhrtF4CPCWiPUXqZmn0FWPUi0rRC0T0gnPu2sF8eWuxbGZVWSzLslxO1teaey5s2I//7hMYDgaYDId48P5LZ4adNXPcF/CN2MQ+6A3vw8GnfnUdwIPM/Khjfodr7X2LuqusQ1EUuigKUxVFORgoNVBEFYCKgQERlaSUAWDArDjCOwY7hmNeZ+YtAJfBqB27t1jr5summ3ednTdtt1jWdcPASwWbzzD448aYz//lv/m/7/3JH/ngmRG/Qrvtn8rNnT101uH6jV1cv7mLb3vv24unn71y/sbNnXsUqTvXJ+PzZWkeZMajTdO+A4y7i9LAaA2tFIzRMEbBaAVFCkQEBqDCd0QAZfNCBtDZDtY6MPuRwTHDWgvbObTWwloHay3argMD+4UxnyGij3fWfW46m19tW/vCeDB87u2PPrD/8d99gkdViXPrIyzqFg89dO9xP9JjbWce2jcqS0OXL2zpKy+9fA8B7ym0+WOO3bc4dhURFaNBVW5vTCqjNUgpeLNFcgmZ0Tr2H3RdB6ywHACBkfCvIoImgtEGKDmODmAOxu/GddO+s2nat3ZdNyeim4XR/64o9M9+4ekrTyhFOwBs/wpu33Zbe+gvPncFi7rBWx+8Z/j4l55/8NbuwQeGw8Gj65PRfVrR2xTRnUVhUBQGhTEojIZSHjkwc8DdDMcAOzFwjp6XHUds3nvSYrXyFRGY/SZK+e+JCATAOe+1u8577a5z1jF/wbH73els8dxiUT82rsrfeNujD73w4Y99xmlFeP973nbcj/bY2m1l0MIM/PbvPYnZfIH77r+jbNtuSwEPLOv2WxfL+s+VRfHWjcmYJ+MhDapC9pT/gyEng2Zw/AzIbJUB55LR55CXw2PneND0HclfRB6uIPxLFCFN03WYL5duOl3Omqb9nbIwPwHm37m1N73KzHtKUVOOB3jPo2/E565fx1svXjzuR/91a7c15GDmu5j5B+Z1+34FetuF7Y17BlWJsijIaA2Ak1Eyw8dMWPYNRsw9VJH/3J+3BZDC3PfinO3EYtveXXtYQgD7gIxWLhg5MKxKVWqz1rTdOxZ1c2E+rz/DjN8E8EsAnjvuZ3tc7bYy6P/pf/5f8KGPfApVUZh9O3tkd+fg2yfj4Q8Oq/IdRuvttfEQZVmAgrFZ6ydsYtA9kMrxLxCSk81/BrxRM1P8hhEd8EpH4OzQYUTg9LNjwDn/vVIKSimUhYFSapMZm2Bc0prO1XVbLer6N6nQj33kdz7XqKa5rTjr28qgh8MhAJhl09xZFOZHnOUPalIPTcbD0WBQQJHylJrLocQKRYHgeQMcAAAOximGSsicLmeemvvGrgIjAiI459JkMd83Hp/RudAhHEORg1YEIoXRoERVmu1lbd6366YPdNY8wE33jwE8DaDDbTRhvG0M+vEvPIuHH7oXH/rwb7+l6drvXV8f/ZHxaPDGyXgwrspgzOwixBALEI8K4CvOOMSQZR/5RYybOR2Ls4NHT00AMcUTJWiDiNURIIoDwxFgLUEp53UhRLoozGR9MnygKPT3Tuf1iJn/xZvvuuvXfurnPmQB4Nq1q7h06fJxv4rXtZ36cejpp69gXA2ws5wWbd1sThf1jxhj/tzW5uTNa5PR2rAsg4f0YzrDw4yEX1dmbVljZKKhzJO7zJMng0SELvnmsrvLRgPPTeedwUW87pygbAbYsyFaKShN4ViMxbLB3sF81nb2nzP4n2qiJw4O5tPvev87j/t1vO7ttvHQYGwVZfntm0X5HVqrN09Go/GgKOAjd715GTI/mdEOfZyc/+t/oez7hK0jYwGPgTl44QRpGYAL2waczSEYQwQiBqBC52AQfKdTpAIiZ3TOQYGglIcxhSmwNh4Np7PFH5vOF9tO0f8G4JPczkDF+LjfxOvaTr3a7p4L53Hxzi2ynb2radvvKQr9zrXJcK0qjSIiP9li571g3IuOHLpkavdqWyQwMiqaiOOfnLMTtqM/IAj06Y8SnsZD3M9PYB26zqKzfuZYGKPK0txRVcW3MuOD1rp3/PJvPGa+8Ozzx/1KXtd2qj305556Gk++8KIGY9uy+yYifLsx+r7hoIpBi0il5bO3I6zWBz84/ux3S/v0Jo+hCRHChz/NfvbdJOeyIyMSaUGXXRv39hYGw7GDdRwmjAQCoSoLMGP7oJ39sCm0G6+Pnwdwixc7joZbx/16Xpd2qg0aAG7uH1TW2u/ZmIx/9NzW+qXxcKCJ0I/i4WgBfe+zjNWI3Fxu/wIX5JM+WonfCYuRkLA/ECk/KRSPKzAlOwOYVq9TqBUGMUXM7ZhB8IZdFqaqquJBbdTb19dHj5Rl8RiAneN+L69XO9WQY20yVOuT0UZZFO8zRn/raFgNy6KIxnzIp2aY4kje9itgDjpiEzFootyzpy04N1mhAvNrWDm4OOdo9OEonOEUCh7dOj+R1EqpsixGRWHePJvXf/T6jd37/9ZPfxKfefLp4349r0s71QZ9MF2MqsLct7k2uXM0HExIkeIwqYo0WLY9hf+OmvVR8LroYWK/gYOn0nJjTY6ZAywI079Au6WwNyXsHHZMgfHQ8Ryy0HtgQVwKm4tX5rChPw/7uQEYxmgw8OBssfzT09niHX/nR79ZH/e7eb3aqYQcN688i1nj8KUre28YDqrvPb+1/tBoNNCaVAZhqW+wGX6mnkUnbCEiIt/EI/aP41EARfCRH08CL4BnO7Kt4rkkkNLjtDMOm7Iojee20zUKbUcSaQzcH4GgSQ2M0vcoY97y1EsHDxmjnwWwPG1RxFNp0KPKoLadAuERx+4HtNH3DgflCiYVGLCCjeMWfaouGXXaRjxvb7twaO+RD80IoWIonL3hBnoOKx0lj40zsiumZNjW9iep/prkMsTgvZfXSqEqCsfAI/NF/T4Qdl946eXlcb+r17qdSoMeTEoqG1etjQcXtNb3aq2GACJrkDfqaSySdTKJ1zsMnL39Ue5Te4fliAXi4fqwIoYSGemU/j+S88dgTGbMETuvdrNwhPCdQBK5DrkDrZRZ1M0763kzU0p99NL21rXjflevdTtVBi3D58c/d63UWt89HFZ3FUUxMVorAMlgQov02yF5Ufr0KM+M3LPisIZ/VXh0VJNjJ7M7YofcmIEjtuinw0SDDl8lUZW/c1JKMXCJGW8uC3NxMhp86drLt9ojD31C26kyaGmzupto5d4+Go8eGg0HVBY6RP2SpR3Gjd6PURrTIw2WAhkZsl2FGsGKIqLNMk/CCZGcOaeNGIiRQrkOYkhOjOg4CAqkED19osApTm4zVO8TBZiC2MpfoFKAMQqMoqrK8r69g/kX6ra9ilNk0KeK5fjhH/6Z4JWw6Rx/wFl+e2m0Virxu8kAxZtlYeoVSWik0dInEETL+eZMCXPnSqTVxn3PLb4zV+Z5SjHfrt/xXHZoz4C4EOnMdSBJ8hqvCYi6D01qva7b91y5dvORm7f2TxXjcaoM+p/8kw8CAEpjNoxS7yDwG7RSuhfZO0oOmn3Qp/GQCe3TDonxzUPblJt5dpAESyJ/HL10ynbpGTWvXAmvHiMdFxmsSL+uyF4pARzlf15r2u4PLZb1o3XTmMXe/Lhf3WvWThXkaGrr39ZoNOpsOyyMCbl59Ir4OQepMgHMtRKUYehcWMTRM2fqt3gM7nvweBLuCZeYsAItAFIE4nC1PUXeYSRNRB5bMId9GDqMRl4I5VkYGaFcjCxiYK19uLP2vsqXWjg17VTdzK29Hbp+8/qkMPqcMaosC397hzwz0gSy36iHjVfo5TRt7DniMDH7arPAldbnqcMUVCBCAO+84vNzjXSa7GXIPZHV/TuII0HsTBrARBFtbYzHk8FkOIOPD534dqogx2w+o+lscdk6e19VFZUp9GHsjNzXHcIcCedmaVPIcC6Q4Vjh1FZaH0IcDrPnibar5xdv7TJ6Lj+GfMyO0x/4641jAOfGH353IYWLPRfua4qYYVGUF/Z29qvjfnevVTtVBr0/n6uDxfy+ZdM8Uhg9Ko3BK0ky/L+5lmJ1QzGoBEPStpkgSSxsxSjz4x5isqNuI4XThWM56iiUlTWIuF6FzyQ6SAgquwRrAHjRExGU8nppgVNaE7SmjWXX3vf8jVtrx/3uXqt2qgzaOqc7ax9ou+5RpWistcYrRXWPDvfyod945Zdcc7Gyhd+shxHiyQ6f/5VPe+gK+pKm8LOi/nEzjbVMPNO9ImJpCpBEKQVFdGFZt4/sTeenRkt6qgzaGKWUogfY8VuZMZIsD2mHhv2o+MmGdRZxjx+mGVK+IGcmjmASchYDh4+ZNlsJhGTQxLEDOycKJq/FyOEG+l0oP7bUAXFO4JFMDr3yzkVMLmlbGsy4tFw2b58v6vPH/e5eq3ZqDLrebzAelsYYvam02iLC0fwqvQI2QM5BZH/HCRgifdYLM2dctj/+V7vSbNbJ6O8fXOlqYDtNDhMDEyWwGQxP0ISyw+WfcSxY45kP3m677pGu7bYPddAT2k4VyzEaVFXdWFMYnUGKr4STfctFP+JZSWWSUdlqhfsFMhuPx6AwoUvMNFEwlhjZS546kSUUwukAh+wYFTUjkhwQjimTxhXSXIHA5OkKin2EAJUCLST42xEc89A5dzcznxoMfWoMuiwKXZpyXJi61EpnmSGchbEz1UZmnBkzHD6DH/J77NdK9APJg/dUdbRyKOGX5Vy94Eo6XN875lCmD8gd5zXzwmcudY8swp4Jr7IAToAlzmcGExGMUqqEH61PPHV3agz66u7N0jFvGK0rrVUi3DLHCCT7PDS49irCIG0c+d2+RzxE/a3smMcWk3dGDIvnZpp3jH59j6z8gfy+ClOyz2PL5ou9gjn9aA9CUUjWWhW7s7oAqDnq0ZykdmoM+sbB/oAdb2ujhlqrJPzhBAuioazkCnrarM8YRPwajHG1xnM0wIBVONuAOHnGuE/O7kkcJIPOrALkEN9KyXAThJFL9rjYhRsUqCFXxwCUpqgLybupEjmspsB6KFLKjOaLZqyU6uBL857YdmoMell3Q0V0SSs10UqhZ1KhNJHHoasyOWnB8oNhOvhwsrjTXuA8E+9znuiXJU9FL9xjMtA/RjahW52Q+VB1P0iT987e1tJBHAdFHvpeGelaHIuRExQRFIG0ovFiPl9TRFOcGfQ3RmsbO9Fa3V1UZs17aDHozNOCoChNs0hmg9mka3XClg//0lZgcqTW/Hd0KKqXyzsjsskwd+o33PPM6DEPGf4+kkIXAz4i3B0O4SBRztSTlCKliNaWi3qTCNeP+z1+re30GHTbrrHT96Eym95DC0MhQ3ieppSgQo+iCxAiT7+KU7pXYvtyMEy5PDUPnGdwIZddUH6O3KsnrTOtQBtKW0eqro+n0+dK+XC3lA9TIbrohMnxARYiRRt1024COPFS0lNj0F3brYH5XmbeUDGKRggkVtowDsE54xE+k8lfT1Dq/yY+7BZ7SCB+wHE0eKXGqztJUCb+nEyWsls4KhMmD7rI79JWQ+6kCHAc6n94gyZFipm3mrY9h1NgDyf+BqR1tpuAcLdjXicKy0agP1xnZG5G12UvPWZ1JyVej6CIBF+SfCY6LbuYzM1GOCHeOI8asosYOUYus2169e9CwMVl7r1f4DFBmngPRzwnJzg6dihSjnmr69rzOAX2cOJvQFrb2SFAF5hRep2DfEMrEb7DvlMcKq18mLN2hwm6ZMwi5zx0kFXhktiiHC/HH1mLVUvD7zLi9DQaGcuYS08p/ysAdqVUpuDL9ycoImWt226cPY9TADlOfOhbJj7WurJzdszMSuWrVHHyuqsZ08CRwb/4+yrvnP6shLsjB8eHD9rbf2UpCr9xv1rS4dwvHOqCq1wycozeny9EebSMSlnaCwFQBOWc2247e6FtrZFnelLbqfHQDiDnmFJ+H62wBEBkCgQ6EPkslBg74eTMI+RwPf44OuPwO7IJJAVDcUmyH2FGhBucfkd+GLlCRkathf2ySGAufpJ6qTm3LQGg5M193iEHgZK/PheqrjLYsbLWnm+77hKAAie8nRaDJmbWnXUxvN2jFgRDi3Y4lCbK4QcJ4xVhQXYcOUqsZB5+Pwq+yBeyXZqtRRyRO9ieXCQ7iKRPpa7h+vj7iIBeRDCM2CHyL4kzDI4IOcg5N+6s3aJTADlOg0ETAM3MWoqr9CZ0ubiNkzY4ZyjiUfLtcu+XtR4Fl1lmz3ZjZ0ifemOjsDoAep0igpX+QSBLuykFOPZSixg1fIVqS/n6iZFbVwrEgCIH12V8vCKwJnLM2lo3VERnBv0N0AhAoZUuOitBLo513RgERbmt9OvT5Q4092j5/KsXXOTcTrMpXiZYSp3C9fxoz1bRp9zishMBCgChnkaMRMqt5tfI/WNl3ll2ckFXHVkWZB2dI09N1jqtjPmq4tdv9HZaDLo0RhfW2pzoim+We+yDZFQnz5lwcYIK/eBJFtImr9VYsec+spCtc/ze0zmjzzpkSioX/o3Xz8nTUrzeAIoEK6ucRszPkSbNDEQNSxql/DVIUoBSSp3kCSFwegy6MlqVdVg5nhle0xBFPt7R9dbR7tta37AzsiIPqKwWRTyEUyGUG6OHd8IOUe+MZGzhKuO2CmLUGeOBMOGMN0w4yu56lUkdi5ou6rEdQt5hxo9nD5HKwpx4ezjxNwBPPQ6VVoM+uZZwdLSkTO0bNRFHQQsnHWIlmNLjptPPkH+PoutWuGMEg11NnwonSf/mYqdVPYdcdNxfmI0+PApyLC9yykalmK610heL0hgAVB8xTz0p7TQYNAEYaqMH3gnKhIgSW6CCACnzSom6Qxb7oGgwwoQ4YU2ov/SatD4GRxZtDLRbEONTkMGt5hkmT80Zh8wZrMizXcI3rt9RDnUMeSrw2FxWoCUACKUPXA5F/KGUKYoSgGqYT6zi7jQYtAYwNloPIaE6SsYc4sUr2SdYHW6TJBQZpHUJE0f6LI/6cWJUYkmYbMLVt/0MMoR9RDQk5XkTbu7DG/k41rKmsFCQdJYYlUnnoTjE+AcQ7015nl5xSJgFA8RQilRZmgGAgrvO4YR66ZNv0AzF4InRagQwpeyNXE6Zm+SKUGnVwCNPnA3noJ6x55LPXiaMnFcOlVNo8XjUZ02QyUlzoRGHUrssRhuMvsevywHiCVefTY/ZE6aDiFJSQIpQ6tLoIYASna2P+7X+ftuJN2jHTjFjTZOaEIikHEAyZAZYBRcXKyX3AjB5GNp/lEfkOFlx3CppqPNhnyHCpaxa0gpM6dfYY8SKRyEi2eOSM6zuHa1gBzpk1AmapP0lwtjLJwweOx4nUjpkSm3WAAzI8sFxv9ffbzsNWg7N7Na1VhOi/H5W3FNWkG4VCcQStD0jPYKSlf7hObD8IpLRrNB1EeoesRJAFDMdFUHML4FDRY3eIbIAC/LzChY/WtehKGdJvHDJf0KmLMwGgLFSJ5eOPvEeurNWBw30OvmW8vwC/Ijp/ymujeiNhXEAA1ARgkukL/ndw5pqSSJ4ha6SwiByTkr9KvW1FazTEykhzQV8ra94QPk6hm56c4JA2YWBiaVEWBD3uzAyeAMPdCFRqY065xxPOA9xnrB24g16WTeaGZsA1kn5ahocJ1WJ8RB2gEhKz+aG6BvDr8QqJgz5Phv+j2xitSRlbPvBC4+vk9BoVfiU6DikgudgXwwGHndHitGlrsOh0PlqZLDvvVOnE6bGsTfkjOEAKaoIdLHtuo22PbEkx8k36Bu+Av22tXZjOKioMCtyBGEveHVp41QyK58RrppsYjI4i9qt8sOHGY3Dvwu2Rjxf/LkHN46KmMiNcDRoElhwyEEnIVYqNtO/H0Qq00OOotBgx4P5or77+o3d7aZtTyzmOPEG/eLVGwbAtlK0uTkZq9Gg8t4ni8LFhFMxbEoUXISwnOXt5TaeRwfRJ0b61fk5aY9Xd0DuDV2Ut0aBEYnnDZ0nzvm81xcevRcEkrsLhs3ORbpPMPAqi9IriBNGgMIojIYV2rYb7R1MH5jO5xf56GSXE9FOrEGL57z28o4B4dzW+mR968IalUUR17oWbUT+IjkMy4FQiMfKHaPXNeVDu+zpm81Ce71jYNXJ5hNFJLwtOLgnb43APMKICFlcmqzKdlY6gOyErLMxkqovnE9WmpVjW8dR1FQaja7rqps7+/e3nb1gjD4z6ONq0/lSAVgbD4fDsiygtYrRPQY8hRdwZC64743HK5M0jzEB4Z9zaBA3Q8DjecaheONewCQxIHmnkqFBdBW555V1BgVDi7YjdSxOYXw6KgjDcM7FGtJyDdKRI5YPBw2r3hWz+fJC3bSb9955QZ3UFWZPvEEXRUHMbLRWURiUeyfKDDZO96gPN4DDwRQv5An8hrAFAmNUqubJweVSdozkbRO08N+7TA/dZ05UJBxXhFNIEziQTPoS1OjptjMKL/LLAUIppfznkgQRbj6WHwvQRmttLl/YrACcyODKiTfosjTKWkdKUVyw3TlOFe9zii787YflFPvrI44UafGExEporhd6yyaGPW1zNhyETZMePxlbT6PB2TEyXlu+6yN5ysRSeTi+n+rlQKBMgXRoNS9GtuKs7zhVaYaT0XALwAJAe9zv9z+0nViDtkHMX2hNHCJozlk4K+FhjlQVkYpDeZSJuv4kLhp1wN893Bwll8H3hRpdMTuGUx5ghA4Bs8pFkCIcptg4BkCkKmjOszjnktCpJ6PzXUcERj6rO2lDEhWYaLx+YR3fKRwzrHUplA+gMGaitb4A4CbODPrr165fD8tUEysGaLXgSj5hC+TGoQxvv6xaNkEMBungPw/y6ujRkf3cZwz60XHJEFE9FiRsF6J4SW+ShEWpLl2agvbrXEue4cqNwC9HoVQGr4JXp1jNKWH82DkFngGpsxJp7Zd6O3kAGifYoPf2GgBA1znySy708XBCmJyPyPJTNMi8IHLklx2H6Fo6HlaOEeFD/nvgfnm1BxFn15TweH49RJythegyrhjJ42ZXn+AO5zfm92GGCEAp9B6Rz+U0pWMXJ72i/XDOdUS6wQmtFX1iDXp39wIAoK6ds856CJJAbKK/wN71RSPyrzWWAnMZ6apW0qSALCk1RQFxaKv+JJAD7eeY4iSR1GpNjtV/5RDKB2ESBkpCKiBbQyV53FTwPE0u4/0xYG26Puc8zLDO+v0cwMTonIO1Dg3bpVJmHycQbgAn2KBnszEAoO06y+w6l615HU0sDKlKcW9amAcpRDdH+SxOcHagz0B+uQdkx8gNu89ucY+bjgGTbHlj+Ve45t7eKwxJjA5Gei4OA9kZV47RjxvG5Su8RDpiERHb+nMGuN9ZW1vHBwC6437Hv592YtV2WiLc5DpStM9A03UdW2d7LIHIJnsZKnmCqeTdZU8ikl8SjIhRPGTr/UkmStJtyBqB/dxFDhO2owxYAii5HLRvvPEeIFg/1HVWaY4g169UCuzkOZL+7n2xmZjoqyTfUu6PYIx2StFyOp+e2JVlT6yHlra+NlwCeLIszBvni+YNBCqqqoBz6e06MGApcbW9tY1lcpQmgZyxBYKVPanCqUMEUBoNLgtExJIE8QzZMZHpMOL5e5OynpZZ9odom+EXoM87IIizawhQKa6Sxdl1Olj5nMI5LKNtHZiZ10aDOQOL3f2DEwk3gBNs0B/4gDeKi+c3lmB8rq67N09ni/u0pqIsTZ+8jZMqWtHG93GtZIpnUeg06Yu4/LBeQ8LpaWKXQwekjiGBjhxVIBkgIExHmrRGhiKdLIg7MxqOUyfw8ua+Vju71GzU4Niv67aFY15sTEbPlKW5uljW9iRGCYETbNDS7rh8oWbmp5555soz09ncDgehPFtGgaUlhFOTSkaceVmEyZxACABZGHvFiuM2ubUCMTIY8wa9YlkdkWWSeL5kbPJxTJEKXHJcZi5GAxGinf2SBNKPFQURFlGolhSeg1Yg5xI3qRTqtgU73llfG//WxXObTy3rZhWWn5h24g36wvmthpmf/+IXX3ips842bYe6aVGWRcy09o3A7IIB9IMc0Zu6PCSXS0TzkDKQwt4p9pc8KmXbZJxyZuAJH6+kaQkjkVHPsa9ETXQ/uphDCk9Dcq+Gh7/XFO6OAiUwOuvQtF0YnWh/UJWfvnh+69nFsj4z6ONqk7K0AG6SUreqqnRt5zCb19BKwxhK2R6RLfDYQjAmgODp0iQSQMyaTso4ilE3RQIz+vOm3Mt6Ly0cGkUM6xxD6aDscP1O4XfnVLE/ZqikDURspZBgRs6Fs+OYxaKykgpyGOdc6DSEprFYLluUhUFZmjkpfKko9DVTjM4M+riaVsoBqLc2JvO2s3Y2X2A2X2I0rGAKkwmDxHsRlEzu8loZCAqJQ9Ak89SCP1X/u6TLoKjSi/g2gyacrDaIgRDTuGKhyWzCKNctLAj3RoVskovEsZPAFaSFnokohOJlhPG4u+061G2D89sb2Fwft1rpl4lonnWjE9dOvEGH5rbWJzt10z4znc4Hy7qdWOfScCzKskhhAR7r5jWcoyNH+Nq3HFYE9iKvqpvkmSuKt5zlyII6ok3umS3lcCbsEy88wZk8yJJzIHmIPmXXJC49D3P7a/HevW07NG3nBlUx3d5Yu6oU7eNsWbdvjLa1Pr6yP5v/RtN2k7ptHxGDdlHNH/4wRV5aUYisBYuOw3IQ/AAiEOqncEhkjrI0c9nbcZpIigIwapQEbQcJKMI/vY7EqUJTL0CTzfwSi5Kt3Y0+vLDOsxhhdYMwOWVYqZrkHLquQ9N2HTO+tLY2+jSB5sf9Hr/WdmIDK9KEUZiMB1fLsvzEdL64UtctnHXp+7yIEDyOJuI06fIbZhHCNFEUNVz+XS8zvLe/1E/i3kiQ/o4bx2hdRCai6Avn6Nedy5mToLGWe8tpxpXrdOG6SCHmEObSAAeHpm7axbL+7HBQ/fZwWM1OKl0n7dR46OFwuMv788fni/qGUQq2c3DW+ZcpMCAwCD6ilr04GaUzTpoj4+GhSS/JFtTzqoK/exoLCtCC+6o/F/juvGC5wO68tofg8rQ+oTfIKDldrZ2RnTuG1SEjR6pCCnYeOlGs32EPpvMnRoPqswCWwCpFebLaqTFoAPWtW/vXCmNmpdGo2xbLukZRGGite7jTSZpUxoTl5QHAgA2cNJC8dPSEnGCHEBFuFTQjjQg51o661aB2o+DZrUMPVhABbAEXRhKVUX1ybPlZKRXqPLuEm2Wy6zjmHyI8A+sYTddBK4XNjTErwg0A13BCBUl5O00G7a5cuTYbD6srRquX2q47t2za0oSyBolNRpyYgRE1xHESFX6gHI5keFeOFb15bwm5LLq3QmknLTL3jnFk41eGKznUybNlBOxEiRUn9ibn/rzwkNE0LYhouj4ZPaO1uoYTmnK12k6TQWM0qrrRsHyiae0n66Z9X9t2ZY+Hy0PhMZgSjCYMyRJE86xeL0jeM1zByCLTTEm1gGTQkDpiiqISvy3FF2XhW0kIsBYhE6Wf/+h3z8Pa4R8WKBW+y3QgpPxf4q0FTjRth8LoK+uT8W+WZfHicb+716qd+EmhNCLCcFDa7c21zymtPrGom4Nl04YZvg9iWNECW5s+s9Z/xq7n8eLEyrmoQfb7ONiwRJoEV2z2WXT3/kB+f+siU+Gsg7MWztkYtbPWb5OnXOXi/97+To7h4pls0DJHfbNLdR3BvoM5eQ6W0bUOi2WN+aJ+bjgafHhrY/Liah28k9pOlYfe3Fh3ly9sPfvcSzc+N5sv58ZodJ2FCovZx4IzKbgWJmRh/etcEx0gheihtWSCZNRZ2CyKjSDCoExvIYaoWTxzFqFMR8i4cf9ZLCUWOhWgohKvvw8SxlllqNkroaxlpIWIHGxn0baW66a9UlTFpx+6/+5bx/3uXqt2ajw0AEzGQ1dVxcH1l3evHUzn7XLZoOvEQ7rAOys/lCPBCqVUnPT5+s2HazgjLIOmSEGRihE+r01WsdP4IogKBJXtnImJ4vn8o6d8f6Lss7BfHhoPDI3XZCdvqrSCUjrpqokD1BAdtsT0HRwcmBwrRUtneeelqzdv4BRMBqWdKg9916XzuLW719VNe8to/aQidbFp2gtakyqMBkj1lZVATMMSxkI8cwQPwaCcS0Vl8nUQ5Ui+ECSCESVLFs/I7CK9F7UlYTOl+iULUhg7hyAhSxwcmRHhGvOa1FID24WlKGI2OTswHOq6RdvZaVWWn9ZKf/75568tcIJD3avtVBk0AJzb2sRP//yH9wB8xBh1fr6st7VWSisFhvPejfr0lwsZtqQzXUUWXfTYFxA+V0UtR/8YPmKXwtt5E8MWj9wvA5Y6gQrlDvLlKuQkApUUAaT6Sy/7OYLzuY8xOsgBT7sg7neYL2rUdbuzvjb65Y210SesdSdW+3xUO1WQQ9ql7e39c5sbH7PWfX42X7i28+lxeQ07KZMlTaJzHCgL0ul70Wj4gEjYn/IMlVyp5/fTEYYEfXKAGkm3kbEYQIbrKVQw8n/yNKsITQJVqJSQJv2UM5KOJ1FSiUoSoWk7TOeLRd00n93emDyztTE+0dqN1XaqDFqM49u++dHFw3ff89R0tnhuNl92bWeTJ5OhXoRKmbrfD8/pWFIuKx074/16EEGO1eeWe4yhsAg5CSJHSxcU+fE4QaREyx1K3YKMDkn/IRBDuHRCgjAOzI553nX26t7+/PnpfLn3xvsvnxq4AZxCyAEApOGUUvs7+/s7ZWGmbdeNrfVGrRlZGHuFsQgYlBBgBfV1TTE6uAIL5BiehgteXaSh/tse7aZCqpcvLxBj1J7TFmMEBd10OoEs0SbSU2flGkJ+YKAOpdNKrT9mRmstuq5zRqnnB2X1aSLsAZBCjaemna67CW1vr+FFXVtjzDNlWfx769zVxbKBzfjc1ebVc7kRIhoWsklX3hEysXOy+ky4JJJr6tF46eASUs/PmYuhJPIXoUnsNCEimeuNMl13Lkll+A5kuw7zee2Y+TOTcfXh0aDa+UPv+ibs7p94gV2vnUoPvXmxAgD861/56BeZ+Ze6pr3rYLq4vLE2gtEqaigkMidBkp5AP7RUTUk4Z4ZzFEoa+G2ZfPAiLzbu9w2iJfSNWdK6EmXtvbWHuipLweKE3+N+CbMHNWzc3IGhAn62OaQC0HWWp7PFUmv1mbe99Z6Pbm6MDgDg8uXLx/26XtN2Kg1a2ng8utoul5+6cePWjUFZYjQsYYyO1UmV8pM3AL0wcqzXkYmB/CbBkFwmTe3D2l4NEMTaz5I76P+SDHGZAEZ4zgiZJaHzKB+GTyUNEr1nbai1gUzpF7y2Yx85FLqw7SyWddNN54ubzvFL99977sb22uUTWUjmq7VTbdCLxXJBtn2xaboXtVa7TdutGWO0MTqo5Ch65jyp1TF7LLZSfrY/mVtVOGfBmLAwkCx0mcMM9I6bH7MfzPHwIUQXj4hO5gkJqbMkPbZzLuL+5bJB29qXmfHRpuuefvGl3bZpThW5EdupNmgAmC7qxXg8eNwY/cSybr/JaD0uChPprzjpi+uSuMQqUFZYBuiVNFjlbtOKVeGDzHZzas6xLxTTlzNn1ZbyMqjs1whXIeLj2QyXzhcmt459tVNfmN1PDjlISbvOYjZfonPuC3dePv8vB4Pq8eN+J69nO5WTQmk/9IffA6NVvbUx+bgC/eb+wWw+X9aBLXBgL0L2QQcR74gIj30ak80+i41kqYgsbculLO7kJcNnedUkAOJzE3ZHlHvK9r4DiTjKHZrISjAmTzWz1qHrvNjKRwot6rbFwWzh9g9m10bDwWN/+DveffNtb3oEd5y/+7hfz+vSTrVBA8BbHrin+973vuMxZ90nFst6t64b17VdfPHIuNtUtDwsUCneLwWtk0EKbZcloLoVBiWW9MrYuQiX84gkEEeAfD2WuL9L9fXyYyeVnffIXjmYOlbTdljWTVM37XOzRf3FZ56/8vKTX3j21Og2jmqnHnJc3Npw5WQ0s869VJbFSwzcNa/bYVkwlYWBciECR1mVfZeieMJUEPolBnpqu7iN/0QYiJjHB0RKIlGD+Vrj4fMQGRRDT9qR/FxSoIYThReOr0LGrwvy0fmiwXxR761NRv/Pxvr4V5RSi+N+H693O/UG/fxLL2NzfeyKylwtSvMbbWfXd/YO/sDm+gRGax/cYIbSeRww0WrCHMRUrb7ItOeR84pIADITR29emQUGex/kofa82lLqPMn7RmjCLlslKwVZus6i7Sw6y7sba8OPv+vtDz+2uzdrv/ktDx73K3ld26k36G9+5yNopwv8gbc8ePXWzsHPfv6pL59vO/uWQVmWg7L0dZENQ0Ov8Bbec7og+CEpSXAElk2qOVnxSqaaiJE8n5nbjy7G4IcUXVeeh45JspSgRUxGCZWPpApTDHmnWgnoPE3HzvHcKP18XXfP3tw52AlFeU51O/UGDQDl2gjMvHjh6vUvPvfCtWc663Y6a8/Nl0szGQ1TZaMQ5suZiR5jJ/Se6CuYM8YjFVXPI30RgnBf5xw9NPVFUBFqZDWowS4cPUGQpB9JwRcOVcuXTYOd/SkpUr+9sTb5V0brZ5nZPfn0C8f9Kl73duoNWozl1t6eu/vyxYPtrfUnm7b77Vu7B99irT0/GJQwUElvnC1WmTRIMnmTIIhkrxxN4cVscvSmcR4rx5ocCDl+SRuCCEUku0Rq1yWmJcpaFaXoZTiDY0bbdFjWrW27bmaM+fjDD979b++/+44bW5sjMDP+9HG/kNe5nXqDzts//Ze/gEcffujjL9/YK3Z2Dy4NyuL82mQEBYLWCoUxvdrNqfYGZfpkilWVAEm/ksU+Q70OxzHRVppAj6M6QBI6cdRqRwYmGHNc2hgu1usL9Rfg4KFI3bTYO5ij6+z8wvbGU2VhnpqMhy9tbgyb4372X6922xj0uc1NLNoFBmZw7f/78Kc+OR4OfhfAnTu7B5e6iTVrkxGUctAqK4LYi/BlGo3w/aroKH0uH8QekcLb+ZFSra+k00i7hK8ok5TKh2EimFw6mqbDYtmCGSiK4vr6ZPSLVWk+9dgTzy4no1E43ekR8r9SO/U8dN52bywBgAejcuctb7r/t7Y21z65P50v96dz1E2Lztq41Bn1XXQmrg+5gMjSqUKLGjzKqECpfBTyAJVKZQkIFOrPZZrlvMB6ECqJrFUpQFHSPQvHba3DYlFjNq+5qqrFxtrk82uT0c901j32gfc+ijsubR73o/+6tdvGQ+dtNKymxpgPH8zm5y/wxvuWy3Zy89Y+zm2tgYbJ6BSplNXNQQrEvt6GH+1FnBwOzCnKl08WpbHz8k8JuUfWhDlL2aKI3ZOe2cnhfTmC4J0lMlg3LXYOZjiYLhaT8fBXL1/c/rmNtdHzzzz3YndkbZBT3G6ru73jji0QEb7vz/4P3WKx/PK5rbVP3nnp3GOjYbXTtC0Wixr1soHtbDCcuDChNyzLMZoXKxPFlBVhNLI/K+eP0UGXFHXesNHzuhLudlKHLnrvFBmUdc2XTYPdgxmatmuKUr9UlPpD73rbw79+950XZ9/97e8G21MdGDzUbksP/cHveg8A4MF77/yyte5feadJ37Zc+rnTplnzkzwXVpxCbsgEDtkosrSahL6xMmGMtB4yET4EkXNcR4VVqJYEX+I3JuaGfqKEpnOpvgbYF5hZ1A129g6wubF284H77vjMZDT8DIArStGplId+tXZbGvSP//2/IiHklwH85nS2eHdhDJ744rOYzhYojMGYBkBhwCCQCyFnoe2si4yGgopyT4pFGP154srGzH2I4ShxzoEijMtTqKAhcZw6i3XxM6muZK3F3nSOxbLB5sYatrfWHr/z0vn/dzisvlg3XTNf1hiUxXE/6q97uy0NOpvtz5Z186VLF7afA9HsiS8+NziYzXVZlWACxqOB99DkC8xQKD8g4W8iAnQItEjUL6j0RMvRS8yFlA9L2eJSEzpfb8UGyKGVipFCMWZnvWB/UTe4fmMPZWHwyMP3ua3Ntccvn9/6FWP0tUF1+xmytNvSoPOmlFoOB+Zzo0H1kc2NyR+czZfbt3b34NgCYIyGJQpjfAEXtvBgQ2c8teuL+0MaNgNw2eqYBEQIkYovUqLf5HhZSYLIXSOxiK112J/OcXP3AC/f3MXlC1u4+47zzaUL23sba+ObRLcn1JB2Wxt0gB0OwONKqY+MBoOHhsNqe382w+7uFGBGZ8eYjAYoizKKSMVrg9h7bpLCNByZDo+SU1aIpEk5F1bRolBQMa4kkK+FEopBRgjjvXRdt9ifzjGdLVA3DZqmQdt1zaAqX9pYG9+sm7bNV7S9HdttbdChMYBn9/anv2cd75VFgaoosKwb3Lhp0bQWXeewsdZfUFOUdMYAIApLYDB6TF0MTROUVkGwz3FRUGstpAxuFxIMekxJgBrWeW3zdLbAjZt7fgmO4RAH1QJ10033DmZP1k1zZTpbcFVuHPfzPNZ2ZtDe5vZf3tl/qbW21kZjMh5iMhr47GnnsHcwQ9O0GI9HGA0qb7yZuEi0GOIYhVOOIWo5Czh68wgpsrVBKXhtqUUHRqh0tMSybrCsW5AiDKoCw6rEZDRAURRt3ba3Fk0zndc1zt/G3hk4M2hp9tbuwbztOqsUYTIeYjSooBVhZ2+K6XyBnWXjF353jKow0FnUUGlfOTSUxovLtkk+IlhK4mbQQig4izRhlJID1qH1yxVjvqyxP52jbT00Hg0HGA1KFEZhMh5CG8PWObtY1q5ubmv4DODMoGOrl4111rEiQlGVGFQFtFbY4DGIgP2DBW7u7GF3b4q18RCT6K2tZz+UgjE+odVZr6GG0z59in3oXCi4vA5dnoMoqwjUywZ7B3NMZzO0nYXWGoOqRFkUUUSllcJwMIApjHaOh/P5smya2yuIclQ7M2h4aPCTP/shOGaUhcFwUKCqilglVCg6mgJ122FZt+jcFLPFElVhUBYFyqoEw8AYFYvOwFq/YI8DtBbmQuplpNrN1vk1t9uug7X++HXtVx8ojA5euUJRGDCAwmgYreHA0FoN2PGd83m9tVieimVSvqZ2ZtChWfaZIIOKMBpWKI2JGjs9IQwqg8lkiNmiwWJR42A2R910GA0rTIZDjEIyqy1C5gsBZAEXIIXWWQndwFx0VhbAtJgtlpjOF5gvlmF5jQpbm2sYDypUpYk16BwYVVmgLApJghk56x5cLttLhSkUTvhKsF9ru+0Netk0qNsG//fPfIgdMwNpaLfWhVC2AZGCdQpghUFZoCoLLJZNyK5uMV/UAHxyrV9KLlT6D4o7X7cjLLHGjM5aNG0bipgDkjywNhqhKDTKskBVlNDagEj7YxoPW4rCoDAFmtbCdk53nd0C2sloVKnDOY63V7ttDFpe9GLe4mA2w3Qxx8F0jmFVgZk3Hnn43gee/NLzIwLBaA2tNQAbmAeCdQpF4Y1Ea8JoUHpo0LRYLGu03RJN04KZoWsFpXWUkKqAWyR8DXjKrm1bEBEKo1FVJUbDCqPBwK+rGChCTQpaa5jCoCg1iAnG+GMXxsC5Dm1nq6oq737jg/c8AuCpT372qfn2xgS3dvawtbneew6n3chvG4N+pcbMRefcuy9f2PoTV67dvEMHgVFRaJhCwzkL5xw666C08kq8oIQrCoWyGmBtbYBtO4G1Dm3bYbFo0XWuL1wCYGLRcopa6bLUqCpfyUkrBa1VMHry2LzwuNwY7b1+0GUDQFFodNbz5KPh8Fu0Un8ewD+7fnP3d4dVgc31yXE/3q97O1XdVbzw7nSKeb3E/sES04MFZgdz3No5wK997NP4sb/7FzWA9StXb1y+ubN/72y+fHA4LN9Tt917Xrx6495Cm9GdF7dQlIXXXVgbRUVta9F2vkhN27boOtsvfUs+QDKb1bCd9R0gyD3jAvMI1fzJG3BRaBQBd1MoHilefDgoYQoDRQpGh5JgUkQS/nrmixoHsxrnt9YXd91x/tmmbX+l6+wntjcmT1++eO45ANf/wl//B+0f/6Pvw8baGGuTITbWx9hYG2FjzRv8afLaJ/ZOrlxhVAaYtzNYt8Ct3T089cwL+JM/8O1YtDXtHkxpb3+hptOFme3Pi6btTFGYantzfb2qinuY3TsWy/pbF4v6vXXbrtdNa5q2U+PRkC5sr0NrDee8xxWWo+2EibC+8lLn0IU1Cpm9mIiIIPSZMQZd8OhFoX2n6GzMUwQoLlWhyLMXRWG8NkQRqrLwEUYGjPYdwEpGS6i6u1g0uLl7AGMMr6+NXFUWbVUWXx4Nyw8ZrT/StPazL9/auzWdLRbrk3G7Nh50Gxtju7WxZiejIb/x/X8GP/FjfwPbm2NMRkNcPr+Fg9kCGxsnM+J4qiDHxXOb+Olf+DD+1A/+98z8qfGyvnZpNls+wMzfVNftgzd3D7au3tgZDQblZDIaXBhUxZ1G6wsjU2E8qkCkUBYGZWEgBVukx8fJnlKwzqHTHTptUTJiHTkE3bKORSCltrSCX4XLG7lUD3WWobT30h5ueDrOLx+HgOMRyu/69VJ0WMlLvLxSGspoOOeIiHTbdbpu2gdv3NotD6aLPzBfNjfLwixHw8FLYH5cK/35jbXxM5PR8Pp/+7f/cftjf/e/Oe7X9pq2E+GhBUrc2jvAclnj+o1d7O3P8PQLz+M/+5EP0sG0HXzpuec3dnYPtvcOZusMrK2Nh5vDYXWXVuqNtu3e2TTtm5ZNu+GNyrMIg7LAYFAGXldBKx1L0VrrPbCsz6J1VN4D8MVcOmujQs6GtRBdMFSJBHbWwxUTook+tStkdncOxmgUpUnrHWrhviV5IAiasvUUlfJZ6hQW4ySFmI7VCY5fNljWDTrrUBQGVWFuDKry00qpT7dd9+Tu/vxq27a742E13Vgf3brj0ubOvXfeOf3P//o/sD/yPe/F1voE57c3ocjh/Dphb8a45557jtsUvmo7sQataISLmxd0y/XE8fKem7t7b9+fzr5172D2aNN0l4rC6NGgLMejQTWoilFVmKooC10EhkDqKSslaVEOTIgTu5jqFKSg8YEF7yjLLGvtjbNrXeSZ27ZLJbskPxCpNIIx3hBtx9DaT/hknUNPzSET+PfPDRCMUSiMArM38rIMi24yBb6aYiKAc55WbNquq9t2sazrxWxe19NZ3RqtDjbWhs+vTYa/ubU5/thkOHzq4vbGraefv9ru7M34zKBfwzY9OEBZKDz70g529ud46dpN/J3/8yfwqX/zD9c++/jT997c2X/zzv7sTmv5wsb6cHs0rB4wWr/JOr4HQGlCiLgotIcRpfEhYwlQ2FRGq7MdbOcA8uJ6j3tTbh/gE2PBaV2UvNazY0bX2pjVLZ0BkEr7HCWn0iHkGLI0RhfC5cZor/3IchnzFQcAD2lUMFylCIXxK9MSKLAhOh6XGWjaNtS585Patu3QBN2HVrQDwhN1235hd3/+krP2xqAqrm1trD3+8H13P3Pu3MbNn/6Fj+DOixvY2BjhrrvPw3WMC5ubx20iR7ZvCIMWDe/ewT4WdYOr13bwF//WP8FH/tXfo2eef8nc2JkOrt/YGZSF2bhwbuNu29l3LZb1dx/Mlm9tu+7CcFDSeDSgtfFQjYYDDKqStCZwkF6Gs/QSWNNSaAFeSLgaSVgvi9uDCFppxLJeUsQx1pJ2IQgTcgrFGOH5ZucAYyh60X6VMX+wrvMBPmN0ZEM8B+5igEdrFd19rIwaiqdL0q3n0FUslC7Lasj+kgdJ8GsWzhc1zxdLns6XbjpfgoD9QVU8PR4Ofrkqy9+6tXvwdNO2O5PxaLm5NVk8+vD9HU2+3f3Wh/8RLl/cxmhQ4fLFc/hG0WF/w04K/9Kf/X4A0IXRdwN4l3Xu3bd2D97atN14fTI6NxpWd6xPxhtaK621gjYKJkysZMLlva1LSafWRWVbXGk1ZmhzNrxzSJ9CrOss4WoxDsnO7tV7cQwbZJ9Sh8NjYV+JX1R3sgCnC+ukQI4BxJFidVm3hKdd8PIqFG3knleyynpjJgWtRdrqtzeFjthcB0xflQUZo2kyGqrOOljrtjvblXXTbly/ufuB/elyvyzMF5j5U1rRxwA8809//G9+w4pGjq1LCS6+8vIu9g+muHFrF+9/718ANx8ZffaJZy7t7c/vqZv2QlEUDwyq8l2LZf3upu0eGFYlRqMK4yijNEGy6cJEzMVKQ+LdgLRcsFBw1tleOYFelSTiWNtZQtOijRZdhnQQ2YV7vIY3aFIUs8VVCJg466IxifLOHyIrwZsZNANgy3Fxoa5zYaVZFQqdC0JPo4cKS972DJoo4nOAUIQgjUAZ+dlah7ptMV8sMVvUWC5bGK2vlKX5VGe7jzVt90Xn+PpoWD3/lofvfWlr467Zv/utD+Pi9iY21ye4644L/j6OyVt/I3ho0oFC+PKXf3bthasv32ut+06Avq/t7AOd5Y3hoBxcPL85GJQF/KQuPazOWnRhWQYKhuXrWSDWuQAQ05h8XivFIIWHBb5akvDIscgLEJd+S6W+ZK1tAquAd4Nn9jg5yyMkgFVWMZQ4Tgz90K9ib+rCdZqsSHqEJjqVS5D9SWCQ8gYteF+iiYhwKC1u30UOHABraOU7h2ICLAVo5RMIBlWJrU3vFJq2uzibL79jsbv8lrbtpqbQzxPwizdu7f3qU09/7pkXrt44MFp7GWG/aNnX35i+3ifc25/h5s097OxNce3mLr73O/9g9fQL1+9/8aXrf7BumkcJuDisyjdVZfkWgDaNVhgOKlRVgbLQ6eWxixOmrgsGrWR270slcoAeQD8EHdfKDBM1F1KdtJbfs+yTbNkIqYmhovehuFCP4FylUmFHFTy0/C765zyTRao0yUiiQyDFQxuKUCZmdXGWcS5YOmiw/T2oODLImuAsVAuylLBsghrvm4VB0QBUpAfbrkNdt341rc7CMc/atnts2TRPNm17vTD6sXsvX/zEw2+455mf/LlfX95/90VcOr+J89sb2Nr4+obfX1cPLS/vyrWbsJbx8q1d/NW//+P42//Vf1IqRaOqLDZ/+9NP3VOU5h1Gqx9iY97rnKu01jQeDzAeDjykCHi1zdmHsHgmOHlYAsVQtQrlulyOKeJLzbBp8IhSJlcERNGD50XOw3AtxRl9GedkWFKR0bELZ1AhO0V25x48Afw6hDHpFuEaApQQg3Tx3BwLoUdfqBiyWL0UhJREW8UeS7uVe2D40QIgkAtPLl9TMVwzEXlBFBEGVYnRYADrHJZ1Mz6Yzt/T2u49JYq2MPpj00W9/dFPPv6pjbXRs1qrvUFVzv7of/pXm1//6O/hnjsvwmiF++6+/LpPHr/ukONnfuXf43/8L//jOxh4j2P+vt296SNVZdYn4+HlzfXJoJDImTHxZTh2sM7TTtKkuIufgAF5TThpighkFGS5BicFYlRarZXIp1AJAPXe3b/sBAukKGLwvDotVyGuXBkNwbIRdBBAWkGrAHtCZxRPHrcBQRkpAhngBaURhCgbZazHPvka3b4+iKfzKHTKcGiQIhhSaZQJuF3HQA/Jo4udobMOzqbC7ZG98dAcZVlge3MNG26MzrpiWTdvm82XF/cO5nuddU8w4xed449/4hd+5ln8zb/wdbWv162rHNRzzGZL3Lixj0/83ufxJz/4XWtPffmFew6m80eMUm9SRG9n4AOKcL4oNEbDIUbDAYrwYmUS50INZD8Dt9GjpjUDkQq5cKosJIXL5YX7yJwN8k8dU5+k9K0UD5elHnrLHAf9Udd5VsOEa8y9Da9cA4CYc4hArbkYjAnQJMPl0mnyQueSq4hgmAjRRVII99DrU/GZSM4iqVSaTHC3tX4ybIyOI1Ba/jkVjBTYJdfq4YeO+m5R/1nry5HN5kvMFzW6zt0oC/NrddP+3t7B9Mn1yejxb3rTA8/961/+rek7H30IF7bWMR4OcO7C5ok0aHXjxr4xWk+M1g/vHcy+e76s/xQ7d1dZmGJrY1KNhpVWoVBFXB4tTPJsyH5W5KsROcugkInqrItG6yWeWZXPldCeDoYpxkBKRYbCU3BeYOR3zrx8eDoi9/TQJuDcgI11qJxku6zGc1ZIVCg8iSh6/UZYjzswFpKH6LhP4ckxpAwCEbJ9VKD90Ds2r+wfkUy4BukskizgbBpxbMcRuqUJKMVnYIwOzoH8KBp4caUoPtPFsrF7B/N6/2DWLpvmhfXx6KcvXdj6lbbtvtA03fTC1no3Hg7c62XQrynkYGY8c2MH9cEB/trf+Mf4h//HX167devgD01ni++YzZcPaq0fnowGDxfGFGWhMRxWfgIiFJvzmRyrVJaDQAOKcoo8nOzrNgtV51Gu4E9vEyHCZsRjrrxwraApUV9+aYr0MoVKU1q8HQUMioiftfbY3FcpRawJHdOxehBCjJ7SPWiCYu1HCaH68lFGpXuIy1pkz0A8p7yHWOk3Y1kEPkDWFw9gXCaZ2lAPmsR7CMf2I0oqVyaQT2uFIiQJD4elVopGg6pA3bSjtuv+xI2dvUcVqWeqsvj1S9sbH/3r//Cn9h57/MsYDtbw4P3brymm/pqOJMPVzZ19tF2H6y/v4IFHHlRXnn1+e7GoL7WtfYNW+geZ8YPLujlfGENbmxMMqzJgwGy11eCZu876ULFSAW5wvMo4rwlYdBUWAIDrEu8rmDBL5YvXbTMmQlwpBUbABi8qHO7qPQNJ/6EC3xyvgb2n88aXUX50+BoEp0oARbaxNnlRMf7V/WU7b1CZgRPADilyKbUV0m3GX+XZ63gPqQPZELnURh+6ByDVHGH2dKcpTMTaRnuZq1R6atqWFdQNAD8P5p83xnypqspr916+99YXnv+Su3h+G4UpcOn82tc8aXxNPbR1Djv7B2vs+I+0Tffdu/uzt40G1V3r65OtjbURifwS8Go1l6X1y8N2AVjmq7AqLZ6P02RQSmtZ0QeHl0ISG+4r1Ugic1k5WjFMsUajhanIj+9iMRkxYqEEIV4rThZlsikvJVB4DJDOjocU9l69B7lWgRp5dFE6XJ91QQ9uaaP6Sii5BkrPMVKZAMDkvTlLB0/MjzRRDgrEEIpRBgpfHKcNsEaDA72qlcb2xgSddbRcNlv70/kH58v67Wuj4WfKsvjVW3sHv2St3XstbfBrMujrN3bxxWeu4NzWOpqm3bp5a//NLz939VsAfBuReufG2vieQeWjesNBGYU7XZeKdseC4WJWMQMkYYsQQIajjLeXET+DFTJ0JgFRHxCTVCmKvFf2XZydIeYCytnkuIr6BRj7+6arUCrBAGFYZDsJvBASt5wv6xZFRYqze0jQJ7/O2C0oXUfcRqkIeWSUSivTZu4+g0NyMH8PiXWRlQtkBtpfW0Z0L4mIlPskIhhjYAwDgHHMlwpjLhHh4rKut+aLK5erqvzY5vr6E5OR2Xnq6Rdx7eWdr8mg/4N9u9zAk8+8iPOb67S7PyuJaBvgN09ni/+obbsfZeaNqiz0xvpEl2URXmyY6FmPk0UMJA/8qPCSDSW3EpYMmgt3WIF2eH+OdeFk2ePsJlIgIytQvnoMqZlBoB5NBiAGYyRkvHru/B44wIJ8OwnGePz9ygspHEn1fZVjH7oHmxiLV3dsWtnORQ3L6j3k2pJ8AhnXmZF1ZdiH5K112J/NbV03lsF7xhT/YjIe/QyAJ8B8a2tj0tzc2ec3veEu5BDo1bavyUOf21qng+niPfvT+Qd296ffXJbmrZPR8EIV0vyLkPkhM/i0lIOLUkx5MMIlx6hYpLRymCGTGo8sRN+QRwDZIZaoZU5eiV0aUv3+FDlsGSTCc09DOKfQt9BYEl2T6ZEKC2TGSRilAjL+mvo8cpocAn6N76TJlvvLo5MJvqTP5Bridat0jfnP/XP2r0lGEcBPaOW6/bYc7iEz8ZVrUDqU5WOZfCLAMX9fzBScCWICMGk/NxmPBrosjG667sJsvvye/dn8ns218acmo9Gvnd9e/8jNnf3fd/j8VRv0tWu7OL+xgf/rJ34J/8Wf+T4ioguf/+Jzjzjrfsg6991FoR+uyqIcjyoMqyokiNpeJgeyiUV6yMFyIEM6kE9i5IFlc8PshWRLqCEFAkiiBJQ6jRiowEsJKCgKdZuRhaRlqBcmYMVJEIKhK6SVYcP+Uio3GYIYbtpbDClBk/726bkc/j7/LCnp+usgpvPmHYoOPXsCAZp69yDvgUl+z48V7jNsA/hgjvDsVp6xdB7HcEQAnMRXoZRCVfo0t6Jt0XbdGxzzPda6N8wXy43PP/UcGaMfB+jlH/+pf8vdgnFzfw+XXuVKXq/an4tBU8kK4NFTX77yvXXT/td13T6iiDY210fVsKrIk+9e/dZ1vmxQAgtIoVcWr8DZxC2xAshERiq+5T56lOMKh6yVRAVlG5cWxAxlPuWlRIMBAt/NMdIWqSsIE5GzIX3GQUYIa11Io8rvIS1Dob/C/n5USLw4ZfsLN98Pj8c5dDQgWfd79R4QittEFV62f+85coJnr3QPwsf7e0gUoUykfSQ1E3llnYDDvZmsXoloWBZ1w/sHi5oZe1VZPF6VxT9644N3/huA5q4m9x9i0PrVGvR3ff934uGH3kDXXt6948VrN/5423Y/zI7fXxR6azyszHg0oMgpR3F8WvNP1nDve5s8ApHJEyhlW4BynLuyjjZnHSVv2SRHKMDcc+U8IMdfE7sgblzCyIdWj40TRpGfJm0G8ntQFK+tfw2pg3LvGaTnINWWesGdmHybrkGOwLmRQSaHFHXdXp2n4gVGJkOuIQ85ZseL6yqGDhFHQZmGZ+9C7i2fYIrhimMiUnGSKjmUWikiIkPAxDFfYPBkZ29W2c5dXd8YTn/9Y7+Gn/rnP/mq7PRVeehPfvopnNscq9mivcDg9zPw1xj8DiJSa+MhjQZlVL4Jdov64/AwRAeRR6tyk84NXLy1YEmpvyyeyh9flg7udwt5L4pEnOSiZ/KCJv+dsCyH+Q55F34fmbz6bG+b6aGTV5WOIXAFzKCAG/MJlSwOJIZlBagKxBGjDJ/l24nn7l+PS2sl8kq3oqRxdjHrRsWASO8apGtwdg/wSQl+nRfvmJQkKbCLLIbMjUSiitVriO+LYyKwKCONTv6USGFZN5gtlgzAKaLfJdDfU1AfGQ3N9Vt7M/fNb3vjV7XVV42hmW1x9cat7y8L8+fX18ZvHg0rPRiUKEQXwfm2gpdSf5GJEaLnSYafhtQAC+ILSWbWn2SRn9RhZfXV8NJz89akEwiU6JzMwCETwizvLwvBMQduOh4x804EkA8PRoWah9VJOyFGJN6O2cXRI3qyCK9CZ04kNGRBONI6QYSYBUMwSoGlsyLBs3Sd4aplfxn5CNFzEoXACdLKW6vX4LfhROHJMyT/XRwpZL3yNONMDiL7meFfv1Rplc5ReUaMmrbTy7p583Q6/+/azq4/cNe5nwTwqrJkXpVBK0XD2aJ9YDio3qe1el9ZGAxDDWXJfhbsKsYsI3uc8x2aWfnXJdRwntSZucmMxxWjyMwrGIfINaMYH+llRmYFfSFR6hxhrRP5HQkmCDyJsCCfH5KXjgpL4ngFKsVbljEg88DhKiP/SxQZAhHnc3Z+eYgCHaJZEKKumVglL7hyDcSH70m+FOGhf2NpHpAmpSIrzY4hgSuh6cJ2Fg7gBM96rxJpbhTXm2GflEHEUPDGXRYmjOjdxBj9PqXUk9NF+zGl1DMAFq+JQVvnLqDD+zfWRm8oChNKVOmQ4sQxTUlgQXwP3KeacmMCEIn/yDwg7e9F6mn2Lo3BGQWXjFqO4QLtp8KwGbOns2NEbyjHUABc8ohRhB8wdA8OyLGCm1GhhBFZ8cpJhK+I4nwi3XTC3gCgI1uTML4L3/vgDvcE/ofuIb//QEPKcz7qHtJdRgvzEUp4A02dOoMP1I9GChzjbH/x7JyxNDFJAVihIhE/83je+XOHYxqjMB5WICJ0nXtD17n3O8dTAM+9JgY9X9YXjNbvq6riwcGgDJnJfWppVaUmC7sLrXbIacWfCZqiKfWiZpLqJJ42zprDS+tRR1hxiOFFazGKoObznSW92jjExpcfjDt4KgreaXWkEG8twzPpnDITakuGZoFXie9O8ybqXxPl3pT8KKATxpURTMUbFkPy9Jxa3T88QxkpJVkgkS4Uf9byvoBYZVpKjskXUV4Tqb/8HgI3T0FQln2XrUKaJrGcJpwyt5SseKUIhTZo2/rBRd28zzr3O6+ZQbfWbjLwqGO+LNSY6w0o/RZn2PEDWsGI0rj/s6i/MtZBnoNz/pxpOeLMKPLOlV2FvAcZgtOE6vD15ntFr5/P2NGf2PbPIthVrkulI1O6Z+KsCtIhBJaMjrJeKfvLJ7Kop145ACFBgMQmZQyFXKkDmMJzXLmJnE7MvyTy64vKd0601qs4mfrXo47YH6B4Dxnpkt4hS82U8Mydu9x29lHr3CZeRXtVBk2gEsCWbG+DQMdHh7I1sAOAcBznfEGGiR4VIcMRRWPNPFDAV5ThrSgFDXfOoGAYSENqJBwC1MiGSBXVaFHNEHGzlNFIUmSpZZFj6zSsxg+CRLMXmcuHKARvKNE3nQ8d3vhyjjsfkkVays7nrsp19nowreQuhuvp7c/9+YF3BgKXQnoYc4IQMdKXnlR8lxkFB+KI3Z1jMGW1QXrsFcX5hbcFip5dplWJyQoxBSkAJLCMYQBsEVD+vg1a8NeirqE14SOf+LwKRh1tk8Exny6Ov3EG2MeE/qWlBytpTlGok3mIfEm0GKXLhm6KXVnOK2IcOXV/5IjRREiKkny2MkmT39GHPvmLEClmeiEpZK8yJia9TvGQ4YWDQDqHFwnnkoQspb+ErtXrUEDUMkfOPAxVUv/jqP3TPQhzRIlLFxhGBBZKjVbgZAYpBKcn2W5iRjzflvrcqhRU6pT4THUOE9YwJ6Fw7AyDh+dDRFQCpJqugbUsRep7x/6KBr3SlNHa5OL05Kgo3gghiPTZT3Tyz9OTCb03M+C+6D115xgx6/U0MTeAVEYxBUNjpEV51KFoFbIJC2dGlUTvMpGNQ6qUA1hFSSSSTg8v+pOhkIJFIRCBVBYByf68dwzDdqQQwzVJhFQfcQ/JwzFUgGkivhK2TLJ+8rIK6d2nm5H7JJXNBShFDZMT6L9LCeUzJ08tE0uhLSUVLioXs3tQyBJylYNikRIQiMKy0g7okDqvMdoEt+W+krF+NYMuAVxeXxvdN50tjBQfFCopzr5JJkoEYvEMfYbDxcvgaNEc8NwqFs8zLxLMyH4X6gcJrqTOEb7N6a2ox0jQhLKekhd5WcXOPacvkzKRg4YNeiSGPAfxgj1+PpvYhSMIfEL28pJnpd6+CaLlHbw/UZO94nWIt129B+T3INoViveQO60+DSn3nLsaijmZ8R7CMHaEL+g9h3imGA9I5033QGYyHt4H4G4AVwE0v1+DNgAulKW5hDmZiDXlwQo8QGSe45cRT4UhazX4AqRJEGdBmHyY9B1GIlScJXFmtpqzoxEnp4RTDqu1EtPh/dHvND2YIW+AEw3ojrqHaBxp/949rFgDrxhCYodyqIXYCWUSltR1+TWkZy0OJGpOMs46Vyqu3gPl18DhWfXuID0jkeAeMub+MLrC51PvHtIo2LsCH41khgP3RqPwgylLcwnABQA38BUM+v8H5sxP5ZkaoU4AAAAldEVYdGRhdGU6Y3JlYXRlADIwMTItMDktMDNUMDk6NDY6MDArMDI6MDAz+X7GAAAAJXRFWHRkYXRlOm1vZGlmeQAyMDEyLTA5LTAzVDA5OjQ2OjAwKzAyOjAwQqTGegAAAABJRU5ErkJggg=="
                for k, v in x.items():
                    # Handle bytes (images) and datetime fields to avoid any errors in response
                    if str(type(v)) == "<class 'bytes'>":
                        try:
                            v = v.decode('utf-8')
                        except AttributeError:
                            pass
                        x[k] = v
                    if str(type(v)) in ("<class 'datetime.datetime'>", "<class 'datetime.date'>"):
                        x[k] = str(v)
                    if str(k) == "blood_type" or str(k) == "rh":
                        if not v:
                            x[k] = ""
                        else:
                            x[k] = v
                data_to_push.append(x)

            return valid_response(data_to_push)
        return invalid_response('invalid object model', 'The model %s is not available in the registry.' % model_name)

    @authenticate_token
    @http.route(['/intarvas/get-doctor-list'], type='http', auth="none", methods=['GET'], csrf=False)
    def get_doctor_list(self, **payload):
        """This method will allow list all the doctors

        Args:
            token: must contain in headers to validate the call
        Returns:
            - Data dictionary containing list of all doctors with required fields.
            - Returns if failed error message in the body in json format
        """
        model_name = 'oeh.medical.physician'
        model = request.env[self._model].sudo().search([('model', '=', model_name)], limit=1)
        payload['fields'] = "['id', 'name', 'speciality', 'degree_id', 'image_512', 'available_lines', 'appointment_type', 'prescription_count']"

        if model:
            domain, fields, offset, limit, order = extract_arguments(
                payload)
            data = request.env[model.model].sudo().search_read(
                domain=domain, fields=fields, offset=offset, limit=limit, order=order)

            data_to_push = []
            for x in data:
                if 'image_512' in x:
                    x['image'] = x.pop('image_512')
                    if not x.get('image') or x.get('image') == 'false':
                        x['image'] = "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"
                for k, v in x.items():
                    # Handle bytes (images) and datetime fields to avoid any errors in response
                    if str(type(v)) == "<class 'bytes'>":
                        try:
                            v = v.decode('utf-8')
                        except AttributeError:
                            pass
                        x[k] = v
                    if str(type(v)) in ("<class 'datetime.datetime'>", "<class 'datetime.date'>"):
                        x[k] = str(v)
                    if str(k) == "degree_id":
                        degree_name = []
                        if v and len(v) > 0:
                            for degree_id in v:
                                degree = request.env['oeh.medical.degrees'].browse(int(degree_id))
                                if degree:
                                    degree_name.append(str(degree.name))
                        else:
                            degree_name = v
                        x[k] = degree_name
                    if str(k) == "speciality":
                        if v and len(v) > 0:
                            x[k] = v[1]
                        else:
                            x[k] = ""
                    if str(k) == "available_lines":
                        schedule_list = []
                        if v and len(v) > 0:
                            for schedule_id in v:
                                schedule = request.env['oeh.medical.physician.line'].browse(int(schedule_id))
                                if schedule:
                                    schedule_values = {
                                        'day': schedule.name,
                                        'start_time': self.get_time_string(schedule.start_time),
                                        'end_time': self.get_time_string(schedule.end_time),
                                    }
                                    schedule_list.append(schedule_values)
                        else:
                            schedule_list = v
                        x[k] = schedule_list
                data_to_push.append(x)

            return valid_response(data_to_push)
        return invalid_response('invalid object model', 'The model %s is not available in the registry.' % model_name)

    @authenticate_token
    @http.route(['/intarvas/get-prescription-info/<user_type>/<user_id>'], type='http', auth="none", methods=['GET'], csrf=False)
    def get_prescription_list(self, user_type=None,user_id=None, **payload):
        """This method will allow list all the prescription information for given user id and type

        Args:
            token: must contain in headers to validate the call
            <user_type> must contain user's type [1: Patient, 2: Physician, 3: Health Center Admin]
            <user_id> Logged in User ID
        Returns:
            - Data dictionary containing list of assigned (in case of patient login) / generated (in case of doctor login)
            prescriptions for given in user type and id.
            - Returns if failed error message in the body in json format
        """
        if not user_type:
            return invalid_response('user_type not found', 'User type not found in request ! ')

        if not user_id:
            return invalid_response('user_id not found', 'User ID not found in request ! ')

        model_name = 'oeh.medical.prescription'
        model = request.env[self._model].sudo().search([('model', '=', model_name)], limit=1)
        payload['fields'] = "['id', 'name', 'patient', 'doctor', 'date', 'info', 'prescription_line']"

        payload['order'] = 'id desc'

        if user_type == '1':
            payload['domain'] = "[('patient', '=', " + str(user_id) + ")]"
        elif user_type == '2':
            payload['domain'] = "[('doctor', '=', " + str(user_id) + ")]"

        if model:
            domain, fields, offset, limit, order = extract_arguments(
                payload)
            data = request.env[model.model].sudo().search_read(
                domain=domain, fields=fields, offset=offset, limit=limit, order=order)

            data_to_push = []
            for x in data:
                for k, v in x.items():
                    if str(type(v)) in ("<class 'datetime.datetime'>", "<class 'datetime.date'>"):
                        x[k] = str(v)
                    if str(k) == "info":
                        if v and len(v) > 0:
                            x[k] = v[1]
                        else:
                            x[k] = ""
                    if str(k) == "patient":
                        if v and len(v) > 0:
                            x[k] = v[1]
                        else:
                            x[k] = ""
                    if str(k) == "doctor":
                        if v and len(v) > 0:
                            x[k] = v[1]
                        else:
                            x[k] = ""
                    if str(k) == "prescription_line":
                        prescription_list = []
                        if v and len(v) > 0:
                            for prescription_id in v:
                                prescription = request.env['oeh.medical.prescription.line'].browse(int(prescription_id))
                                if prescription:
                                    if prescription.start_treatment:
                                        start_treatment_str = str(prescription.start_treatment)
                                    else:
                                        start_treatment_str = ''

                                    if prescription.end_treatment:
                                        end_treatment_str = str(prescription.end_treatment)
                                    else:
                                        end_treatment_str = ''

                                    if prescription.dose and prescription.dose_unit:
                                        dose_str = str(prescription.qty) + " (" + str(prescription.dose) + " " + str(
                                            prescription.dose_unit.name) + ")"
                                    else:
                                        dose_str = str(prescription.qty)
                                    prescription_values = {
                                        'name': prescription.name.name or '',
                                        'indication': prescription.indication.name or '',
                                        'dose': dose_str,
                                        'start_treatment': start_treatment_str,
                                        'end_treatment': end_treatment_str,
                                    }
                                    prescription_list.append(prescription_values)
                        else:
                            prescription_list = v
                        x[k] = prescription_list
                data_to_push.append(x)

            return valid_response(data_to_push)
        return invalid_response('invalid object model', 'The model %s is not available in the registry.' % model_name)

    @authenticate_token
    @http.route(['/intarvas/get-labtest-info/<user_type>/<user_id>'], type='http', auth="none", methods=['GET'],
                csrf=False)
    def get_labtest_list(self, user_type=None, user_id=None, **payload):
        """This method will allow list all the labtest information for given user id and type

        Args:
            token: must contain in headers to validate the call
            <user_type> must contain user's type [1: Patient, 2: Physician, 3: Health Center Admin]
            <user_id> Logged in User ID
        Returns:
            - Data dictionary containing list of assigned (in case of patient login) / generated (in case of doctor login)
            lab tests for given in user type and id.
            - Returns if failed error message in the body in json format
        """
        if not user_type:
            return invalid_response('user_type not found', 'User type not found in request ! ')

        if not user_id:
            return invalid_response('user_id not found', 'User ID not found in request ! ')

        model_name = 'oeh.medical.lab.test'
        model = request.env[self._model].sudo().search([('model', '=', model_name)], limit=1)
        payload['fields'] = "['id', 'name', 'patient', 'pathologist', 'test_type', 'requestor', 'date_requested', 'date_analysis', 'results', 'state', 'lab_test_criteria']"

        payload['order'] = 'id desc'

        if user_type == '1':
            payload['domain'] = "[('patient', '=', " + str(user_id) + ")]"
        elif user_type == '2':
            payload['domain'] = "[('pathologist', '=', " + str(user_id) + ")]"

        if model:
            domain, fields, offset, limit, order = extract_arguments(
                payload)
            data = request.env[model.model].sudo().search_read(
                domain=domain, fields=fields, offset=offset, limit=limit, order=order)

            data_to_push = []
            for x in data:
                for k, v in x.items():
                    if str(type(v)) in ("<class 'datetime.datetime'>", "<class 'datetime.date'>"):
                        date = v.strftime("%Y-%m-%d %H:%M:%S")
                        x[k] = str(date)
                    if str(k) == "results":
                        if v and len(v) > 0:
                            x[k] = v[1]
                        else:
                            x[k] = ""
                    if str(k) == "requestor":
                        if v and len(v) > 0:
                            x[k] = v
                        else:
                            x[k] = ""
                    if str(k) == "patient":
                        if v and len(v) > 0:
                            x[k] = v[1]
                        else:
                            x[k] = ""
                    if str(k) == "pathologist":
                        if v and len(v) > 0:
                            x[k] = v[1]
                        else:
                            x[k] = ""
                    if str(k) == "test_type":
                        if v and len(v) > 0:
                            x[k] = v[1]
                        else:
                            x[k] = ""
                    if str(k) == "lab_test_criteria":
                        labtest_list = []
                        if v and len(v) > 0:
                            for labtest_id in v:
                                labtest_result = request.env['oeh.medical.lab.resultcriteria'].sudo().browse(int(labtest_id))
                                if labtest_result:
                                    labtest_values = {
                                        'name': labtest_result.name or '',
                                        'result': labtest_result.result or '',
                                        'normal_range': labtest_result.normal_range or '',
                                        'unit': str(labtest_result.units.name) or '',
                                    }
                                    labtest_list.append(labtest_values)
                        else:
                            labtest_list = v
                        x[k] = labtest_list
                data_to_push.append(x)

            return valid_response(data_to_push)
        return invalid_response('invalid object model', 'The model %s is not available in the registry.' % model_name)

    @authenticate_token
    @http.route(['/intarvas/get-appointment/<user_type>/<user_id>'], type='http', auth="none", methods=['GET'],
                csrf=False)
    def get_appointment(self, user_type=None, user_id=None, **payload):
        """This method will allow list all the appointments for given user id and type

        Args:
            token: must contain in headers to validate the call
            <user_type> must contain user's type [1: Patient, 2: Physician]
            <user_id> Logged in User ID
        Returns:
            - Data dictionary containing list of appointments for given in user type and id.
            - Returns if failed error message in the body in json format
        """
        if not user_type:
            return invalid_response('user_type not found', 'User type not found in request ! ')

        if not user_id:
            return invalid_response('user_id not found', 'User ID not found in request ! ')

        model_name = 'oeh.medical.appointment'
        model = request.env[self._model].sudo().search([('model', '=', model_name)], limit=1)
        payload[
            'fields'] = "['id', 'name', 'patient', 'doctor', 'appointment_date', 'appointment_end', 'institution', 'urgency_level', 'comments', 'patient_status', 'state']"

        if user_type == '1':
            payload['domain'] = "[('patient', '=', " + str(user_id) + ")]"
        elif user_type == '2':
            payload['domain'] = "[('doctor', '=', " + str(user_id) + ")]"

        payload['order'] = 'appointment_date desc'

        if model:
            domain, fields, offset, limit, order = extract_arguments(
                payload)
            data = request.env[model.model].sudo().search_read(
                domain=domain, fields=fields, offset=offset, limit=limit, order=order)

            data_to_push = []
            for x in data:
                for k, v in x.items():
                    if str(type(v)) in ("<class 'datetime.datetime'>", "<class 'datetime.date'>"):
                        date = v.strftime("%Y-%m-%d %H:%M:%S")
                        x[k] = str(date)
                    if str(k) == "comments":
                        if v and len(v) > 0:
                            x[k] = v[1]
                        else:
                            x[k] = ""
                    if str(k) == "patient":
                        if v and len(v) > 0:
                            x[k] = v[1]
                        else:
                            x[k] = ""
                    if str(k) == "doctor":
                        if v and len(v) > 0:
                            x[k] = v[1]
                        else:
                            x[k] = ""
                    if str(k) == "institution":
                        if v and len(v) > 0:
                            x[k] = v[1]
                        else:
                            x[k] = ""
                data_to_push.append(x)

            return valid_response(data_to_push)
        return invalid_response('invalid object model', 'The model %s is not available in the registry.' % model_name)

    @authenticate_token
    @http.route(['/intarvas/update-profile-photo/<user_type>/<user_id>'], type='http', auth="none", methods=['PUT'],
                csrf=False)
    def update_profile_photo(self, user_type=None, user_id=None, **payload):
        """Update an existing user's profile image.

        Args:
            token: must contain in headers to validate the call
            <user_type> must contain user's type [1: Patient, 2: Physician, 3: Health Center Admin]
            <user_id> Logged in User ID
            file object (ufile): must contain profile image files in body as form-data.
        Returns:
            - Data dictionary containing profile picture update status.
            - Returns if failed error message in the body in json format
        """
        if not user_type:
            return invalid_response('user_type not found', 'User type not found in request ! ')

        if not user_id:
            return invalid_response('user_id not found', 'User ID not found in request ! ')

        if user_type == '1':
            model_name = 'oeh.medical.patient'
        elif user_type == '2':
            model_name = 'oeh.medical.physician'
        else:
            model_name = 'res.users'

        model = request.env[self._model].sudo().search([('model', '=', model_name)], limit=1)
        if model:
            if payload.get('ufile'):
                files = request.httprequest.files.getlist('ufile')
                args = []
                attachment = False
                for ufile in files:

                    filename = ufile.filename
                    if request.httprequest.user_agent.browser == 'safari':
                        # Safari sends NFD UTF-8 (where é is composed by 'e' and [accent])
                        # we need to send it the same stuff, otherwise it'll fail
                        filename = unicodedata.normalize('NFD', ufile.filename)

                    try:
                        file_data = base64.encodestring(ufile.read())
                        file_data_to_send = file_data.decode('utf-8')
                        #data = request.env['oeh.rest.api.token'].sudo()._store_images_from_api(file_data)
                        if file_data:
                            image_values = {
                                #'image_medium': data["image_medium"],
                                #'image_small': data["image_small"],
                                'image_1920': file_data,
                            }
                            request.env[model.model].sudo().browse(int(user_id)).write(image_values)
                            data = {
                                'message': 'Profile Picture updated successfully!',
                                'filename': filename,
                                'image': file_data_to_send,
                                'mimetype': ufile.content_type,
                                }
                            return valid_response(data)
                    except Exception as e:
                        return invalid_response('failed to upload image', 'Failed to upload image !')
        return invalid_response('invalid object model', 'The model %s is not available in the registry.' % model_name)

    @authenticate_token
    @http.route(['/intarvas/remove-profile-photo/<user_type>/<user_id>'], type='http', auth="none", methods=['GET'],
                csrf=False)
    def remove_profile_photo(self, user_type=None, user_id=None, **payload):
        """Remove an existing user's profile image.

        Args:
            token: must contain in headers to validate the call
            <user_type> must contain user's type [1: Patient, 2: Physician, 3: Health Center Admin]
            <user_id> Logged in User ID
        Returns:
            - Data dictionary containing profile picture removal status.
            - Returns if failed error message in the body in json format
        """
        if not user_type:
            return invalid_response('user_type not found', 'User type not found in request ! ')

        if not user_id:
            return invalid_response('user_id not found', 'User ID not found in request ! ')

        if user_type == '1':
            model_name = 'oeh.medical.patient'
        elif user_type == '2':
            model_name = 'oeh.medical.physician'
        else:
            model_name = 'res.users'

        model = request.env[self._model].sudo().search([('model', '=', model_name)], limit=1)
        if model:
            try:
                file_data = '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'
                #data = request.env['oeh.rest.api.token'].sudo()._store_images_from_api(file_data)
                if file_data:
                    image_values = {
                        #'image_medium': data["image_medium"],
                        #'image_small': data["image_small"],
                        'image_1920': file_data,
                    }
                    request.env[model.model].sudo().browse(int(user_id)).write(image_values)
                    data = {
                        'message': 'Profile photo removed successfully!',
                        'image': file_data
                    }
                    return valid_response(data)
            except Exception as e:
                return invalid_response('failed to remove image', 'Failed to remove profile image !')
        return invalid_response('invalid object model', 'The model %s is not available in the registry.' % model_name)

    @authenticate_token
    @http.route(['/intarvas/update-profile/<user_type>/<user_id>'], type='http', auth="none", methods=['POST'],
                csrf=False)
    def update_profile(self, user_type=None, user_id=None, **payload):
        """Update existing user's profile information

        Args:
            token: must contain in headers to validate the call
            <user_type> must contain user's type [1: Patient, 2: Physician, 3: Health Center Admin]
            <user_id> Logged in User ID
        Returns:
            - Data dictionary containing profile update status.
            - Returns if failed error message in the body in json format
        """
        if not user_type:
            return invalid_response('user_type not found', 'User type not found in request ! ')

        if not user_id:
            return invalid_response('user_id not found', 'User ID not found in request ! ')

        if user_type == '1':
            model_name = 'oeh.medical.patient'
        elif user_type == '2':
            model_name = 'oeh.medical.physician'
        else:
            model_name = 'res.users'

        model = request.env[self._model].sudo().search([('model', '=', model_name)], limit=1)
        if model:
            try:
                user = request.env[model.model].sudo().search([('id', '=', int(user_id))])
                if user:
                    request.env[model.model].sudo().browse(int(user.id)).write(payload)
                else:
                    return invalid_response('no_patient_found', 'No profile found for given ID %s' % str(user_id))
            except Exception as e:
                return invalid_response('failed to update profile', 'Failed to update profile information !')
            else:
                data = {
                    'message': 'Profile updated successfully!'
                }
                return valid_response(data)
        return invalid_response('invalid object model', 'The model %s is not available in the registry.' % model_name)

    @authenticate_token
    @http.route(['/intarvas/today-appointment/<user_type>/<user_id>'], type='http', auth="none", methods=['GET'],
                csrf=False)
    def get_todays_appointment(self, user_type=None, user_id=None, **payload):
        """This method will list all the appointments of current date for given user id and type

        Args:
            token: must contain in headers to validate the call
            <user_type> must contain user's type [1: Patient, 2: Physician]
            <user_id> Logged in User ID
        Returns:
            - Data dictionary containing today’s appointment(s) list.
            - Returns if failed error message in the body in json format
        """
        if not user_type:
            return invalid_response('user_type not found', 'User type not found in request ! ')

        if not user_id:
            return invalid_response('user_id not found', 'User ID not found in request ! ')

        model_name = 'oeh.medical.appointment'
        model = request.env[self._model].sudo().search([('model', '=', model_name)], limit=1)
        payload[
            'fields'] = "['id', 'name', 'patient', 'doctor', 'appointment_date', 'appointment_end', 'institution', 'urgency_level', 'comments', 'patient_status', 'state']"

        if user_type == '1':
            payload['domain'] = "[('patient', '=', " + str(user_id) + ")]"
        elif user_type == '2':
            payload['domain'] = "[('doctor', '=', " + str(user_id) + ")]"

        payload['order'] = 'appointment_date desc'

        if model:
            domain, fields, offset, limit, order = extract_arguments(
                payload)
            data = request.env[model.model].sudo().search_read(
                domain=domain, fields=fields, offset=offset, limit=limit, order=order)

            data_to_push = []
            for x in data:
                appointment_start = x.get('appointment_date')

                if str(type(appointment_start)) in ("<class 'datetime.datetime'>", "<class 'datetime.date'>"):
                    appointment_start_date = appointment_start.date().strftime("%Y-%m-%d")
                else:
                    appointment_start_date = datetime.strptime(appointment_start, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")

                if appointment_start_date == datetime.today().date().strftime("%Y-%m-%d"):
                    for k, v in x.items():
                        if str(type(v)) in ("<class 'datetime.datetime'>", "<class 'datetime.date'>"):
                            date = v.strftime("%Y-%m-%d %H:%M:%S")
                            x[k] = str(date)
                        if str(k) == "comments":
                            if v and len(v) > 0:
                                x[k] = v[1]
                            else:
                                x[k] = ""
                        if str(k) == "patient":
                            if v and len(v) > 0:
                                x[k] = v[1]
                            else:
                                x[k] = ""
                        if str(k) == "doctor":
                            if v and len(v) > 0:
                                x[k] = v[1]
                            else:
                                x[k] = ""
                        if str(k) == "institution":
                            if v and len(v) > 0:
                                x[k] = v[1]
                            else:
                                x[k] = ""
                    data_to_push.append(x)

            return valid_response(data_to_push)
        return invalid_response('invalid object model', 'The model %s is not available in the registry.' % model_name)

    @authenticate_token
    @http.route(['/intarvas/notification/mute/<user_type>/<user_id>'], type='http', auth="none", methods=['GET'],
                csrf=False)
    def mute_notifications(self, user_type=None, user_id=None, **payload):
        """This method will turn notifications status ON or OFF based on user's action on the mobile apps.

        Args:
            token: must contain in headers to validate the call
            <user_type> must contain user's type [1: Patient, 2: Physician]
            <user_id> Logged in User ID
        Returns:

            returns if failed error message in the body in json format
        """
        if not user_type:
            return invalid_response('user_type not found', 'User type not found in request ! ')

        if not user_id:
            return invalid_response('user_id not found', 'User ID not found in request ! ')

        model_name = 'oeh.medical.notifications'
        model = request.env[self._model].sudo().search([('model', '=', model_name)], limit=1)

        if model:
            try:
                user = False

                if user_type == '1':
                    user = request.env['oeh.medical.notifications'].sudo().search([('patient_id', '=', int(user_id))])
                elif user_type == '2':
                    user = request.env['oeh.medical.notifications'].sudo().search([('physician_id', '=', int(user_id))])

                if user:
                    if 'notification' in payload and payload.get('notification'):
                        if payload.get('notification')=='off':
                            request.env[model.model].sudo().browse(int(user.id)).write({
                                'notification_setting': False
                            })
                        else:
                            request.env[model.model].sudo().browse(int(user.id)).write({
                                'notification_setting': True
                            })
                else:
                    return invalid_response('no_profile_found', 'No notification profile found for given ID %s' % str(user_id))
            except Exception as e:
                return invalid_response('failed to update profile', 'Failed to update notification status !')
            else:
                data = {
                    'message': 'Notification status updated successfully!'
                }
                return valid_response(data)
        return invalid_response('invalid object model', 'The model %s is not available in the registry.' % model_name)

    @authenticate_token
    @http.route(['/intarvas/patient/registration'], type='http', auth="none", methods=['GET'],
                csrf=False)
    def patient_registration(self, **post):
        model_name = 'oeh.medical.patient'
        model = request.env[self._model].sudo().search([('model', '=', model_name)], limit=1)

        if model:
            try:
                username, password, first_name, middle_name, last_name = post.get('login'), post.get('password'), post.get('first_name'), post.get('middle_name'), post.get('last_name')
                if not all([username, password, first_name, middle_name, last_name]):
                    # throw error message if any information from name, login, password are not provided or incorrect
                    error_msg = 'either of the following are missing [login, password, first_name, middle_name, last_name]'
                    return invalid_response('missing error', error_msg)

                values = {}
                supported_langs = [lang['code'] for lang in request.env['res.lang'].sudo().search_read([], ['code'])]
                if request.lang in supported_langs:
                    values['lang'] = request.lang

                name = first_name + ' ' + middle_name + ' ' + last_name
                values['name'] = name
                values['active'] = True
                values['customer'] = True

                search_partner = request.env[model_name].sudo().search([('name', '=', name)], limit=1)
                if search_partner:
                    partner = search_partner
                else:
                    partner = request.env['res.partner'].sudo().create(values)

                if partner:
                    patient_values = {}
                    search_patient = request.env[model_name].sudo().search([('first_name','=', first_name),
                                                                            ('middle_name','=', middle_name),
                                                                            ('last_name','=', last_name)], limit=1)
                    if search_patient:
                        return invalid_response('patient already exists', 'Patient already exists !')

                    patient_values['first_name'] = first_name
                    patient_values['middle_name'] = middle_name
                    patient_values['last_name'] = last_name
                    patient_values['partner_id'] = partner.id

                    if post.get('dob'):
                        patient_values['dob'] = post.get('dob')
                    if post.get('gender'):
                        patient_values['sex'] = post.get('gender')
                    if post.get('is_covid19'):
                        patient_values['is_covid_19'] = True
                        if post.get('partner_latitude'):
                            patient_values['partner_latitude'] = post.get('partner_latitude')
                        if post.get('partner_longitude'):
                            patient_values['partner_longitude'] = post.get('partner_longitude')

                    patient = request.env[model_name].sudo().create(patient_values)
                    if patient:
                        group_employee_id = request.env.ref('base.group_user').id
                        group_patient_id = request.env.ref('intarvas.group_oeh_medical_patient').id
                        user_values = {
                            'name': partner.name,
                            'partner_id': partner.id,
                            'login': username,
                            'password': password,
                            'no_reset_password': True,
                            'group_ids': [(6, 0, [group_employee_id,group_patient_id])]
                        }
                        if partner.company_id:
                            user_values['company_id'] = partner.company_id.id
                            user_values['company_ids'] = [(6, 0, [partner.company_id.id])]
                        partner_user = request.env['res.users'].sudo()._signup_create_user(user_values)
                        if partner_user:
                            patient.sudo().write({'oeh_patient_user_id': partner_user.id})

            except Exception as e:
                print(e)
                return invalid_response('failed to register patient', 'Failed to register new patient !')
            else:
                data = {
                    'message': 'Patient Registered successfully!'
                }
                return valid_response(data)
        return invalid_response('invalid object model', 'The model %s is not available in the registry.' % model_name)