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

import logging
import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)


# Pharmacy Management

class intarvasPharmacy(models.Model):
    _name = 'oeh.medical.health.center.pharmacy'
    _description = "Information about the pharmacy"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits={
        'res.partner': 'partner_id',
    }

    STATES = [
        ('Draft', 'Draft'),
        ('Invoiced', 'Invoiced'),
    ]

    state = fields.Selection(STATES, string='State', readonly=True, default=lambda *a: 'Draft')
    amount_total = fields.Monetary(string='Total', store=True, help="The total amount.")
    doctor = fields.Many2one('oeh.medical.physician', string='Doctor', help="Current primary care / family doctor", domain=[('is_pharmacist','=',False)])
    patient = fields.Many2one('oeh.medical.patient', string='Patient', help="Patient Name")
    partner_id = fields.Many2one('res.partner', string='Related Partner', required=True, ondelete='cascade', help='Partner-related data of the hospitals')
    pharmacist_name = fields.Many2one('oeh.medical.physician', string='Pharmacist Name', domain=[('is_pharmacist','=',True)], required=True)
    institution = fields.Many2one('oeh.medical.health.center', string='Health Center')
    pharmacy_lines = fields.One2many('oeh.medical.health.center.pharmacy.line', 'pharmacy_id', string='Pharmacy Lines')
    info = fields.Text(string='Extra Information')

    def create(self, vals):
        vals["is_pharmacy"] = True
        vals["is_company"] = True
        pharmacy = super(intarvasPharmacy, self).create(vals)
        return pharmacy

    @api.onchange('state_id')
    def onchange_state(self):
        if self.state_id:
            self.country_id = self.state_id.country_id.id


class intarvasPharmacyLines(models.Model):
    _name = 'oeh.medical.health.center.pharmacy.line'
    _description = 'Pharmacy Lines'

    STATES = [
        ('Draft', 'Draft'),
        ('Invoiced', 'Invoiced'),
    ]

    @api.depends('prescription_lines.price_subtotal')
    def _amount_all(self):
        """
        Compute the total amounts of the Prescription lines.
        """
        for order in self:
            val = 0.0
            for line in order.prescription_lines:
                val += line.price_subtotal
            order.update({
                'amount_total': val,
            })

    price_unit = fields.Float(string='Unit Price', required=True, default=lambda *a: 0.0)
    actual_qty = fields.Integer(string='Actual Qty Given', help="Actual quantity given to the patient")
    qty = fields.Integer(string='Prescribed Qty', help="Quantity of units (eg, 2 capsules) of the medicament")
    indication = fields.Many2one('oeh.medical.pathology', string='Indication', help="Choose a disease for this medicament from the disease list. It can be an existing disease of the patient or a prophylactic.")
    name = fields.Many2one('oeh.medical.prescription', string='Prescription #', required=True, ondelete='cascade')
    patient = fields.Many2one('oeh.medical.patient', string='Patient', help="Patient Name", required=True)
    doctor = fields.Many2one('oeh.medical.physician', string='Doctor', help="Current primary care / family doctor", domain=[('is_pharmacist','=',False)])
    prescription_lines = fields.One2many('oeh.medical.health.center.pharmacy.prescription.line', 'prescription_id', string='Prescription Lines')
    pharmacy_id = fields.Many2one('oeh.medical.health.center.pharmacy', string='Pharmacy Reference')
    amount_total = fields.Monetary(compute=_amount_all, string='Total', store=True, help="The total amount.")
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', help="Pricelist for current prescription")
    currency_id = fields.Many2one(related='pricelist_id.currency_id', string="Currency", readonly=True)
    info = fields.Text(string='Extra Information')
    state = fields.Selection(STATES, string='State', readonly=True, default=lambda *a: 'Draft')
    price_subtotal = fields.Float(string='Subtotal', default=lambda *a: 0.0)

    # Fetching prescription lines values
    @api.onchange('name')
    def onchange_prescription_id(self):
        for rec in self:

            lines = [(5, 0, 0)]
            for line in rec.name.prescription_line:
                val = {
                    'name': line.name,
                    'indication': line.indication,
                    'price_unit': line.name.list_price,
                    'qty': line.qty,
                }
                lines.append((0, 0, val))
                rec.prescription_lines = lines

    def _get_default_journal(self):
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        return journal

    def action_prescription_invoice_create(self):
        invoice_lines = []
        for pres in self:
            # Create Invoice
            if pres.patient:
                if pres.prescription_lines:
                    sequence = 1
                    for ps in pres.prescription_lines:
                        # Create Invoice line
                        invoice_lines.append((0, 0, {
                            'display_type': 'product',
                            'name': ps.name.product_id.name,
                            'product_id': ps.name.product_id.id,
                            'price_unit': ps.price_unit,
                            'quantity': ps.actual_qty,
                            'sequence': sequence,
                            'product_uom_id': ps.name.product_id and ps.name.product_id.uom_id and ps.name.product_id.uom_id.id or self.env.ref(
                                'uom.product_uom_unit') and self.env.ref('uom.product_uom_unit').id or False,
                        }))
                        sequence = sequence + 1
                default_journal = self._get_default_journal()

                # Create Invoice
                invoice = self.env['account.move'].sudo().create({
                    'move_type': 'out_invoice',
                    'journal_id': default_journal.id,
                    'partner_id': pres.patient.partner_id.id,
                    'patient': pres.patient.id,
                    'invoice_date': datetime.datetime.now().date(),
                    'date': datetime.datetime.now().date(),
                    'ref': "Walk-In # : " + pres.name.name,
                    'invoice_line_ids': invoice_lines
                })
            else:
                raise UserError(_('No patient selected !!'))
        return self.write({'state': 'Invoiced'})

    def get_prescription_invoice_lines(self):
        invoice_lines = []
        for pres in self:
            if pres.prescription_lines:
                # Prepare Invoice lines
                invoice_lines.append((0, 0, {
                    'name': 'Medicines',
                    'display_type': 'line_section',
                    'account_id': False,
                    'sequence': 1,
                }))
                sequence = 2
                for ps in pres.prescription_lines:
                    price = ps.price_unit

                    invoice_lines.append((0, 0, {
                            'display_type': 'product',
                            'product_id': ps.name.product_id.id,
                            'quantity': ps.actual_qty,
                            'name': ps.name.product_id.name,
                            'price_unit': price,
                            'product_uom_id': ps.name.product_id.uom_id and ps.name.product_id.uom_id.id or self.env.ref('uom.product_uom_unit').id or False,
                            'sequence': sequence,
                        }))
                    sequence = sequence + 1
        return invoice_lines

    # Preventing deletion of a prescription which is not in draft state
    def unlink(self):
        for priscription in self.filtered(lambda priscription: priscription.state not in ['Draft']):
            raise UserError(_('You can not delete a prescription which is in "Invoiced" state !!'))
        return super(intarvasPharmacyLines, self).unlink()


