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


from odoo import fields, models, api, _
from werkzeug.urls import url_encode
import random, string
from odoo.exceptions import UserError


class intarvasMedicalPatient(models.Model):
    _inherit = 'oeh.medical.patient'

    patient_token = fields.Char(string="Patient Token")
    patient_url = fields.Char(string="Patient URL", compute="_get_patient_url")
    is_portal_access = fields.Boolean(string='Is having Portal Access?', default=False)
    base_url = fields.Char(string='Base URL')


    @api.model_create_multi
    def create(self, vals_list):
        if not isinstance(vals_list, list):
            vals_list = [vals_list]

        for vals in vals_list:
            vals['patient_token'] = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

        return super(intarvasMedicalPatient, self).create(vals_list)

    def change_grant_access(self):
        for patient in self:
            if patient.is_portal_access:
                # Store user info before revoking access
                revoked_user_name = patient.oeh_patient_user_id.name if patient.oeh_patient_user_id else None
                
                patient.is_portal_access = False
                if patient.oeh_patient_user_id:
                    patient.oeh_patient_user_id.sudo().write({
                        'active': False
                    })
                    
                    # Log the activity for audit trail
                    patient.message_post(
                        body=f"Portal access revoked. User {revoked_user_name} no longer has access to patient portal.",
                        message_type='notification'
                    )
                    
                    
            else:

                if not patient.oeh_patient_user_id:
                    if not patient.email:
                        raise UserError(
                            _('Please enter correct email address !'))

                    group_portal_id = self.env.ref('base.group_portal').id
                    default_password = self.env.company.patient_account_password

                    user_values = {
                        'name': patient.name,
                        'partner_id': patient.partner_id and patient.partner_id.id or False,
                        'login': patient.email or patient.partner_id.email or False,
                        'password': default_password or False,
                        'group_ids': [(6, 0, [group_portal_id])],
                        'active': True
                    }
                    user = self.env['res.users'].sudo().create(user_values)
                    search_resource = self.env['resource.resource'].sudo().search([('name', '=', patient.name)],
                                                                                  limit=1)
                    if search_resource and user:
                        search_resource.write({'user_id': user.id})

                    patient.oeh_patient_user_id = user.id
                    patient.is_portal_access = True
                    user.sudo().action_reset_password()
                else:
                    patient.is_portal_access = True
                    if patient.oeh_patient_user_id:
                        patient.oeh_patient_user_id.sudo().write({
                            'active': True
                        })

                template_id = self.env['ir.model.data']._xmlid_to_res_id(
                    'intarvas_patient_portal.oeh_email_template_patient_portal',
                    raise_if_not_found=False)
                ctx = {
                    'default_model': 'oeh.medical.patient',
                    'default_res_ids': self.ids,
                    'default_use_template': bool(template_id),
                    'default_template_id': template_id,
                    'default_composition_mode': 'comment',
                    'force_email': True,
                }
                return {
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'mail.compose.message',
                    'views': [(False, 'form')],
                    'view_id': False,
                    'target': 'new',
                    'context': ctx,
                }

    def _get_patient_url(self):
        for patient in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            patient.patient_url = base_url + '/patient/portal'


class intarvasMedicalPhysician(models.Model):
    _inherit = 'oeh.medical.physician'

    formatted_name = fields.Char(string="Formatted Name", compute="_compute_formatted_name", store=False)

    @api.depends('name')
    def _compute_formatted_name(self):
        for physician in self:
            if not physician.name:
                physician.formatted_name = 'General Appointment'
            else:
                name = physician.name.strip()
                # Check if name already starts with Dr. or Doctor
                if name.lower().startswith('dr.') or name.lower().startswith('doctor '):
                    physician.formatted_name = name
                else:
                    physician.formatted_name = f'Dr. {name}'
