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
from odoo import tools
from datetime import datetime
from odoo.exceptions import UserError

# Inpatient Prescriped Medicines details
class intarvasInpatientPrescribedMedicaments(models.Model):
    _name = 'oeh.medical.inpatient.prescribed.medicine'
    _description = 'Inpatient Admissions Prescribed Medicines'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    FREQUENCY_UNIT = [
        ('Seconds', 'Seconds'),
        ('Minutes', 'Minutes'),
        ('Hours', 'Hours'),
        ('Days', 'Days'),
        ('Weeks', 'Weeks'),
        ('When Required', 'When Required'),
    ]

    DURATION_UNIT = [
        ('Minutes', 'Minutes'),
        ('Hours', 'Hours'),
        ('Days', 'Days'),
        ('Months', 'Months'),
        ('Years', 'Years'),
        ('Indefinite', 'Indefinite'),
    ]

    inpatient_id = fields.Many2one('oeh.medical.inpatient', string='Inpatient Admission Reference', ondelete='cascade', index=True)
    name = fields.Many2one('oeh.medical.medicines', string='Medicines', help="Prescribed Medicines", domain=[('medicament_type','=','Medicine')], required=True)
    indication = fields.Many2one('oeh.medical.pathology', string='Indication', help="Choose a disease for this medicament from the disease list. It can be an existing disease of the patient or a prophylactic.")
    dose = fields.Integer(string='Dose', help="Amount of medicines (eg, 250 mg ) each time the patient takes it")
    dose_unit = fields.Many2one('oeh.medical.dose.unit', string='Dose Unit', help="Unit of measure for the medication to be taken")
    dose_route = fields.Many2one('oeh.medical.drug.route', string='Administration Route', help="HL7 or other standard drug administration route code.")
    dose_form = fields.Many2one('oeh.medical.drug.form','Form', help="Drug form, such as tablet or gel")
    qty = fields.Integer(string='Quantity', help="Quantity of units (eg, 2 capsules) of the medicament", default=lambda *a: 1.0)
    common_dosage = fields.Many2one('oeh.medical.dosage', string='Frequency', help="Common / standard dosage frequency for this medicines")
    frequency = fields.Integer('Frequency')
    frequency_unit = fields.Selection(FREQUENCY_UNIT, 'Unit', index=True)
    admin_times = fields.Char(string='Admin hours', size=128, help='Suggested administration hours. For example, at 08:00, 13:00 and 18:00 can be encoded like 08 13 18')
    duration = fields.Integer(string='Treatment duration')
    duration_period = fields.Selection(DURATION_UNIT, string='Treatment period', help="Period that the patient must take the medication. in minutes, hours, days, months, years or indefinately", index=True)
    start_treatment = fields.Datetime(string='Start of treatment')
    end_treatment = fields.Datetime('End of treatment')
    info = fields.Text('Comment')
    patient = fields.Many2one('oeh.medical.patient', 'Patient', help="Patient Name")



class intarvasInpatientConsumedMedicaments(models.Model):
    _name = 'oeh.medical.inpatient.consumed.medicine'
    _description = 'Inpatient Admissions Consumed Medicines'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    inpatient_id = fields.Many2one('oeh.medical.inpatient', string='Inpatient Admission Reference',
             ondelete='cascade', index=True)
    name = fields.Many2one('oeh.medical.medicines', string='Consumed Medicine', required=True)
    date_time = fields.Datetime(string='Date & Time', required=True, default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='Given By', default=lambda self: self.env.user)
    dose_no = fields.Integer('Dose #')
    dose = fields.Float('Dose', help='Amount of medication (eg, 250 mg) per dose')
    dose_unit = fields.Many2one('oeh.medical.dose.unit', 'Dose unit', help='Unit of measure for the medication to be taken')
    qty = fields.Integer(string='Quantity', help="Quantity of units (eg, 2 capsules) of the medicament", default=lambda *a: 1.0)
    remarks = fields.Text('Remarks')



