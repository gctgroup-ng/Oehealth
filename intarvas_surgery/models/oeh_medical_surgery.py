# -*- encoding: utf-8 -*-
##############################################################################
#    Copyright (C) 2015 - Present, Intarvas (<https://www.intarvas.com>). All Rights Reserved
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

from odoo import fields, api, models, _
from odoo.exceptions import UserError
import calendar
import time
import datetime


class intarvasSurgeryRCRI(models.Model):
    _name = "oeh.medical.surgery.rcri"
    _description = "Revised Cardiac Risk Index"

    RCRI_CLASS = [
        ('I', 'I'),
        ('II', 'II'),
        ('III', 'III'),
        ('IV', 'IV'),
    ]

    def get_rcri_name(self):
        result = {}
        rcri_name = ''
        for rc in self:
            rcri_name = 'Points: ' + str(rc.rcri_total) + ' (Class ' + str(rc.rcri_class) + ')'
            rc.name = rcri_name
        return result

    name = fields.Char(compute=get_rcri_name, string="RCRI", size=64)
    patient = fields.Many2one('oeh.medical.patient', string='Patient', help="Patient Name", required=True)
    doctor = fields.Many2one('oeh.medical.physician', string='Doctor', domain=[('is_pharmacist', '=', False)],
                             help="Health professional / Cardiologist who signed the assesment RCRI")
    rcri_date = fields.Datetime('Date', required=True, default=lambda *a: datetime.datetime.now())
    rcri_high_risk_surgery = fields.Boolean(string='High Risk surgery',
                                            help='Includes andy suprainguinal vascular, intraperitoneal or intrathoracic procedures')
    rcri_ischemic_history = fields.Boolean(string='History of Ischemic heart disease',
                                           help='History of MI or a positive exercise test, current complaint of chest pain considered to be secondary to myocardial ischemia, use of nitrate therapy, or ECG with pathological Q waves; do not count prior coronary revascularization procedure unless one of the other criteria for ischemic heart disease is present"')
    rcri_congestive_history = fields.Boolean(string='History of Congestive heart disease')
    rcri_diabetes_history = fields.Boolean(string='Preoperative Diabetes',
                                           help="Diabetes Mellitus requiring treatment with Insulin")
    rcri_cerebrovascular_history = fields.Boolean(string='History of Cerebrovascular disease')
    rcri_kidney_history = fields.Boolean(string='Preoperative Kidney disease',
                                         help="Preoperative serum creatinine >2.0 mg/dL (177 mol/L)")
    rcri_total = fields.Integer(string='Score', help='Points 0: Class I Very Low (0.4% complications)\n'
                                                     'Points 1: Class II Low (0.9% complications)\n'
                                                     'Points 2: Class III Moderate (6.6% complications)\n'
                                                     'Points 3 or more : Class IV High (>11% complications)',
                                default=lambda *a: 0)
    rcri_class = fields.Selection(RCRI_CLASS, string='RCRI Class', required=True, default=lambda *a: 'I')

    @api.onchange('rcri_high_risk_surgery', 'rcri_ischemic_history', 'rcri_congestive_history', 'rcri_diabetes_history',
                  'rcri_cerebrovascular_history', 'rcri_kidney_history')
    def on_change_with_rcri(self):
        total = 0
        rcri_class = 'I'
        if self.rcri_high_risk_surgery:
            total = total + 1
        if self.rcri_ischemic_history:
            total = total + 1
        if self.rcri_congestive_history:
            total = total + 1
        if self.rcri_diabetes_history:
            total = total + 1
        if self.rcri_kidney_history:
            total = total + 1
        if self.rcri_cerebrovascular_history:
            total = total + 1

        self.rcri_total = total

        if total == 1:
            rcri_class = 'II'
        if total == 2:
            rcri_class = 'III'
        if (total > 2):
            rcri_class = 'IV'

        self.rcri_class = rcri_class


class intarvasSurgeryTeam(models.Model):
    _name = "oeh.medical.surgery.team"
    _description = "Surgery Team"

    name = fields.Many2one('oeh.medical.surgery', string='Surgery')
    team_member = fields.Many2one('oeh.medical.physician', string='Member',
                                  help="Health professional that participated on this surgery",
                                  domain=[('is_pharmacist', '=', False)], required=True)
    role = fields.Many2one('oeh.medical.speciality', string='Role')
    notes = fields.Char(string='Notes')

    @api.onchange('team_member')
    def onchange_team_member(self):
        if self.team_member:
            if self.team_member.speciality:
                self.role = self.team_member.speciality.id


