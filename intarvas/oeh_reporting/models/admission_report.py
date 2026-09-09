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


class AdmissionReport(models.Model):
    _name = "oeh.medical.admission.report"
    _description = "Admission Analysis Report"
    _auto = False
    _rec_name = 'admission_id'
    _order = 'admission_date desc'

    admission_id = fields.Many2one('oeh.medical.inpatient', string='Admission', readonly=True)
    admission_number = fields.Char(string='Admission #', readonly=True)
    patient_id = fields.Many2one('oeh.medical.patient', string='Patient', readonly=True)
    admission_date = fields.Datetime(string='Admission Date', readonly=True)
    discharge_date = fields.Datetime(string='Discharge Date', readonly=True)
    admission_type = fields.Selection([
        ('Routine', 'Routine'),
        ('Maternity', 'Maternity'),
        ('Elective', 'Elective'),
        ('Urgent', 'Urgent'),
        ('Emergency', 'Emergency'),
        ('Other', 'Other'),
    ], string='Admission Type', readonly=True)
    admission_reason_id = fields.Many2one('oeh.medical.pathology', string='Reason', readonly=True)
    attending_physician_id = fields.Many2one('oeh.medical.physician', string='Attending Doctor', readonly=True)
    operating_physician_id = fields.Many2one('oeh.medical.physician', string='Operating Doctor', readonly=True)
    institution_id = fields.Many2one('oeh.medical.health.center', string='Institution', readonly=True)
    ward_id = fields.Many2one('oeh.medical.health.center.ward', string='Ward', readonly=True)
    bed_id = fields.Many2one('oeh.medical.health.center.beds', string='Bed', readonly=True)
    state = fields.Selection([
        ('Draft', 'Draft'),
        ('Hospitalized', 'Hospitalized'),
        ('Invoiced', 'Invoiced'),
        ('Discharged', 'Discharged'),
        ('Cancelled', 'Cancelled'),
    ], string='Status', readonly=True)
    stay_duration_days = fields.Float(string='Stay Duration (Days)', readonly=True)

    # Invoice related
    invoice_amount = fields.Monetary(string='Invoice Amount', readonly=True, currency_field='currency_id')
    invoice_state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
    ], string='Invoice Status', readonly=True)
    payment_state = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('reversed', 'Reversed'),
        ('invoicing_legacy', 'Invoicing App Legacy'),
    ], string='Payment Status', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)

    # Date fields for grouping
    admission_year = fields.Char(string='Year', readonly=True)
    admission_month = fields.Char(string='Month', readonly=True)
    admission_week = fields.Char(string='Week', readonly=True)

    # Count fields
    admission_count = fields.Integer(string='# Admissions', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    i.id as id,
                    i.id as admission_id,
                    i.name as admission_number,
                    i.patient as patient_id,
                    i.admission_date as admission_date,
                    i.discharge_date as discharge_date,
                    i.admission_type as admission_type,
                    i.admission_reason as admission_reason_id,
                    i.attending_physician as attending_physician_id,
                    i.operating_physician as operating_physician_id,
                    i.institution as institution_id,
                    i.ward as ward_id,
                    i.bed as bed_id,
                    i.state as state,
                    CASE
                        WHEN i.discharge_date IS NOT NULL AND i.admission_date IS NOT NULL
                        THEN EXTRACT(EPOCH FROM (i.discharge_date - i.admission_date)) / 86400
                        WHEN i.admission_date IS NOT NULL
                        THEN EXTRACT(EPOCH FROM (NOW() - i.admission_date)) / 86400
                        ELSE 0
                    END as stay_duration_days,
                    am.amount_total as invoice_amount,
                    am.state as invoice_state,
                    am.payment_state as payment_state,
                    am.currency_id as currency_id,
                    TO_CHAR(i.admission_date, 'YYYY') as admission_year,
                    TO_CHAR(i.admission_date, 'YYYY-MM') as admission_month,
                    TO_CHAR(i.admission_date, 'YYYY-IW') as admission_week,
                    1 as admission_count
                FROM
                    oeh_medical_inpatient i
                    LEFT JOIN account_move am ON (i.move_id = am.id)
            )
        """ % (self._table,)
        self.env.cr.execute(query)
