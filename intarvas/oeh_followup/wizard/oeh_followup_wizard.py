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

# -*- coding: utf-8 -*-
from odoo import fields, models, api
from datetime import datetime, timedelta


class FollowUpLabTestWizard(models.TransientModel):
    _name = 'oeh.followup.prescription.wizard'
    _description = 'Wizard for Prescription Follow-Up'

    @api.model
    def _get_default_followup_date(self):
        followup_days = self.env.company.followup_prescription_duration
        if followup_days > 0:
            return datetime.now() + timedelta(days=int(followup_days))
        else:
            return datetime.now() + timedelta(days=1)

    name = fields.Char('Name')
    patient = fields.Many2one('oeh.medical.patient')
    sources = fields.Char('Sources')
    followup_date = fields.Datetime('Followup Date', default=_get_default_followup_date)
    notes = fields.Text('Notes')
    schedule_followup = fields.Boolean('Schedule Follow-Up', default=True)
    prescription_bool = fields.Boolean(default=True)

    def save_prescription_data(self):
        prescriptions = self.env['oeh.medical.prescription'].browse(self._context.get('active_ids', []))
        if prescriptions:
            for pres in prescriptions:
                self.env['oeh.medical.followup'].create({
                    'name': self.name,
                    'followup_date': self.followup_date,
                    'notes': self.notes,
                    'patient': pres.patient.id,
                    'health_center': pres.institution and pres.institution.id or False,
                    'source_prescription': pres.id,
                    'source_followup_bool': False,
                    'source_prescription_bool': True,
                    'source_appointment_bool': False
                })


class FollowUpAppointmentWizard(models.TransientModel):
    _name = 'oeh.followup.appointment.wizard'
    _description = 'Wizard for Appointment Follow-Up'

    @api.model
    def _get_default_followup_date(self):
        followup_days = self.env.company.followup_appointment_duration
        if followup_days > 0:
            return datetime.now() + timedelta(days=int(followup_days))
        else:
            return datetime.now() + timedelta(days=1)

    name = fields.Char('Name')
    patient = fields.Many2one('oeh.medical.patient')
    followup_date = fields.Datetime('Followup Date', default=_get_default_followup_date)
    notes = fields.Text('Notes')
    schedule_followup = fields.Boolean('Schedule Follow-Up', default=True)

    def save_appointment_data(self):
        appointments = self.env['oeh.medical.appointment'].browse(self._context.get('active_ids',[]))

        if appointments:
            for app in appointments:
                # print(app.source_app)
                followup_obj = self.env['oeh.medical.followup']
                followup_obj.create({
                    'name': self.name,
                    'followup_date': self.followup_date,
                    'notes': self.notes,
                    'patient': app.patient.id,
                    'health_center': app.institution and app.institution.id or False,
                    'source_appointment': app.id,
                    'source_followup_bool': False,
                    'source_prescription_bool': False,
                    'source_appointment_bool': True
                })
                app.write({'state': 'Completed'})


class FollowUpWizard(models.TransientModel):
    _name = 'oeh.followup.wizard'
    _description = 'Wizard for Patient Follow-Up'

    @api.model
    def _get_default_followup_date(self):
        return datetime.now() + timedelta(days=5)

    schedule_followup = fields.Boolean('Schedule Follow-Up', default=True)
    name = fields.Char('Name')
    patient = fields.Many2one('oeh.medical.patient')
    sources = fields.Char('Sources')
    followup_date = fields.Datetime('Followup Date', default=_get_default_followup_date)

    def prev_notes(self):
        followups = self.env['oeh.medical.followup'].browse(self._context.get('active_ids', []))
        if followups:
            for test in followups:
                return test.notes

    notes = fields.Text('Notes', default=prev_notes)

    def save_followup_data(self):
        followups = self.env['oeh.medical.followup'].browse(self._context.get('active_ids',[]))
        if followups:
            followup_obj = self.env['oeh.medical.followup']
            for followup in followups:
                followup_obj.create({
                    'name': self.name,
                    'followup_date': self.followup_date,
                    'notes': self.notes,
                    'patient': followup.patient.id,
                    'health_center': followup.health_center and followup.health_center.id or False,
                    'source_followup': followup.id,
                    'source_followup_bool': True,
                    'source_prescription_bool': False,
                    'source_appointment_bool': False
                })
                followup.write({'state': 'done', 'fin_followup_datetime': datetime.now()})