class intarvasSurgerySupply(models.Model):
    _name = "oeh.medical.surgery.supply"
    _description = "Supplies related to the surgery"

    name = fields.Many2one('oeh.medical.surgery', string='Surgery')
    qty = fields.Integer(string='Initial required quantity', required=True, help="Initial required quantity",
                         default=lambda *a: 0)
    supply = fields.Many2one('product.product', string='Supply', required=True,
                             help="Supply to be used in this surgery")
    notes = fields.Char(string='Notes')
    qty_used = fields.Integer(string='Actual quantity used', required=True, help="Actual quantity used",
                              default=lambda *a: 0)


class intarvasSurgery(models.Model):
    _name = "oeh.medical.surgery"
    _description = "Surgerical Management"
    _inherit = ['mail.thread']
    _order = 'id desc'

    CLASSIFICATION = [
        ('Optional', 'Optional'),
        ('Required', 'Required'),
        ('Urgent', 'Urgent'),
        ('Emergency', 'Emergency'),
    ]

    STATES = [
        ('Draft', 'Draft'),
        ('Confirmed', 'Confirmed'),
        ('In Progress', 'In Progress'),
        ('Done', 'Done'),
        ('Invoice', 'Invoice'),
        ('Signed', 'Signed'),
        ('Cancelled', 'Cancelled'),
    ]

    GENDER = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Female -> Male', 'Female -> Male'),
        ('Male -> Female', 'Male -> Female'),
    ]

    PREOP_MALLAMPATI = [
        ('Class 1', 'Class 1: Full visibility of tonsils, uvula and soft '
                    'palate'),
        ('Class 2', 'Class 2: Visibility of hard and soft palate, '
                    'upper portion of tonsils and uvula'),
        ('Class 3', 'Class 3: Soft and hard palate and base of the uvula are '
                    'visible'),
        ('Class 4', 'Class 4: Only Hard Palate visible'),
    ]

    PREOP_ASA = [
        ('PS 1', 'PS 1 : Normal healthy patient'),
        ('PS 2', 'PS 2 : Patients with mild systemic disease'),
        ('PS 3', 'PS 3 : Patients with severe systemic disease'),
        ('PS 4', 'PS 4 : Patients with severe systemic disease that is'
                 ' a constant threat to life '),
        ('PS 5', 'PS 5 : Moribund patients who are not expected to'
                 ' survive without the operation'),
        ('PS 6', 'PS 6 : A declared brain-dead patient who organs are'
                 ' being removed for donor purposes'),
    ]

    SURGICAL_WOUND = [
        ('I', 'Clean . Class I'),
        ('II', 'Clean-Contaminated . Class II'),
        ('III', 'Contaminated . Class III'),
        ('IV', 'Dirty-Infected . Class IV'),
    ]

    def _surgery_duration(self):
        for su in self:
            duration = 0.0
            if su.surgery_end_date and su.surgery_date:
                diff = fields.Datetime.from_string(su.surgery_end_date) - fields.Datetime.from_string(su.surgery_date)
                if diff:
                    duration = float(diff.days) * 24 + (float(diff.seconds) / 3600)
            su.surgery_length = duration
        return True

    def _patient_age_at_surgery(self):
        def compute_age_from_dates(patient_dob, patient_surgery_date):
            if (patient_dob):
                dob = datetime.datetime.strptime(patient_dob.strftime('%Y-%m-%d'), '%Y-%m-%d').date()
                surgery_date = datetime.datetime.strptime(patient_surgery_date.strftime('%Y-%m-%d %H:%M:%S'),
                                                          '%Y-%m-%d %H:%M:%S').date()
                delta = surgery_date - dob
                years_months_days = str(delta.days // 365) + " years " + str(delta.days % 365) + " days"
            else:
                years_months_days = "No DoB !"
            return years_months_days

        result = {}
        for patient_data in self:
            patient_data.computed_age = compute_age_from_dates(patient_data.patient.dob, patient_data.surgery_date)
        return result

    def _get_surgeon(self):
        """Return default physician value"""
        therapist_obj = self.env['oeh.medical.physician']
        domain = [('oeh_user_id', '=', self.env.uid)]
        user_ids = therapist_obj.search(domain)
        if user_ids:
            return user_ids.id or False
        else:
            return False

    name = fields.Char(string='Surgery #', size=64, readonly=True, required=True, default=lambda *a: '/')
    patient = fields.Many2one('oeh.medical.patient', string='Patient', help="Patient Name", required=True)
    admission = fields.Many2one('oeh.medical.appointment', string='Admission', help="Admission Name")
    procedures = fields.Many2many('oeh.medical.procedure', 'oeh_surgery_procedure_rel', 'surgery_id', 'procedure_id',
                                  string='Procedures',
                                  help="List of the procedures in the surgery. Please enter the first one as the main procedure")
    pathology = fields.Many2one('oeh.medical.pathology', string='Condition', help="Base Condition / Reason")
    classification = fields.Selection(CLASSIFICATION, string='Urgency', help="Urgency level for this surgery", required=True)
    surgeon = fields.Many2one('oeh.medical.physician', string='Surgeon', help="Surgeon who did the procedure",
                              domain=[('is_pharmacist', '=', False)], required=True, default=_get_surgeon)
    anesthetist = fields.Many2one('oeh.medical.physician', string='Anesthetist', help="Anesthetist in charge",
                                  domain=[('is_pharmacist', '=', False)], required=True)
    surgery_date = fields.Datetime(string='Start date & time', help="Start of the Surgery", default=lambda *a: datetime.datetime.now())
    surgery_end_date = fields.Datetime(string='End date & time', help="End of the Surgery")
    surgery_length = fields.Float(compute=_surgery_duration, string='Duration (Hour:Minute)',
                                  help="Length of the surgery")
    computed_age = fields.Char(compute=_patient_age_at_surgery, size=32, string='Age during surgery',
                               help="Computed patient age at the moment of the surgery")
    gender = fields.Selection(GENDER, string='Gender')
    signed_by = fields.Many2one('res.users', string='Signed by',
                                help="Health Professional that signed this surgery document")
    description = fields.Text(string='Description')
    preop_mallampati = fields.Selection(PREOP_MALLAMPATI, string='Mallampati Score')
    preop_bleeding_risk = fields.Boolean(string='Risk of Massive bleeding',
                                         help="Patient has a risk of losing more than 500 ml in adults of over 7ml/kg in infants. If so, make sure that intravenous access and fluids are available")
    preop_oximeter = fields.Boolean(string='Pulse Oximeter in place', help="Pulse oximeter is in place and functioning")
    preop_site_marking = fields.Boolean(string='Surgical Site Marking',
                                        help="The surgeon has marked the surgical incision")
    preop_antibiotics = fields.Boolean(string='Antibiotic Prophylaxis',
                                       help="Prophylactic antibiotic treatment within the last 60 minutes")
    preop_sterility = fields.Boolean(string='Sterility Confirmed',
                                     help="Nursing team has confirmed sterility of the devices and room")
    preop_asa = fields.Selection(PREOP_ASA, string='ASA PS', help="ASA pre-operative Physical Status")
    preop_rcri = fields.Many2one('oeh.medical.surgery.rcri', string='RCRI',
                                 help='Patient Revised Cardiac Risk Index\n Points 0: Class I Very Low (0.4% complications)\n Points 1: Class II Low (0.9% complications)\n Points 2: Class III Moderate (6.6% complications)\n Points 3 or more : Class IV High (>11% complications)')
    surgical_wound = fields.Selection(SURGICAL_WOUND, string='Surgical Wound')
    info = fields.Text(string='Extra Info')
    anesthesia_report = fields.Text(string='Anesthesia Report')
    institution = fields.Many2one('oeh.medical.health.center', string='Health Center', help="Health Center", required=True)
    postoperative_dx = fields.Many2one('oeh.medical.pathology', string='Post-op dx', help="Post-operative diagnosis")
    surgery_team = fields.One2many('oeh.medical.surgery.team', 'name', string='Team Members',
                                   help="Professionals Involved in the surgery")
    supplies = fields.One2many('oeh.medical.surgery.supply', 'name', string='Supplies',
                               help="List of the supplies required for the surgery")
    building = fields.Many2one('oeh.medical.health.center.building', string='Building',
                               help="Building of the selected Health Center", required=True)
    operating_room = fields.Many2one('oeh.medical.health.center.ot', string='Operation Theater')
    state = fields.Selection(STATES, string='State', readonly=True, default=lambda *a: 'Draft')

    surgery_type = fields.Many2one('surgery.types', string='Surgery Type',required=False)
    move_id = fields.Many2one('account.move', string="Invoice", help="Related Invoice")

    def create(self, vals):
        # Generate next surgery sequence
        company = self.env.company
        search_sequence = self.env['ir.sequence'].search(
            [('code', '=', 'oeh.medical.surgery'), ('company_id', 'in', [company.id, False])], order='company_id')
        if not search_sequence:
            values = {
                'name': 'Surgery (' + str(company.name) + ')',
                'code': 'oeh.medical.surgery',
                'company_id': company.id,
                'prefix': 'SR',
                'padding': 4,
            }
            sequence = self.env['ir.sequence'].sudo().create(values)
            vals['name'] = sequence and sequence.next_by_code('oeh.medical.surgery') or '/'
            health_surgery = models.Model.create(self, vals)
            return health_surgery
        else:
            sequence = self.env['ir.sequence'].next_by_code('oeh.medical.surgery')
            vals['name'] = sequence
            health_surgery = super(intarvasSurgery, self).create(vals)
            return health_surgery


    def action_surgery_confirm(self):
        for surgery in self:
            if surgery.operating_room:
                query = _("update oeh_medical_health_center_ot set state='Reserved' where id=%s") % (
                    str(surgery.operating_room.id))
                self.env.cr.execute(query)
        return self.write({'state': 'Confirmed'})

    def action_surgery_start(self):
        for surgery in self:
            if surgery.operating_room:
                query = _("update oeh_medical_health_center_ot set state='Occupied' where id=%s") % (
                    str(surgery.operating_room.id))
                self.env.cr.execute(query)
        return self.write({'state': 'In Progress', 'surgery_date': datetime.datetime.now()})

    def action_surgery_cancel(self):
        for surgery in self:
            if surgery.operating_room:
                query = _("update oeh_medical_health_center_ot set state='Free' where id=%s") % (
                    str(surgery.operating_room.id))
                self.env.cr.execute(query)
        return self.write({'state': 'Cancelled'})

    def action_surgery_set_to_draft(self):
        return self.write({'state': 'Draft'})

    def action_surgery_end(self):
        for surgery in self:
            if surgery.operating_room:
                query = _("update oeh_medical_health_center_ot set state='Free' where id=%s") % (
                    str(surgery.operating_room.id))
                self.env.cr.execute(query)
        return self.write({'state': 'Done', 'surgery_end_date': datetime.datetime.now()})

    def action_surgery_sign(self):
        phy_obj = self.env["oeh.medical.physician"]
        domain = [('oeh_user_id', '=', self.env.uid)]
        user_ids = phy_obj.search(domain)
        if user_ids:
            self.signed_by = self.env.uid or False
            self.state = 'Signed'
        else:
            raise UserError(_('No physician associated to logged in user'))


    def action_view_invoice(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        if self.move_id:
            action['res_id'] = self.move_id.id
            action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
            action['context'] = dict(self._context,
                                     default_partner_id=self.patient and self.patient.partner_id.id or False,
                                     default_patient=self.patient and self.patient.id or False)
        return action


    def _get_default_journal(self):
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        return journal


    def set_to_invoiced(self):
        invoice_obj = self.env["account.move"]
        invoice_lines = []

        for surgery in self:
            if surgery.patient:
                default_journal = self._get_default_journal()
                sequence_count = 1

                invoice_lines.append((0, 0, {
                    'name': 'Surgery Charges',
                    'display_type': 'line_section',
                    'account_id': False,
                    'sequence': sequence_count,
                }))

                sequence_count += 1

                invoice_lines.append((0, 0, {
                    'display_type': 'product',
                    'name': "Surgery charge - {}".format(
                        surgery.surgery_type.name if surgery.surgery_type else "Unknown Surgery Type"
                    ),
                    'product_id': surgery.surgery_type.product_id.id if surgery.surgery_type.product_id else False,
                    'price_unit': surgery.surgery_type.price_of_surgery or 0.0,
                    'quantity': 1.0,
                    'sequence': sequence_count,
                }))

                invoice_vals = {
                    'move_type': 'out_invoice',
                    'journal_id': default_journal.id,
                    'partner_id': surgery.patient.partner_id.id,
                    'patient': surgery.patient.id,
                    # 'invoice_date': datetime.today().date(),
                    # 'date': datetime.today().date(),
                    'invoice_date': fields.Date.today(),
                    'date': fields.Date.today(),
                    'ref': f"Surgery Admission #: {surgery.name}",
                    'invoice_line_ids': invoice_lines,
                }

                invoice = invoice_obj.sudo().create(invoice_vals)

                self.write({'state': 'Invoice', 'move_id': invoice.id})

        return True


# Inheriting Patient module to add "Surgeries" screen reference
class intarvasPatient(models.Model):
    _inherit = 'oeh.medical.patient'
    pediatrics_surgery_ids = fields.One2many('oeh.medical.surgery', 'patient', string='Surgeries')
