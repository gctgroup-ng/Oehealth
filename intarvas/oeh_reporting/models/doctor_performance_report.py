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


class DoctorPerformanceReport(models.Model):
    _name = "oeh.medical.doctor.performance.report"
    _description = "Doctor Performance Report"
    _auto = False
    _rec_name = 'doctor_id'
    _order = 'total_appointments desc'

    doctor_id = fields.Many2one('oeh.medical.physician', string='Doctor', readonly=True)
    doctor_name = fields.Char(string='Doctor Name', readonly=True)
    specialty_id = fields.Many2one('oeh.medical.speciality', string='Specialty', readonly=True)
    institution_id = fields.Many2one('oeh.medical.health.center', string='Institution', readonly=True)

    # Performance metrics
    total_appointments = fields.Integer(string='Total Appointments', readonly=True)
    scheduled_appointments = fields.Integer(string='Scheduled', readonly=True)
    completed_appointments = fields.Integer(string='Completed', readonly=True)
    cancelled_appointments = fields.Integer(string='Cancelled', readonly=True)
    completion_rate = fields.Float(string='Completion Rate (%)', readonly=True)
    avg_duration = fields.Float(string='Avg Duration (Hours)', readonly=True)
    total_consultancy_price = fields.Integer(string='Total Consultation Fees', readonly=True)
    total_prescriptions = fields.Integer(string='Total Prescriptions', readonly=True)

    # Date fields for grouping
    period_year = fields.Char(string='Year', readonly=True)
    period_month = fields.Char(string='Month', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    ROW_NUMBER() OVER (ORDER BY p.id, TO_CHAR(a.appointment_date, 'YYYY-MM')) as id,
                    p.id as doctor_id,
                    e.name as doctor_name,
                    p.speciality as specialty_id,
                    p.institution as institution_id,
                    COUNT(a.id) as total_appointments,
                    COUNT(CASE WHEN a.state = 'Scheduled' THEN 1 END) as scheduled_appointments,
                    COUNT(CASE WHEN a.state = 'Completed' THEN 1 END) as completed_appointments,
                    COUNT(CASE WHEN a.state = 'Cancelled' THEN 1 END) as cancelled_appointments,
                    CASE
                        WHEN COUNT(a.id) > 0 THEN
                            (COUNT(CASE WHEN a.state = 'Completed' THEN 1 END)::float / COUNT(a.id)::float * 100)
                        ELSE 0
                    END as completion_rate,
                    AVG(a.duration) as avg_duration,
                    SUM(COALESCE(p.consultancy_price, 0)) as total_consultancy_price,
                    (SELECT COUNT(*) FROM oeh_medical_prescription WHERE doctor = p.id) as total_prescriptions,
                    TO_CHAR(a.appointment_date, 'YYYY') as period_year,
                    TO_CHAR(a.appointment_date, 'YYYY-MM') as period_month
                FROM
                    oeh_medical_physician p
                    LEFT JOIN hr_employee e ON (p.employee_id = e.id)
                    LEFT JOIN oeh_medical_appointment a ON (p.id = a.doctor)
                GROUP BY
                    p.id, e.name, p.speciality, p.institution,
                    TO_CHAR(a.appointment_date, 'YYYY'),
                    TO_CHAR(a.appointment_date, 'YYYY-MM')
            )
        """ % (self._table,)
        self.env.cr.execute(query)
