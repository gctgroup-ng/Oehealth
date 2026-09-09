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

from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    patient = fields.Many2one('oeh.medical.patient', string='Related Patient', help="Patient Name")
    appointment = fields.Many2one('oeh.medical.appointment', string="Appointment #")
    prescription = fields.Many2one('oeh.medical.prescription', string="Prescription #")
    inpatient = fields.Many2one('oeh.medical.inpatient', string="Inpatient Admission #")

    @api.model
    def get_default_location_id(self):
        company_user = self.env.user.company_id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_user.id)], limit=1)
        if warehouse:
            return warehouse.lot_stock_id.id
        else:
            raise UserError(_('You must define a warehouse for the company: %s.') % (company_user.name,))

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for move in self:
            if self.env.company.stock_deduction_method == 'invoice_post':
                move.oeh_process_inventories()
        return res

    def _compute_amount(self):
        # OVERRIDE
        res = super(AccountMove, self)._compute_amount()
        for move in self:
            if move.payment_state == 'paid' and self.env.company.stock_deduction_method == 'invoice_paid':
                move.oeh_process_inventories()
        return res

    def oeh_process_inventories(self):
        for move in self:
            location_id = self.get_default_location_id()
            if move.appointment:
                if move.appointment.prescription_line:
                    for pres_line in move.appointment.prescription_line:
                        if pres_line.prescription_line:
                            for line in pres_line.prescription_line:
                                if line.name.type == 'product':
                                    self.update_invoice_product_stock(line.name.product_id, location_id, line.qty)
                        pres_line.write({'state': 'Invoiced'})
                if move.appointment.treatment_line:
                    for treatment in move.appointment.treatment_line:
                        if treatment.treatment_items:
                            for treat_line in treatment.treatment_items:
                                if treat_line.name.type == 'product':
                                    self.update_invoice_product_stock(treat_line.name, location_id, treat_line.qty)
            if move.prescription:
                if move.prescription.prescription_line:
                    for pres_line in move.prescription.prescription_line:
                        if pres_line.name.type == 'product':
                            self.update_invoice_product_stock(pres_line.name.product_id, location_id, pres_line.qty)

        return True

    def update_invoice_product_stock(self, product_id, location_id, qty):
        Inventory = self.env['stock.change.product.qty']
        product = product_id.with_context(location=location_id)
        th_qty = product.qty_available
        new_qty = th_qty - qty

        if int(new_qty) < 0:
            new_qty = 0
        inventory = Inventory.create({
            'new_quantity': new_qty,
            'product_id': product_id.id,
            'product_tmpl_id': product_id.product_tmpl_id.id,
        })
        inventory.change_product_qty()
        return True
