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
from odoo import models, fields, _
from datetime import datetime, timedelta


class OehMedicalFollowUp(models.Model):
    _name = 'oeh.medical.followup'
    _description = 'Patient Followup Details'

    FOLLOWUP_STATE = [
        ('scheduled', 'Scheduled'),
        ('done', 'Done')
    ]

    name = fields.Char('Name', readonly=False, tracking=True)
    patient = fields.Many2one('oeh.medical.patient', readonly=False, tracking=True)
    health_center = fields.Many2one('oeh.medical.health.center', tracking=True)
    source_followup = fields.Many2one('oeh.medical.followup', string='Followup Source', tracking=True)
    source_followup_bool = fields.Boolean('Source is Followup', tracking=True)
    source_appointment = fields.Many2one('oeh.medical.appointment', string='Appointment Source', tracking=True)
    source_appointment_bool = fields.Boolean('Source is Appointment', tracking=True)
    source_prescription = fields.Many2one('oeh.medical.prescription', string='Prescription Source', tracking=True)
    source_prescription_bool = fields.Boolean('Source is Prescription', tracking=True)
    state = fields.Selection(FOLLOWUP_STATE, default='scheduled', tracking=True)
    followup_date = fields.Datetime('Followup Date', default=datetime.now() + timedelta(days=5), readonly=False, tracking=True)
    fin_followup_datetime = fields.Datetime('Completed Followup Date & Time', readonly=False, tracking=True)
    notes = fields.Text('Notes', readonly=False, tracking=True)

    def set_to_done(self):
        return {
            'name': _('Follow-Up Wizard'),
            'type': 'ir.actions.act_window',
            'res_model': 'oeh.followup.wizard',
            'view_mode': 'form',
            'target': 'new'
        }