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

import datetime
from odoo import fields, models, _
from odoo.exceptions import UserError


class intarvasAppointmentWizard(models.TransientModel):
    _name = "oeh.medical.appointment.invoice.wizard"
    _description = "Invoice Wizard for Appointment screen"

    INVOICE_TYPE = [
        ('1', 'Only for consultation'),
        ('2', 'Only for appointment items (e.g. Treatments, Prescriptions and Lab Tests)'),
        ('3', 'Both (consultation + appointment items)'),
    ]

    name = fields.Selection(INVOICE_TYPE, 'Choose Invoicing Type', default='1')

    def _get_default_journal(self):
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        return journal

    def create_invoice(self):
        appointments = self.env['oeh.medical.appointment'].browse(self._context.get('active_ids', []))
        invoice_type = self.name

        for acc in appointments:
            invoice_lines = []
            default_journal = self._get_default_journal()

            if not default_journal:
                raise UserError(_('No accounting journal with type "Sale" defined !'))

            # Create Invoice line
            if invoice_type == '1':  # If first option selected
                consultancy_invoice_lines = acc.get_consultation_invoice_lines()
                invoice_lines.extend(consultancy_invoice_lines)
            if invoice_type == '2':     # If second option selected
                items_invoice_lines = acc.get_appointment_items_invoice_lines()
                invoice_lines.extend(items_invoice_lines)
            if invoice_type == '3':     # If third option "Both (bed charges + consumed medicine)" selected
                items_invoice_lines = acc.get_consultation_invoice_lines()
                invoice_lines.extend(items_invoice_lines)

            # Create Invoice
            invoice = self.env['account.move'].sudo().create({
                'move_type': 'out_invoice',
                'journal_id': default_journal.id,
                'partner_id': acc.patient.partner_id.id,
                'patient': acc.patient.id,
                'invoice_date': datetime.datetime.now().date(),
                'date': datetime.datetime.now().date(),
                'ref': "Appointment # : " + acc.name,
                'appointment': acc.id,
                'invoice_line_ids': invoice_lines
            })
            if self.env.company.stock_deduction_method == 'invoice_create':
                invoice.oeh_process_inventories()
            acc.write({'state': 'Invoiced', 'move_id': invoice.id})
        return True
