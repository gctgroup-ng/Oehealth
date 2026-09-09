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


class AppointmentWaitTimeReport(models.Model):
    _name = "oeh.medical.appointment.wait.time.report"
    _description = "Appointment Wait Time & Duration Analysis"
    _auto = False
    _rec_name = 'doctor_id'
    _order = 'appointment_date desc'

    doctor_id = fields.Many2one('oeh.medical.physician', string='Doctor', readonly=True)
    specialty_id = fields.Many2one('oeh.medical.speciality', string='Specialty', readonly=True)
    institution_id = fields.Many2one('oeh.medical.health.center', string='Institution', readonly=True)
    appointment_date = fields.Datetime(string='Appointment Date', readonly=True)
    time_of_day = fields.Selection([
        ('morning', 'Morning (6am-12pm)'),
        ('afternoon', 'Afternoon (12pm-6pm)'),
        ('evening', 'Evening (6pm-12am)'),
        ('night', 'Night (12am-6am)'),
    ], string='Time of Day', readonly=True)

    # Duration metrics
    avg_duration = fields.Float(string='Avg Duration (Hours)', readonly=True)
    min_duration = fields.Float(string='Min Duration (Hours)', readonly=True)
    max_duration = fields.Float(string='Max Duration (Hours)', readonly=True)
    total_duration = fields.Float(string='Total Duration (Hours)', readonly=True)

    # Efficiency metrics
    appointment_count = fields.Integer(string='# Appointments', readonly=True)
    completed_count = fields.Integer(string='# Completed', readonly=True)
    cancelled_count = fields.Integer(string='# Cancelled', readonly=True)
    efficiency_score = fields.Float(string='Efficiency Score (%)', readonly=True)

    # Date fields for grouping
    appointment_year = fields.Char(string='Year', readonly=True)
    appointment_month = fields.Char(string='Month', readonly=True)
    appointment_week = fields.Char(string='Week', readonly=True)
    appointment_day_of_week = fields.Char(string='Day of Week', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    ROW_NUMBER() OVER (
                        ORDER BY a.doctor,
                        TO_CHAR(a.appointment_date, 'YYYY-MM'),
                        EXTRACT(HOUR FROM a.appointment_date)
                    ) as id,
                    a.doctor as doctor_id,
                    p.speciality as specialty_id,
                    a.institution as institution_id,
                    a.appointment_date as appointment_date,
                    CASE
                        WHEN EXTRACT(HOUR FROM a.appointment_date) >= 6
                             AND EXTRACT(HOUR FROM a.appointment_date) < 12 THEN 'morning'
                        WHEN EXTRACT(HOUR FROM a.appointment_date) >= 12
                             AND EXTRACT(HOUR FROM a.appointment_date) < 18 THEN 'afternoon'
                        WHEN EXTRACT(HOUR FROM a.appointment_date) >= 18
                             AND EXTRACT(HOUR FROM a.appointment_date) < 24 THEN 'evening'
                        ELSE 'night'
                    END as time_of_day,
                    AVG(a.duration) as avg_duration,
                    MIN(a.duration) as min_duration,
                    MAX(a.duration) as max_duration,
                    SUM(a.duration) as total_duration,
                    COUNT(a.id) as appointment_count,
                    COUNT(CASE WHEN a.state = 'Completed' THEN 1 END) as completed_count,
                    COUNT(CASE WHEN a.state = 'Cancelled' THEN 1 END) as cancelled_count,
                    CASE
                        WHEN COUNT(a.id) > 0 THEN
                            (COUNT(CASE WHEN a.state = 'Completed' THEN 1 END)::float / COUNT(a.id)::float * 100)
                        ELSE 0
                    END as efficiency_score,
                    TO_CHAR(a.appointment_date, 'YYYY') as appointment_year,
                    TO_CHAR(a.appointment_date, 'YYYY-MM') as appointment_month,
                    TO_CHAR(a.appointment_date, 'YYYY-IW') as appointment_week,
                    TO_CHAR(a.appointment_date, 'Day') as appointment_day_of_week
                FROM
                    oeh_medical_appointment a
                    LEFT JOIN oeh_medical_physician p ON (a.doctor = p.id)
                GROUP BY
                    a.doctor, p.speciality, a.institution, a.appointment_date
            )
        """ % (self._table,)
        self.env.cr.execute(query)
