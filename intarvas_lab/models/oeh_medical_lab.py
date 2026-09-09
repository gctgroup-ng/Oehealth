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

from odoo import api, fields, models, _
import time
import datetime
from odoo.exceptions import UserError


# Lab Units Management
class intarvasLabTestUnits(models.Model):
    _name = 'oeh.medical.lab.units'
    _description = 'Lab Test Units'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Unit Name', size=25, required=True, tracking=True)
    code = fields.Char(string='Code', size=25, required=True, tracking=True)

    _sql_constraints = [('name_uniq', 'unique(name)', 'The Lab unit name must be unique')]


# Lab Test Department
class intarvasLabTestDepartment(models.Model):
    _name = 'oeh.medical.labtest.department'
    _description = 'Lab Test Departments'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', size=128, required=True, tracking=True)


# Lab Test Types Management
class intarvasLabTestCriteria(models.Model):
    _name = 'oeh.medical.labtest.criteria'
    _description = 'Lab Test Criteria'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Tests', size=128, required=True)
    normal_range = fields.Text(string='Normal Range')
    units = fields.Many2one('oeh.medical.lab.units', string='Units')
    sequence = fields.Integer(string='Sequence')
    medical_type_id = fields.Many2one('oeh.medical.labtest.types', string='Lab Test Types')

    _order = "sequence"


class intarvasLabTestTypes(models.Model):
    _name = 'oeh.medical.labtest.types'
    _description = 'Lab Test Types'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    units = fields.Many2one('oeh.medical.lab.units', string='Units')
    normal_range = fields.Text(string='Normal Range')
    sequence = fields.Integer(string='Sequence')
    name = fields.Char(string='Lab Test Name', size=128, required=True, help="Test type, eg X-Ray, Hemogram, Biopsy...")
    code = fields.Char(string='Code', size=128, help="Short code for the test")
    info = fields.Text(string='Description')
    test_charge = fields.Float(string='Test Charge', default=lambda *a: 0.0)
    lab_criteria = fields.One2many('oeh.medical.labtest.criteria', 'medical_type_id', string='Lab Test Cases')
    lab_department = fields.Many2one('oeh.medical.labtest.department', string='Department')
    currency_id = fields.Many2one('res.currency',
                                  default=lambda self: self.env.user.company_id.currency_id)