class intarvasInpatient(models.Model):
    _name = 'oeh.medical.inpatient'
    _description = "Information about the Patient administration"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    ADMISSION_TYPE = [
            ('Routine', 'Routine'),
            ('Maternity', 'Maternity'),
            ('Elective', 'Elective'),
            ('Urgent', 'Urgent'),
            ('Emergency', 'Emergency'),
            ('Other', 'Other'),
        ]

    INPATIENT_STATES = [
            ('Draft', 'Draft'),
            ('Hospitalized', 'Hospitalized'),
            ('Invoiced', 'Invoiced'),
            ('Discharged', 'Discharged'),
            ('Cancelled', 'Cancelled'),
        ]

    # Automatically detect logged in physician
    def _get_physician(self):
        """Return default physician value"""
        therapist_obj = self.env['oeh.medical.physician']
        domain = [('oeh_user_id', '=', self.env.uid)]
        user_ids = therapist_obj.search(domain, limit=1)
        if user_ids:
            return user_ids.id or False
        else:
            return False


    DURATION_UNIT = [
        ('Minutes', 'Minutes'),
        ('Hours', 'Hours'),
        ('Days', 'Days'),
        ('Months', 'Months'),
        ('Years', 'Years'),
        ('Indefinite', 'Indefinite'),
    ]

    remarks = fields.Text('Remarks')
    dose_no = fields.Integer('Dose #')
    user_id = fields.Many2one('res.users', string='Given By', default=lambda self: self.env.user)
    date_time = fields.Datetime(string='Date & Time', required=True, default=fields.Datetime.now)
    duration_period = fields.Selection(DURATION_UNIT, string='Treatment period', help="Period that the patient must take the medication. in minutes, hours, days, months, years or indefinately", index=True)
    duration = fields.Integer(string='Treatment duration')
    qty = fields.Integer(string='Quantity', help="Quantity of units (eg, 2 capsules) of the medicament", default=lambda *a: 1.0)
    common_dosage = fields.Many2one('oeh.medical.dosage', string='Frequency', help="Common / standard dosage frequency for this medicines")
    dose_form = fields.Many2one('oeh.medical.drug.form','Form', help="Drug form, such as tablet or gel")
    dose_unit = fields.Many2one('oeh.medical.dose.unit', string='Dose Unit', help="Unit of measure for the medication to be taken")
    dose = fields.Integer(string='Dose', help="Amount of medicines (eg, 250 mg ) each time the patient takes it")
    indication = fields.Many2one('oeh.medical.pathology', string='Indication', help="Choose a disease for this medicament from the disease list. It can be an existing disease of the patient or a prophylactic.")
    name = fields.Char(string='Inpatient #', size=128, readonly=True, required=True, default=lambda *a: '/')
    patient = fields.Many2one('oeh.medical.patient', string='Patient', help="Patient Name", required=True)
    institution = fields.Many2one('oeh.medical.health.center', string='Health Center')
    admission_type = fields.Selection(ADMISSION_TYPE, string='Admission Type', required=True)
    admission_reason = fields.Many2one('oeh.medical.pathology', string='Reason for Admission', help="Reason for Admission", required=True)
    admission_date = fields.Datetime(string='Hospitalization Date')
    scheduled_date = fields.Datetime(string='Scheduled Date', required=True, states={'Draft': [('required', True)]}, tracking=True, default=fields.Datetime.now)
    discharge_date = fields.Datetime(string='Discharge Date')
    attending_physician = fields.Many2one('oeh.medical.physician', string='Attending Doctor', default=_get_physician)
    operating_physician = fields.Many2one('oeh.medical.physician', string='Operating Doctor')
    ward = fields.Many2one('oeh.medical.health.center.ward', string='Ward', required=True, domain="[('institution', '=', institution)]")
    bed = fields.Many2one('oeh.medical.health.center.beds', string='Bed', required=True)
    nursing_plan = fields.Text(string='Nursing Plan')
    discharge_plan = fields.Text(string='Discharge Plan')
    admission_condition = fields.Text(string='Condition before Admission')
    info = fields.Text(string='Extra Info')
    state = fields.Selection(INPATIENT_STATES, string='State', default=lambda *a: 'Draft')
    prescribed_medicines = fields.One2many('oeh.medical.inpatient.prescribed.medicine', 'inpatient_id',
                                           string='Prescribed Medicines')
    consumed_medicines = fields.One2many('oeh.medical.inpatient.consumed.medicine', 'inpatient_id',
                                         string='Consumed Medicines')
    move_id = fields.Many2one('account.move', string='Invoice #', copy=False)
    invoice_payment_state = fields.Selection(related='move_id.payment_state', string='Payment Status', readonly=True)
    invoice_amount_total = fields.Monetary(related='move_id.amount_total', string='Invoice Total', readonly=True, currency_field='invoice_currency_id')
    invoice_amount_residual = fields.Monetary(related='move_id.amount_residual', string='Amount Due', readonly=True, currency_field='invoice_currency_id')
    invoice_state = fields.Selection(related='move_id.state', string='Invoice State', readonly=True)
    invoice_currency_id = fields.Many2one(related='move_id.currency_id', string='Invoice Currency', readonly=True)

    #add fields for linked appointment
    appointment_id = fields.Many2one('oeh.medical.appointment',string='Appointments', readonly=True)
    appointment_count = fields.Integer(compute='_appointment_count',string='# Appointments')

    def _appointment_count(self):
        for rec in self:
            rec.appointment_count = self.env['oeh.medical.appointment'].search_count([('id', '=', rec.appointment_id.id)])

    def action_view_appointment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Appointment',
            'res_model': 'oeh.medical.appointment',
            'view_mode': 'calendar,list,form',
            'domain': [('id', '=', self.appointment_id.id)],
            'target': 'current',
        }

    def action_create_appointment(self):
        """Create new appointment from inpatient record"""
        self.ensure_one()
        
        # Prepare appointment values
        appointment_vals = {
            'patient': self.patient.id,
            'doctor': self.attending_physician.id if self.attending_physician else False,
            'institution': self.institution.id if self.institution else False,
            'appointment_date': fields.Datetime.now(),
            'duration': 1.0,
            'reason': f'Follow-up appointment for admission {self.name}',
            'state': 'Scheduled',
            'inpatient_id': self.id,  # Link back to inpatient record
        }
        
        # Create the appointment
        appointment = self.env['oeh.medical.appointment'].create(appointment_vals)
        
        # Open the appointment form
        return {
            'type': 'ir.actions.act_window',
            'name': _('New Appointment'),
            'res_model': 'oeh.medical.appointment',
            'view_mode': 'form',
            'res_id': appointment.id,
            'target': 'current',
        }


    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('oeh.medical.inpatient')
        vals['name'] = sequence or '/'
        health_inpatient = super(intarvasInpatient, self).create(vals)
        return health_inpatient

    def _default_account(self):
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        return journal.default_credit_account_id.id

    def set_to_hospitalized(self):
        hospitalized_date = False
        for ina in self:
            if ina.admission_date:
                hospitalized_date = ina.admission_date
            else:
                hospitalized_date = datetime.now()

            if ina.bed:
                query = _("update oeh_medical_health_center_beds set state='Occupied' where id=%s") % (str(ina.bed.id))
                self.env.cr.execute(query)
        return self.write({'state': 'Hospitalized', 'admission_date': hospitalized_date})

    def set_to_invoiced(self):
        view_id = self.env.ref('intarvas.view_oeh_medical_inpatient_wizard').id
        return {'type': 'ir.actions.act_window',
                'name': _('Create Invoice'),
                'res_model': 'oeh.medical.inpatient.invoice.wizard',
                'target': 'new',
                'view_mode': 'form',
                'views': [[view_id, 'form']],
                }

    def set_to_discharged(self):
        discharged_date = False
        for ina in self:
            if ina.discharge_date:
                discharged_date = ina.discharge_date
            else:
                discharged_date = datetime.now()

            if ina.bed:
                query = _("update oeh_medical_health_center_beds set state='Free' where id=%s") % (str(ina.bed.id))
                self.env.cr.execute(query)
        return self.write({'state': 'Discharged', 'discharge_date': discharged_date})

    def set_to_cancelled(self):
        for ina in self:
            if ina.bed:
                query = _("update oeh_medical_health_center_beds set state='Free' where id=%s") % (str(ina.bed.id))
                self.env.cr.execute(query)
        return self.write({'state': 'Cancelled'})

    def set_to_draft(self):
        return self.write({'state': 'Draft'})

    def unlink(self):
        for inpatient in self.filtered(lambda inpatient: inpatient.state not in ['Draft']):
            raise UserError(_('You can not delete an admission record which is not in "Draft" state !!'))
        return super(intarvasInpatient, self).unlink()

    def action_view_invoice(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        if self.move_id:
            action['res_id'] = self.move_id.id
            action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
            action['context'] = dict(self._context, default_partner_id=self.patient and self.patient.partner_id.id or False, default_patient=self.patient and self.patient.id or False)
        return action


    def action_view_invoice(self):
        self.ensure_one()

        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")

        if self.move_id:
            action['res_id'] = self.move_id.id

            action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]

            context = dict(self._context)

            if self.patient:
                context.update({
                    'default_partner_id': self.patient.partner_id.id if self.patient.partner_id else False,
                    'default_patient': self.patient.id
                })

            action['context'] = context

        return action


    prescribed_medical_ids = fields.Many2many(
        comodel_name='oeh.medical.medicines',
        compute='_compute_prescribed_medical_ids',
        string="Prescribed Medical IDs"
    )

    @api.depends('prescribed_medicines')
    def _compute_prescribed_medical_ids(self):
        for rec in self:
            rec.prescribed_medical_ids = rec.prescribed_medicines.mapped('name')

    @api.onchange('consumed_medicines')
    def _onchange_medicine_id(self):
        for consumed in self.consumed_medicines:
            matching = self.prescribed_medicines.filtered(
                lambda p: p.name == consumed.name
            )
            if matching:
                consumed.dose = matching[0].dose
                consumed.qty = matching[0].qty

    def name_get(self):
        result = []
        for admission in self:
            patient_name = admission.patient.name or ""
            admission_type = admission.admission_type or ""
            bed_name = admission.bed.name if admission.bed else ""
            
            name = f"{admission.name}: {patient_name}"
            if admission_type:
                name += f", {admission_type}"
            if bed_name:
                name += f", {bed_name}"
                
            result.append((admission.id, name))
        return result
