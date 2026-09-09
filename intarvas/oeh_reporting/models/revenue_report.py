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


class RevenueReport(models.Model):
    _name = "oeh.medical.revenue.report"
    _description = "Revenue Analysis Report"
    _auto = False
    _rec_name = 'invoice_id'
    _order = 'invoice_date desc'

    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True)
    invoice_number = fields.Char(string='Invoice #', readonly=True)
    invoice_date = fields.Date(string='Invoice Date', readonly=True)
    patient_id = fields.Many2one('oeh.medical.patient', string='Patient', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    service_type = fields.Char(string='Service Type', readonly=True)
    amount_untaxed = fields.Monetary(string='Untaxed Amount', readonly=True, currency_field='currency_id')
    amount_tax = fields.Monetary(string='Tax', readonly=True, currency_field='currency_id')
    amount_total = fields.Monetary(string='Total', readonly=True, currency_field='currency_id')
    amount_residual = fields.Monetary(string='Amount Due', readonly=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True)
    payment_state = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('reversed', 'Reversed'),
        ('invoicing_legacy', 'Invoicing App Legacy'),
    ], string='Payment Status', readonly=True)

    # Date fields for grouping
    invoice_year = fields.Char(string='Year', readonly=True)
    invoice_month = fields.Char(string='Month', readonly=True)
    invoice_week = fields.Char(string='Week', readonly=True)

    # Count fields
    invoice_count = fields.Integer(string='# Invoices', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    am.id as id,
                    am.id as invoice_id,
                    am.name as invoice_number,
                    am.invoice_date as invoice_date,
                    am.patient as patient_id,
                    am.partner_id as partner_id,
                    CASE
                        WHEN EXISTS (SELECT 1 FROM oeh_medical_appointment WHERE move_id = am.id) THEN 'Appointment'
                        WHEN EXISTS (SELECT 1 FROM oeh_medical_inpatient WHERE move_id = am.id) THEN 'Inpatient'
                        ELSE 'Other'
                    END as service_type,
                    am.amount_untaxed as amount_untaxed,
                    am.amount_tax as amount_tax,
                    am.amount_total as amount_total,
                    am.amount_residual as amount_residual,
                    am.currency_id as currency_id,
                    am.state as state,
                    am.payment_state as payment_state,
                    TO_CHAR(am.invoice_date, 'YYYY') as invoice_year,
                    TO_CHAR(am.invoice_date, 'YYYY-MM') as invoice_month,
                    TO_CHAR(am.invoice_date, 'YYYY-IW') as invoice_week,
                    1 as invoice_count
                FROM
                    account_move am
                WHERE
                    am.move_type = 'out_invoice'
                    AND am.patient IS NOT NULL
            )
        """ % (self._table,)
        self.env.cr.execute(query)
