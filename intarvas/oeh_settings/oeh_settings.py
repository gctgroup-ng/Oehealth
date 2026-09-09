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
from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _name = 'res.company'
    _inherit = 'res.company'

    PATIENT_NAME = [
        ('first_last', 'Firstname Lastname'),
        ('last_first', 'Lastname Firstname'),
        ('last_first_comma', 'Lastname, Firstname'),
    ]

    APPOINTMENT_TYPE = [
        ('Not on Weekly Schedule', 'Not on Weekly Schedule'),
        ('On Weekly Schedule', 'On Weekly Schedule'),
    ]

    INVOICE_CONTROL = [
        ('normal', 'Generate consultation invoice directly'),
        ('dynamic', 'Choose from different invoicing options'),
    ]

    STOCK_DEDUCTION = [
        ('invoice_create', 'On Creation of an Invoice'),
        ('invoice_post', 'On Posting of an Invoice'),
        ('invoice_paid', 'On Payment Completion'),
        ('none', 'No Stock Deduction'),
    ]

    FOLLOWUP_FEATURE = [
        ('on', 'Turned On'),
        ('off', 'Turned Off')
    ]

    INVOICING_FLOW = [
        ('before_consultation', 'Before Consultation'),
        ('after_consultation', 'After Consultation'),
    ]

    UNIT_SYSTEM = [
        ('metric', 'Metric (kg, cm, °C)'),
        ('imperial', 'Imperial (lbs, ft/in, °F)'),
    ]

    appointment_type = fields.Selection(APPOINTMENT_TYPE, string="Doctor's Availability", default='Not on Weekly Schedule')
    appointment_duration = fields.Float(string='Default Duration', default=0.5)
    appointment_invoice_control = fields.Selection(INVOICE_CONTROL, string="Invoicing Control", default='dynamic')
    appointment_invoicing_flow = fields.Selection(INVOICING_FLOW, string="Invoicing Flow", default='before_consultation')
    stock_deduction_method = fields.Selection(STOCK_DEDUCTION, string='Stock Deduction', default='invoice_paid')
    followup_feature = fields.Boolean(string="Turn On/Off Followup Feature", default=False)
    followup_appointment_duration = fields.Integer(string='Appointment Duration (Days)')
    followup_prescription_duration = fields.Integer(string='Prescription Duration (Days)')
    prescription_send_by_email = fields.Boolean(string='Allow to send Prescription by email?', default=True)
    patient_name_order = fields.Selection(PATIENT_NAME, string='Patient Name Display Preference', default='first_last')
    patient_account_password = fields.Char("Default Patient Account Password", default="Pa$$@32#")
    unit_system = fields.Selection(UNIT_SYSTEM, string='Medical Unit System', default='metric')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    appointment_type = fields.Selection(related='company_id.appointment_type', string="Doctor's Availability", readonly=False)
    appointment_duration = fields.Float(related='company_id.appointment_duration', string="Default Duration", readonly=False)
    appointment_invoice_control = fields.Selection(related='company_id.appointment_invoice_control',
                                                   string="Invoicing Control",
                                                   readonly=False)
    appointment_invoicing_flow = fields.Selection(related='company_id.appointment_invoicing_flow',
                                                  string="Invoicing Flow",
                                                  readonly=False)
    stock_deduction_method = fields.Selection(related='company_id.stock_deduction_method',
                                                   string="Stock Deduction",
                                                   readonly=False)
    followup_feature = fields.Boolean(related='company_id.followup_feature', string="Turn On/Off Followup Feature",
                                        readonly=False)
    followup_appointment_duration = fields.Integer(related='company_id.followup_appointment_duration', readonly=False)
    followup_prescription_duration = fields.Integer(related='company_id.followup_prescription_duration', readonly=False)
    prescription_send_by_email = fields.Boolean(related='company_id.prescription_send_by_email', string="Allow to send Prescription by email?", readonly=False)
    patient_name_order = fields.Selection(related='company_id.patient_name_order', string="Patient Name Display Preference", readonly=False)
    patient_account_password = fields.Char(related='company_id.patient_account_password',
                                               string="Default Patient Account Password",
                                               readonly=False,
                                               default_model='res.company')
    unit_system = fields.Selection(related='company_id.unit_system', string='Medical Unit System', readonly=False)

    def action_regenerate_patient_names(self):
        patients = self.env["oeh.medical.patient"].sudo().search([("firstname", "!=", False), ("lastname", "!=", False)])
        _logger.info("Regenerating names for %d patients.", len(patients))
        for patient in patients:
            patient.onchange_firstname_lastname()
        self.execute()
        _logger.info("%d patients updated.", len(patients))
        return True