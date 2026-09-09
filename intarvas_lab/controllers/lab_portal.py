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
from odoo import http, _
import dateutil.parser
from odoo.http import request, content_disposition
from odoo.exceptions import UserError

class OehLab(http.Controller):

    @http.route(['/patient/portal/<int:patient_id>/lab-tests'], type='http', auth="user", website=True)
    def view_patient_labtest(self, patient_id=False, **post):
        values = {}
        values['patient'] = request.env['oeh.medical.patient'].sudo().browse(int(patient_id))
        values['progress_labtest'] = progress_labtest = request.env['oeh.medical.lab.test'].sudo().search(
            [('patient', '=', patient_id), ('state', 'in', ('Draft', 'Test In Progress'))])
        values['completed_labtest'] = completed_labtest = request.env['oeh.medical.lab.test'].sudo().search(
            [('patient', '=', patient_id), ('state', '=', 'Completed')])
        if progress_labtest or completed_labtest:
            values['labtest_available'] = True
        else:
            values['labtest_available'] = False
        return request.render("intarvas_lab.view_patient_lab_test", values)

    @http.route('/patient/portal/<int:patient_id>/lab_requests', type='http', auth='user', website=True)
    def patient_lab_request(self, patient_id=False):
        values = {}
        if patient_id:
            values['patient'] = request.env['oeh.medical.patient'].sudo().browse(int(patient_id))
            values['lab_request'] = lab_request = request.env['oeh.medical.lab.request'].sudo().search([
                ('patient', '=', int(patient_id))
            ])
            if lab_request:
                values['lab_request_available'] = True
            else:
                values['lab_request_available'] = False
        else:
            return request.redirect('/patient/portal/')
        return request.render("intarvas_lab.view_patient_lab_requests", values)

    @http.route(['/patient/portal/<int:patient_id>/lab_request',
                 '/patient/portal/<int:patient_id>/lab_request/<int:labreq_id>'],
                type='http', auth="user", website=True)
    def add_patient_lab_request(self, patient_id=False, labreq_id=False, **post):
        values = {}
        if 'error_message' in post:
            values['error_message'] = post.get('error_message')
        if patient_id:
            values['patient'] = request.env['oeh.medical.patient'].sudo().browse(int(patient_id))
            values['institutions'] = request.env['oeh.medical.health.center'].sudo().search([])
            if labreq_id:
                labreq = request.env['oeh.medical.lab.request'].sudo().browse(int(labreq_id))
                date_requested = dateutil.parser.parse(
                    labreq.date_requested.strftime("%Y-%m-%d %H:%M")).isoformat()
                values['labreq'] = labreq
                values['date_requested'] = date_requested
                values['requestor'] = labreq.requestor
                values['chief_complaint'] = labreq.chief_complaint
                values['form_action'] = _("/patient/portal/lab_request/%s/edit") % int(labreq_id)
            else:
                values['labreq'] = False
                values['date_requested'] = False
                values['requestor'] = False
                values['chief_complaint'] = False
                values['form_action'] = "/patient/portal/lab_request/add"
        else:
            return request.redirect('/patient/portal')
        return request.render("intarvas_lab.patient_manage_lab_requests", values)

    @http.route('/patient/portal/lab_request/add', type='http', auth="user", website=True)
    def create_patient_lab_request(self, **post):
        try:
            patient = request.env['oeh.medical.patient'].sudo().browse(int(post.get('patient')))
            post['patient'] = int(post.get('patient'))
            post['requestor'] = post.get('requestor')
            post['chief_complaint'] = post.get('chief_complaint')
            lab_ids = request.httprequest.args.getlist('lab_test_ids')
            lab_test = []
            for i in lab_ids:
                lab_test.append(int(i))
            post['lab_test_ids'] = lab_test
            post['date_requested'] = dateutil.parser.parse(post.get('date_requested'))
            request.env['oeh.medical.lab.request'].sudo().create(post)
        except UserError as e:
            return request.redirect('/patient/portal/lab-results?error=1')
        return request.redirect('/patient/portal/lab-results')

    @http.route('/patient/portal/lab_request/<int:labreq_id>/edit', type='http', auth="user", website=True)
    def update_patient_lab_request(self, labreq_id=False, **post):
        if labreq_id:
            patient = request.env['oeh.medical.patient'].sudo().browse(int(post.get('patient')))
            post['requestor'] = post.get('requestor')
            post['chief_complaint'] = post.get('chief_complaint')
            lab_ids = request.httprequest.args.getlist('lab_test_ids')
            lab = []
            for i in lab_ids:
                lab.append(int(i))
            post['lab_test_ids'] = lab
            post['date_requested'] = dateutil.parser.parse(post.get('date_requested'))
            request.env['oeh.medical.lab.request'].sudo().browse(int(labreq_id)).write(post)
        return request.redirect('/patient/portal/lab-results')

    @http.route('/patient/portal/<int:patient_id>/lab_request/<int:labreq_id>/remove', type='http', auth="user",
                website=True)
    def delete_patient_labrequest(self, patient_id=False, labreq_id=False, **post):
        if labreq_id:
            labreq = request.env['oeh.medical.lab.request'].sudo().browse(int(labreq_id))
            labreq.sudo().unlink()
        return request.redirect('/patient/portal/lab-results')

    @http.route(
        ['/patient/portal/labtest-report/<int:lab_id>'],
        type='http', auth='user', website=True)
    def print_lab_test(self, lab_id=False):
        if lab_id:
            report = request.env['ir.actions.report']
            lab = request.env['oeh.medical.lab.test'].sudo().browse(int(lab_id))
            report_ref = 'intarvas_lab.action_report_patient_labtest'
            report_sudo = request.env.ref(report_ref).sudo()
            if not isinstance(report_sudo, type(request.env['ir.actions.report'])):
                raise UserError(_("%s is not the reference of a report") % report_ref)
            #report = getattr(report_sudo, method_name)([lab_id], data={'report_type': 'pdf'})[0]
            pdf = report._render_qweb_pdf(report_ref=report_sudo.report_name, res_ids=[lab_id],
                                          data={'report_type': 'pdf'})[0]
            reporthttpheaders = [
                ('Content-Type', 'application/pdf'),
                ('Content-Length', len(pdf)),
            ]
            filename = "Lab Test Report - %s.pdf" % str(lab.name)
            reporthttpheaders.append(('Content-Disposition', content_disposition(filename)))
            return request.make_response(pdf, headers=reporthttpheaders)
        else:
            return request.redirect('/patient/portal')

    @http.route('/patient/portal/labtest/<int:lab_id>/remove', type='http', auth="user", website=True)
    def delete_patient_lab_test(self, lab_id=False, **post):
        if lab_id:
            lab = request.env['oeh.medical.lab.test'].sudo().browse(int(lab_id))
            lab.sudo().unlink()
        return request.redirect('/patient/portal')
