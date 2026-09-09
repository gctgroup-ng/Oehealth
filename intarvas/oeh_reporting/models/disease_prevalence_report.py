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


class DiseasePrevalenceReport(models.Model):
    _name = "oeh.medical.disease.prevalence.report"
    _description = "Disease Prevalence Report"
    _auto = False
    _rec_name = 'pathology_id'
    _order = 'occurrence_count desc'

    pathology_id = fields.Many2one('oeh.medical.pathology', string='Disease', readonly=True)
    pathology_name = fields.Char(string='Disease Name', readonly=True)
    pathology_code = fields.Char(string='Code', readonly=True)
    category_id = fields.Many2one('oeh.medical.pathology.category', string='Category', readonly=True)

    # Occurrence metrics
    occurrence_count = fields.Integer(string='# Occurrences', readonly=True)
    patient_count = fields.Integer(string='# Patients', readonly=True)
    appointment_count = fields.Integer(string='# Appointments', readonly=True)
    prescription_count = fields.Integer(string='# Prescriptions', readonly=True)
    admission_count = fields.Integer(string='# Admissions', readonly=True)

    # Demographics
    male_count = fields.Integer(string='Male Patients', readonly=True)
    female_count = fields.Integer(string='Female Patients', readonly=True)
    avg_patient_age = fields.Float(string='Avg Patient Age', readonly=True)

    # Date fields for grouping
    period_year = fields.Char(string='Year', readonly=True)
    period_month = fields.Char(string='Month', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """
            CREATE OR REPLACE VIEW %s AS (
                WITH pathology_stats AS (
                    SELECT
                        p.id as pathology_id,
                        p.name as pathology_name,
                        p.code as pathology_code,
                        p.category as category_id,
                        COUNT(DISTINCT a.id) as appointment_count,
                        COUNT(DISTINCT pr.id) as prescription_count,
                        COUNT(DISTINCT i.id) as admission_count,
                        COUNT(DISTINCT a.patient) as patient_count,
                        COUNT(DISTINCT CASE WHEN pat.sex = 'Male' THEN pat.id END) as male_count,
                        COUNT(DISTINCT CASE WHEN pat.sex = 'Female' THEN pat.id END) as female_count,
                        AVG(EXTRACT(YEAR FROM AGE(COALESCE(pat.dod, CURRENT_DATE), pat.dob))) as avg_patient_age,
                        TO_CHAR(COALESCE(a.appointment_date, pr.date, i.admission_date), 'YYYY') as period_year,
                        TO_CHAR(COALESCE(a.appointment_date, pr.date, i.admission_date), 'YYYY-MM') as period_month
                    FROM
                        oeh_medical_pathology p
                        LEFT JOIN oeh_medical_appointment_complaints ac ON (p.id = ac.complaint_id)
                        LEFT JOIN oeh_medical_appointment a ON (ac.appointment_id = a.id)
                        LEFT JOIN oeh_medical_prescription pr ON (p.id = pr.indication)
                        LEFT JOIN oeh_medical_inpatient i ON (p.id = i.admission_reason)
                        LEFT JOIN oeh_medical_patient pat ON (
                            pat.id = COALESCE(a.patient, pr.patient, i.patient)
                        )
                    GROUP BY
                        p.id, p.name, p.code, p.category,
                        TO_CHAR(COALESCE(a.appointment_date, pr.date, i.admission_date), 'YYYY'),
                        TO_CHAR(COALESCE(a.appointment_date, pr.date, i.admission_date), 'YYYY-MM')
                )
                SELECT
                    ROW_NUMBER() OVER (ORDER BY pathology_id, period_month) as id,
                    pathology_id,
                    pathology_name,
                    pathology_code,
                    category_id,
                    (appointment_count + prescription_count + admission_count) as occurrence_count,
                    patient_count,
                    appointment_count,
                    prescription_count,
                    admission_count,
                    male_count,
                    female_count,
                    avg_patient_age,
                    period_year,
                    period_month
                FROM
                    pathology_stats
            )
        """ % (self._table,)
        self.env.cr.execute(query)