class intarvasLabTests(models.Model):
    _name = 'oeh.medical.lab.test'
    _description = 'Lab Tests'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    LABTEST_STATE = [
        ('Draft', 'Draft'),
        ('Test In Progress', 'Test In Progress'),
        ('Completed', 'Completed'),
    ]

    display_type = fields.Selection([
        ('line_section', 'Section'),
        ('line_note', 'Note')
        ,
    ], default=False, help="Technical field for UX purpose.")

    units = fields.Many2one('oeh.medical.lab.units', string='Units')
    normal_range = fields.Text(string='Normal Range')
    result = fields.Text(string='Result')
    sequence = fields.Integer(string='Sequence')
    seq = fields.Integer(string='Sequence')
    code = fields.Char(string='Code', size=128, help="Short code for the test")
    name = fields.Char(string='Lab Test #', size=16, readonly=True, required=True, help="Lab result ID",
                       default=lambda *a: '/')
    lab_request = fields.Many2one('oeh.medical.lab.request', string='Lab Requested')
    patient = fields.Many2one('oeh.medical.patient', string='Patient', help="Patient Name", required=True)
    pathologist = fields.Many2one('oeh.medical.physician', string='Pathologist', help="Pathologist")
    requestor = fields.Char(string='Doctor who requested the test', help="Doctor who requested the test")
    requestor_id = fields.Many2one('oeh.medical.physician', string='Doctor who requested the test', domain=[('staff_type', '=', 'doctor')],
                                                         help="Doctor who requested the test")
    results = fields.Text(string='Results')
    diagnosis = fields.Text(string='Diagnosis')
    lab_test_criteria = fields.One2many('oeh.medical.lab.resultcriteria', 'medical_lab_test_id', string='Lab Test Result')
    date_requested = fields.Datetime(string='Date requested', default=lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'))
    date_analysis = fields.Datetime(string='Date of the Analysis')
    state = fields.Selection(LABTEST_STATE, string='State', readonly=True, default=lambda *a: 'Draft')
    institution = fields.Many2one('oeh.medical.health.center', string='Health Center', help="Medical Center",
                                  readonly=True, states={'Draft': [('readonly', False)]})
    appointment = fields.Many2one('oeh.medical.appointment', string='Appointment #')
    move_id = fields.Many2one('account.move', string='Invoice #')
    invoice_payment_state = fields.Selection(related='move_id.payment_state', string='Payment Status', readonly=True)
    invoice_amount_total = fields.Monetary(related='move_id.amount_total', string='Invoice Total', readonly=True, currency_field='invoice_currency_id')
    invoice_amount_residual = fields.Monetary(related='move_id.amount_residual', string='Amount Due', readonly=True, currency_field='invoice_currency_id')
    invoice_state = fields.Selection(related='move_id.state', string='Invoice State', readonly=True)
    invoice_currency_id = fields.Many2one(related='move_id.currency_id', string='Invoice Currency', readonly=True)
    lab_technician_id = fields.Many2one('oeh.medical.physician', domain="[('staff_type', '=', 'lab_technician')]",
                                        string="Lab Technician")
    lab_test_type_ids = fields.Many2many('oeh.medical.labtest.types')
    
    #Add Phlebotomist field
    phlebotomist = fields.Many2one('oeh.medical.physician', string='Phlebotomist', help="Phlebotomist", domain=[('staff_type','=','lab_technician')])

    #Add Pathologist field
    pathologist = fields.Many2one('oeh.medical.physician', string='Pathologist', help="Pathologist who reviews and interprets lab results", domain=[('staff_type','=','doctor')])

    company_id = fields.Many2one('res.company', string='Company', related='institution.company_id', store=True)

    def create(self, vals):
        if isinstance(vals, list):
            for val in vals:
                sequence = self.env['ir.sequence'].next_by_code('oeh.medical.lab.test')
                val['name'] = sequence or '/'
        else:
            sequence = self.env['ir.sequence'].next_by_code('oeh.medical.lab.test')
            vals['name'] = sequence or '/'
        return super(intarvasLabTests, self).create(vals)

    # Fetching lab test types
    @api.onchange('lab_test_type_ids')
    def onchange_lab_test_type_ids(self):
        lab_test_criteria = []
        if self.lab_test_type_ids:
            self.lab_test_criteria = False
            sequence_count = 0
            for lab_test in self.lab_test_type_ids:
                if lab_test.lab_criteria:
                    seq_lab = 0
                    lab_test_criteria.append((0, 0, {
                        'name': lab_test.name,
                        'display_type': 'line_section',
                        'sequence': sequence_count,
                    }))
                    for criteria in lab_test.lab_criteria:
                        sequence_count += 1
                        seq_lab += 1
                        lab_test_criteria.append((0, 0, {
                            'name': criteria.name,
                            'normal_range': criteria.normal_range,
                            'units': criteria.units and criteria.units.id or False,
                            'sequence': sequence_count,
                            'seq': seq_lab
                        }))
            self.lab_test_criteria = lab_test_criteria
        else:
            self.lab_test_criteria = False

    # This function prints the lab test
    def print_patient_labtest(self):
        return self.env.ref('intarvas_lab.action_report_patient_labtest').report_action(self)

    def set_to_test_inprogress(self):
        return self.write({'state': 'Test In Progress', 'date_analysis': datetime.datetime.now()})

    def set_to_test_complete(self):
        return self.write({'state': 'Completed'})

    def unlink(self):
        for labtest in self.filtered(lambda labtest: labtest.state not in ['Draft']):
            raise UserError(_('You can not delete a lab test which is not in "Draft" state !!'))
        return super(intarvasLabTests, self).unlink()

    def _get_default_journal(self):
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        return journal

    def action_lab_invoice_create(self):
        res = {}
        for lab in self:
            # Create Invoice
            if lab.patient:
                invoice_lines = []
                default_journal = self._get_default_journal()

                if not default_journal:
                    raise UserError(_('No accounting journal with type "Sale" defined !'))

                sequence_count = 1
                invoice_lines.append((0, 0, {
                    'name': 'Lab Test',
                    'display_type': 'line_section',
                    'account_id': False,
                    'sequence': sequence_count,
                }))

                sequence_count += 1

                invoice_lines.append((0, 0, {
                    'display_type': 'product',
                    'name': lab.test_type.name,
                    'price_unit': lab.test_type.test_charge,
                    'quantity': 1,
                    'product_uom_id': self.env.ref('uom.product_uom_unit') and self.env.ref(
                        'uom.product_uom_unit').id or False,
                    'sequence': sequence_count,
                }))

                invoice = self.env['account.move'].sudo().create({
                    'move_type': 'out_invoice',
                    'journal_id': default_journal.id,
                    'partner_id': lab.patient.partner_id.id,
                    'patient': lab.patient.id,
                    'invoice_date': datetime.datetime.now().date(),
                    'date': datetime.datetime.now().date(),
                    'ref': "Lab Test # : " + lab.name,
                    'labtest': lab.id,
                    'invoice_line_ids': invoice_lines
                })
                if self.env.company.stock_deduction_method == 'invoice_create':
                    invoice.oeh_process_inventories()
                # res = lab.write({'state': 'Invoiced', 'move_id': invoice.id})
        return res

    def action_view_invoice(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        if self.move_id:
            action['res_id'] = self.move_id.id
            action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
            action['context'] = dict(self._context, default_partner_id=self.patient and self.patient.partner_id.id or False, default_patient=self.patient and self.patient.id or False)
        return action


class intarvasLabTestsResultCriteria(models.Model):
    _name = 'oeh.medical.lab.resultcriteria'
    _description = 'Lab Test Result Criteria'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Tests', size=128, required=True)
    result = fields.Text(string='Result')
    normal_range = fields.Text(string='Normal Range')
    units = fields.Many2one('oeh.medical.lab.units', string='Units')
    sequence = fields.Integer(string='Sequence')
    seq = fields.Integer(string='Sequence')
    # sec_name = fields.Text()
    display_type = fields.Selection([
        ('line_section', 'Section'),
        ('line_note', 'Note')
        ,
    ], default=False, help="Technical field for UX purpose.")
    medical_lab_test_id = fields.Many2one('oeh.medical.lab.test', string='Lab Tests')

    _order = "sequence"


# Inheriting Patient module to add "Lab" screen reference
class intarvasPatient(models.Model):
    _inherit = 'oeh.medical.patient'

    def _labtest_count(self):
        for ls in self:
            ls.labs_count = self.env['oeh.medical.lab.test'].sudo().search_count([('patient', '=', ls.id)])

    lab_test_ids = fields.One2many('oeh.medical.lab.test', 'patient', string='Lab Test IDs')
    labs_count = fields.Integer(compute=_labtest_count, string="Lab Tests")


class AccountMoveLab(models.Model):
    _inherit = 'account.move'

    labtest_id = fields.Many2one('oeh.medical.lab.request', string="Lab Request #")


class intarvasAppointmentLab(models.Model):
    _inherit = 'oeh.medical.appointment'

    labtest_line = fields.One2many('oeh.medical.lab.test', 'appointment', string='Lab Test Lines',
                                   readonly=False, )
    medical_lab_request_ids = fields.One2many('oeh.medical.lab.request', 'appointment', string='Lab Requests')
    lab_test_request_ids = fields.Many2many(
        'oeh.medical.labtest.types', 
        string='Tests Requested'
    )

    def write(self, vals):
        # Fix many2many save issue
        if 'lab_test_request_ids' in vals:
            lab_commands = vals['lab_test_request_ids']
            
            # Handle command [6, false, [ids]] properly
            if isinstance(lab_commands, list):
                for command in lab_commands:
                    if isinstance(command, list) and len(command) == 3 and command[0] == 6:
                        ids_list = command[2]
                        # Ensure proper format
                        vals['lab_test_request_ids'] = [(6, 0, ids_list)]
                        break
        
        return super().write(vals)

    # def get_appointment_items_invoice_lines(self, with_consultancy=False):
    #     invoice_lines = super(intarvasAppointmentLab, self).get_appointment_items_invoice_lines(with_consultancy=with_consultancy)
    #     for acc in self:
    #         sequence = 0
    #
    #         if with_consultancy:
    #             consultancy_invoice_lines = acc.get_consultation_invoice_lines()
    #             invoice_lines.extend(consultancy_invoice_lines)
    #             sequence = 2
    #
    #         # Create Invoice lines for Labs
    #         if acc.labtest_line:
    #             sequence += 1
    #             invoice_lines.append((0, 0, {
    #                 'name': 'Lab Tests',
    #                 'display_type': 'line_section',
    #                 'account_id': False,
    #                 'sequence': sequence,
    #             }))
    #
    #             for lab in acc.labtest_line:
    #                 lab_test_name = lab.name
    #
    #                 invoice_lines.append((0, 0, {
    #                     'display_type': 'line_section',
    #                     'name': lab_test_name,
    #                     'quantity': 1,
    #                     'product_uom_id': self.env.ref('uom.product_uom_unit') and self.env.ref(
    #                         'uom.product_uom_unit').id or False,
    #                     'sequence': sequence,
    #                 }))
    #     return invoice_lines


class intarvasPhysician(models.Model):
    _inherit = 'oeh.medical.physician'

    staff_type = fields.Selection(selection_add=[('lab_technician', 'Lab Technician')])

    def _lab_tests_count(self):
        for ls in self:
            ls.lab_test = self.env['oeh.medical.lab.test'].sudo().search_count([('lab_technician_id', '=', ls.id)])

    lab_test = fields.Integer(compute=_lab_tests_count, string='Lab Tests')


class intarvasLabRequest(models.Model):
    _name = 'oeh.medical.lab.request'
    _description = 'Lab Requests'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    # _rec_name = 'patient'

    LABREQUEST_STATE = [
        ('Draft', 'Draft'),
        ('Sample Taken', 'Sample Taken'),
        ('Invoiced', 'Invoiced'),
        ('Pushed For Testing', 'Pushed For Testing'),
    ]

    samples_ids = fields.Many2many('oeh.medical.labtest.types')
    comments = fields.Text(string='Comments')
    sample_type = fields.Many2one('oeh.medical.sample.types', string='Sample Type')
    test_charge = fields.Float(string='Test Charge', default=lambda *a: 0.0)
    code = fields.Char(string='Code', size=25)
    name = fields.Char(string='Lab Request #', size=16, readonly=True, required=True, help="Lab Request ID",
                       default=lambda *a: '/')
    patient = fields.Many2one('oeh.medical.patient', string='Patient', help="Patient Name", required=True)

    institution = fields.Many2one('oeh.medical.health.center', string='Health Center', help="Medical Center")

    date_requested = fields.Datetime(string='Date requested',
                                     default=lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'))

    requested_by = fields.Char(string='Doctor who requested the test', help="Doctor who requested the test")
    #requestor = fields.Many2one('oeh.medical.physician', string='Doctor who requested the test', domain=[('staff_type', '=', 'doctor')], help="Doctor who requested the test")
    state = fields.Selection(LABREQUEST_STATE, string='State', readonly=True, default=lambda *a: 'Draft')
    lab_test_ids = fields.Many2many('oeh.medical.labtest.types', 'lab_test_types', string='Lab Test types')
    lab_sample_ids = fields.One2many('oeh.medical.lab.samples', 'sample_id', string="Samples")
    total = fields.Float(string='Total', store=True, compute='_amount_total', readonly=True)
    invoice_count = fields.Integer(string="Invoices")
    chief_complaint = fields.Text(string='Chief Complaint')
    currency_id = fields.Many2one('res.currency',
                                  default=lambda self: self.env.user.company_id.currency_id)
    product_id = fields.Many2one("product.product", "Product")
    pricelist_id = fields.Many2one('product.pricelist', string="Pricelist")
    appointment = fields.Many2one("oeh.medical.appointment", "Appointment")
    move_id = fields.Many2one('account.move', string='Invoice')
    invoice_payment_state = fields.Selection(related='move_id.payment_state', string='Payment Status', readonly=True)
    invoice_amount_total = fields.Monetary(related='move_id.amount_total', string='Invoice Total', readonly=True,
                                           currency_field='invoice_currency_id')
    invoice_amount_residual = fields.Monetary(related='move_id.amount_residual', string='Amount Due', readonly=True,
                                              currency_field='invoice_currency_id')
    invoice_state = fields.Selection(related='move_id.state', string='Invoice State', readonly=True)
    invoice_currency_id = fields.Many2one(related='move_id.currency_id', string='Invoice Currency', readonly=True)

    @api.onchange('patient')
    def onchange_patient(self):
        self.currency_id = self.env.user.company_id.currency_id

    @api.onchange('institution')
    def compute_currency(self):
        comp = self.institution.company_id.currency_id
        self.currency_id = comp
        for i in self.lab_test_ids:
            i.currency_id = comp

    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('oeh.medical.lab.request')
        vals['name'] = sequence or '/'
        return super(intarvasLabRequest, self).create(vals)

    @api.depends('lab_test_ids')
    def _amount_total(self):
        total = 0.0
        for line in self.lab_test_ids:
            total += line.test_charge
            self.total = total

    @api.onchange('lab_test_ids')
    def onchange_lab_test_ids(self):
        currency = self.env.user.company_id.currency_id
        if self.institution:
            comp = self.institution.company_id.currency_id
            for i in self.lab_test_ids:
                i.currency_id = comp
        else:
            for i in self.lab_test_ids:
                i.currency_id = currency

    def add_sample(self):
        return {
            'name': _('Add Sample'),
            'type': 'ir.actions.act_window',
            'res_model': 'oeh.medical.samples.wizard',
            'view_mode': 'form',
            'target': 'new',
            'domain': [('samples_ids', 'in', self.lab_test_ids.ids)],
            'context': {
                'default_samples_ids': self.lab_test_ids.ids
            }
        }

    def finished_sample(self):
        return self.write({'state': 'Sample Taken'})

    def _get_default_journal(self):
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        return journal

    def create_invoice(self):
        for lab in self:
            # Create Invoice
            invoice_lines = []
            default_journal = self._get_default_journal()

            if not default_journal:
                raise UserError(_('No accounting journal with type "Sale" defined !'))

            sequence_count = 1
            invoice_lines.append((0, 0, {
                'name': 'Lab Tests',
                'display_type': 'line_section',
                'account_id': False,
                'sequence': sequence_count,
            }))

            sequence_count += 1

            for i in lab.lab_test_ids:
                if lab.pricelist_id and lab.product_id:
                    price_unit = lab.pricelist_id._get_product_price(
                        product=lab.product_id,
                        quantity=1,
                        currency=self.env.company.currency_id,
                        date=lab.date_requested
                    )
                    #print(price_unit)
                else:
                    price_unit = i.test_charge
                lab_test_name = i.name
                #price_unit = i.test_charge
                invoice_lines.append((0, 0, {
                    'display_type': 'product',
                    'name': lab_test_name,
                    'price_unit': price_unit,
                    'quantity': 1,
                    'product_uom_id': self.env.ref('uom.product_uom_unit') and self.env.ref(
                        'uom.product_uom_unit').id or False,
                    'sequence': sequence_count,
                }))

            invoice = self.env['account.move'].sudo().create({
                'move_type': 'out_invoice',
                'journal_id': default_journal.id,
                'partner_id': lab.patient.partner_id.id,
                'patient': lab.patient.id,
                'invoice_date': datetime.datetime.now().date(),
                'date': datetime.datetime.now().date(),
                # 'ref': "Lab Test # : " + lab.name,
                'labtest_id': lab.id,
                'invoice_line_ids': invoice_lines
            })
            if self.env.company.stock_deduction_method == 'invoice_create':
                invoice.oeh_process_inventories()
            # res = lab.write({'state': 'Invoiced', 'move_id': invoice.id})
            lab.write({'state': 'Invoiced', 'move_id': invoice.id})
        return True

    def push_for_testing(self):
        for lab_request in self:
            action = self.env["ir.actions.actions"]._for_xml_id("intarvas_lab.oeh_medical_lab_test_action_tree")
            test_name = []
            if lab_request.lab_test_ids:
                sequence_count = 0
                for test in lab_request.lab_test_ids:
                    seq_lab = 0
                    test_name.append((0, 0, {
                        'name': test.name,
                        'display_type': 'line_section',
                        'sequence': sequence_count,
                    }))

                    if test.lab_criteria:
                        for criteria in test.lab_criteria:
                            sequence_count += 1
                            seq_lab += 1
                            test_name.append((0, 0, {
                                'name': criteria.name,
                                'normal_range': criteria.normal_range,
                                'units': criteria.units and criteria.units.id or False,
                                'sequence': sequence_count,
                                'seq': seq_lab
                            }))

            action['context'] = {
                'default_institution': lab_request.institution and lab_request.institution.id or False,
                'default_patient': lab_request.patient.id,
                'default_date_requested': lab_request.date_requested,
                'default_requestor': lab_request.requested_by or '',
                'default_lab_request': lab_request.id,
                'default_lab_test_type_ids': [(6, 0, lab_request.lab_test_ids.ids)],
                'default_lab_test_criteria': test_name
            }
            action['views'] = [(self.env.ref('intarvas_lab.oeh_medical_lab_test_form').id, 'form')]
            lab_request.write({'state': 'Pushed For Testing'})

        return action

    def action_view_invoice(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        if self.move_id:
            action['res_id'] = self.move_id.id
            action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
            action['context'] = dict(self._context, default_partner_id=self.patient and self.patient.partner_id.id or False, default_patient=self.patient and self.patient.id or False)
        return action


class intarvasSampleType(models.Model):
    _name = "oeh.medical.sample.types"
    _description = "Lab Sample Types "
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Sample Types', size=256, required=True)


class intarvasSamples(models.Model):
    _name = "oeh.medical.lab.samples"
    _description = "Lab Samples"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    comments = fields.Text(string='Comments')
    samples_ids = fields.Many2many('oeh.medical.labtest.types')
    sample_type = fields.Many2one('oeh.medical.sample.types', required=True, string='Sample Type')
    sample_id = fields.Many2one('oeh.medical.lab.request')