class intarvasPharmacyMedicineLines(models.Model):
    _name = 'oeh.medical.health.center.pharmacy.prescription.line'
    _description = 'Pharmacy Medicine Lines'

    @api.depends('price_subtotal')
    def _amount_line(self):
        """
        Compute the total amounts of the Prescription lines.
        """
        for line in self:
            price = line.price_unit * line.actual_qty
            line.price_subtotal = price
        return True

    name = fields.Many2one('oeh.medical.medicines', string='Medicines', help="Prescribed Medicines", domain=[('medicament_type','=','Medicine')], required=True)
    indication = fields.Many2one('oeh.medical.pathology', string='Indication', help="Choose a disease for this medicament from the disease list. It can be an existing disease of the patient or a prophylactic.")
    qty = fields.Integer(string='Prescribed Qty', help="Quantity of units (eg, 2 capsules) of the medicament")
    actual_qty = fields.Integer(string='Actual Qty Given', help="Actual quantity given to the patient")
    prescription_id = fields.Many2one('oeh.medical.health.center.pharmacy.line', string='Pharmacy Prescription Reference')
    price_unit = fields.Float(string='Unit Price', required=True, default=lambda *a: 0.0)
    price_subtotal = fields.Float(compute=_amount_line, string='Subtotal', default=lambda *a: 0.0)

    # Autopopulate selected medicine values
    @api.onchange('name')
    def onchange_medicine_id(self):
        result = {}
        if self.name:
            med_obj = self.env['oeh.medical.medicines']
            med_price_ids1 = med_obj.search([('id', '=', self.name.id)])
            if med_price_ids1:
                self.price_unit = med_price_ids1.lst_price
        return result

    # Change subtotal pricing
    @api.onchange('actual_qty', 'price_unit')
    def onchange_qty_and_price(self):
        result = {}
        if self.actual_qty and self.price_unit:
            self.price_subtotal = self.price_unit * self.actual_qty
        return result



