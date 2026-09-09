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

from odoo import api, fields, models, tools


class AppointmentReport(models.Model):
    _name = "oeh.medical.appointment.report"
    _description = "Appointment Analytics Report"
    _auto = False
    _rec_name = 'appointment_id'
    _order = 'appointment_date desc'

    appointment_id = fields.Many2one('oeh.medical.appointment', string='Appointment', readonly=True)
    appointment_date = fields.Datetime(string='Appointment Date', readonly=True)
    patient_id = fields.Many2one('oeh.medical.patient', string='Patient', readonly=True)
    doctor_id = fields.Many2one('oeh.medical.physician', string='Doctor', readonly=True)
    specialty_id = fields.Many2one('oeh.medical.speciality', string='Specialty', readonly=True)
    institution_id = fields.Many2one('oeh.medical.health.center', string='Institution', readonly=True)
    state = fields.Selection([
        ('Scheduled', 'Scheduled'),
        ('Completed', 'Completed'),
        ('Invoiced', 'Invoiced'),
        ('Cancelled', 'Cancelled'),
    ], string='Status', readonly=True)
    duration = fields.Float(string='Duration (Hours)', readonly=True)
    consultancy_price = fields.Integer(string='Consultation Fee', readonly=True)

    # Date fields for grouping
    appointment_year = fields.Char(string='Year', readonly=True)
    appointment_month = fields.Char(string='Month', readonly=True)
    appointment_day = fields.Char(string='Day', readonly=True)
    appointment_week = fields.Char(string='Week', readonly=True)

    # Count fields
    appointment_count = fields.Integer(string='# Appointments', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    a.id as id,
                    a.id as appointment_id,
                    a.appointment_date as appointment_date,
                    a.patient as patient_id,
                    a.doctor as doctor_id,
                    p.speciality as specialty_id,
                    a.institution as institution_id,
                    a.state as state,
                    a.duration as duration,
                    p.consultancy_price as consultancy_price,
                    TO_CHAR(a.appointment_date, 'YYYY') as appointment_year,
                    TO_CHAR(a.appointment_date, 'YYYY-MM') as appointment_month,
                    TO_CHAR(a.appointment_date, 'YYYY-MM-DD') as appointment_day,
                    TO_CHAR(a.appointment_date, 'YYYY-IW') as appointment_week,
                    1 as appointment_count
                FROM
                    oeh_medical_appointment a
                    LEFT JOIN oeh_medical_physician p ON (a.doctor = p.id)
            )
        """ % (self._table,)
        self.env.cr.execute(query)
