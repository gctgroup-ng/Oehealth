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


class PatientRegistrationReport(models.Model):
    _name = "oeh.medical.patient.registration.report"
    _description = "Patient Registration Analysis"
    _auto = False
    _rec_name = 'patient_id'
    _order = 'registration_date desc'

    patient_id = fields.Many2one('oeh.medical.patient', string='Patient', readonly=True)
    patient_name = fields.Char(string='Patient Name', readonly=True)
    registration_date = fields.Date(string='Registration Date', readonly=True)
    gender = fields.Selection([
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ], string='Gender', readonly=True)
    age = fields.Integer(string='Age', readonly=True)
    age_group = fields.Char(string='Age Group', readonly=True)
    blood_group = fields.Char(string='Blood Group', readonly=True)
    marital_status = fields.Selection([
        ('Single', 'Single'),
        ('Married', 'Married'),
        ('Widowed', 'Widowed'),
        ('Divorced', 'Divorced'),
        ('Separated', 'Separated'),
    ], string='Marital Status', readonly=True)
    ethnic_group_id = fields.Many2one('oeh.medical.ethnicity', string='Ethnic Group', readonly=True)
    has_insurance = fields.Boolean(string='Has Insurance', readonly=True)
    city = fields.Char(string='City', readonly=True)
    state_id = fields.Many2one('res.country.state', string='State', readonly=True)
    country_id = fields.Many2one('res.country', string='Country', readonly=True)

    # Date fields for grouping
    registration_year = fields.Char(string='Year', readonly=True)
    registration_month = fields.Char(string='Month', readonly=True)
    registration_week = fields.Char(string='Week', readonly=True)

    # Count fields
    patient_count = fields.Integer(string='# Patients', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    p.id as id,
                    p.id as patient_id,
                    rp.name as patient_name,
                    p.dob as registration_date,
                    p.sex as gender,
                    EXTRACT(YEAR FROM AGE(COALESCE(p.dod, CURRENT_DATE), p.dob))::integer as age,
                    CASE
                        WHEN EXTRACT(YEAR FROM AGE(COALESCE(p.dod, CURRENT_DATE), p.dob)) < 5 THEN '0-4'
                        WHEN EXTRACT(YEAR FROM AGE(COALESCE(p.dod, CURRENT_DATE), p.dob)) < 13 THEN '5-12'
                        WHEN EXTRACT(YEAR FROM AGE(COALESCE(p.dod, CURRENT_DATE), p.dob)) < 18 THEN '13-17'
                        WHEN EXTRACT(YEAR FROM AGE(COALESCE(p.dod, CURRENT_DATE), p.dob)) < 30 THEN '18-29'
                        WHEN EXTRACT(YEAR FROM AGE(COALESCE(p.dod, CURRENT_DATE), p.dob)) < 45 THEN '30-44'
                        WHEN EXTRACT(YEAR FROM AGE(COALESCE(p.dod, CURRENT_DATE), p.dob)) < 60 THEN '45-59'
                        ELSE '60+'
                    END as age_group,
                    p.blood_type as blood_group,
                    p.marital_status as marital_status,
                    p.ethnic_group as ethnic_group_id,
                    CASE WHEN p.current_insurance IS NOT NULL THEN TRUE ELSE FALSE END as has_insurance,
                    rp.city as city,
                    rp.state_id as state_id,
                    rp.country_id as country_id,
                    TO_CHAR(p.create_date, 'YYYY') as registration_year,
                    TO_CHAR(p.create_date, 'YYYY-MM') as registration_month,
                    TO_CHAR(p.create_date, 'YYYY-IW') as registration_week,
                    1 as patient_count
                FROM
                    oeh_medical_patient p
                    LEFT JOIN res_partner rp ON (p.partner_id = rp.id)
            )
        """ % (self._table,)
        self.env.cr.execute(query)
