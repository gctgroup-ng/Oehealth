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
from odoo.exceptions import ValidationError, UserError


# Chief Complaints Template Management

class intarvasChiefComplaintTemplate(models.Model):
    _name = 'oeh.medical.chief.complaint.template'
    _description = "Chief Complaints Template"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Template Name', required=True, tracking=True,
                      help="Name of the chief complaint template")
    description = fields.Text(string='Description',
                             help="Description of when to use this template")
    active = fields.Boolean(string='Active', default=True)

    # Template Lines
    complaint_line_ids = fields.One2many('oeh.medical.chief.complaint.template.line',
                                        'template_id', string='Complaint Lines')

    def apply_template_to_appointment(self, appointment_id):
        """Apply this template to an appointment"""
        appointment = self.env['oeh.medical.appointment'].browse(appointment_id)
        if not appointment:
            raise UserError(_("Invalid appointment"))

        # Clear existing complaints
        appointment.patient_complaint_ids.unlink()

        # Add complaints from template
        complaint_vals = []
        for line in self.complaint_line_ids:
            complaint_vals.append({
                'appointment_id': appointment.id,
                'complaint_id': line.complaint_id.id,
                'frequency': line.frequency,
                'severity': line.severity,
                'days': line.days,
                'duration': line.duration,
            })

        if complaint_vals:
            self.env['oeh.medical.appointment.complaints'].create(complaint_vals)

        return True


class intarvasChiefComplaintTemplateLine(models.Model):
    _name = 'oeh.medical.chief.complaint.template.line'
    _description = "Chief Complaints Template Line"
    _rec_name = 'complaint_id'

    template_id = fields.Many2one('oeh.medical.chief.complaint.template',
                                 string='Template', required=True, ondelete='cascade')
    complaint_id = fields.Many2one('oeh.medical.complaints', string='Complaint',
                                  required=True, help="Select the chief complaint")

    frequency = fields.Selection([
        ('daily', 'Daily'),
        ('alternate_day', 'Alternate Day'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-Weekly'),
        ('monthly', 'Monthly')
    ], string='Frequency', required=True, default='daily')

    severity = fields.Selection([
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
        ('critical', 'Critical')
    ], string='Severity', required=True, default='mild')

    days = fields.Integer(string='Days', required=True, default=1)
    duration = fields.Selection([
        ('day', 'Day'),
        ('week', 'Week'),
        ('month', 'Month'),
        ('year', 'Year')
    ], string='Duration', required=True, default='day')

# Prescription/Medicine Template Management

class intarvasPrescriptionTemplate(models.Model):
    _name = 'oeh.medical.prescription.template'
    _description = "Prescription Template"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Template Name', required=True, tracking=True,
                      help="Name of the prescription template")
    description = fields.Text(string='Description',
                             help="Description of when to use this template")
    active = fields.Boolean(string='Active', default=True)

    # Template Lines
    medicine_line_ids = fields.One2many('oeh.medical.prescription.template.line',
                                       'template_id', string='Medicine Lines')

    def apply_template_to_appointment(self, appointment_id):
        """Apply this template to an appointment"""
        appointment = self.env['oeh.medical.appointment'].browse(appointment_id)
        if not appointment:
            raise UserError(_("Invalid appointment"))

        # Create medicine lines from template
        medicine_vals = []
        for line in self.medicine_line_ids:
            medicine_vals.append({
                'appointment': appointment.id,
                'patient': appointment.patient.id,
                'name': line.medicine_id.id,
                'indication': line.indication_id.id if line.indication_id else False,
                'dose': line.dose,
                'dose_unit': line.dose_unit_id.id if line.dose_unit_id else False,
                'qty': line.qty,
                'common_dosage': line.common_dosage_id.id if line.common_dosage_id else False,
                'duration': line.duration,
                'duration_period': line.duration_period,
                'info': line.info or '',
            })

        if medicine_vals:
            self.env['oeh.medical.prescription.line'].create(medicine_vals)

        return True


class intarvasPrescriptionTemplateLine(models.Model):
    _name = 'oeh.medical.prescription.template.line'
    _description = "Prescription Template Line"
    _rec_name = 'medicine_id'

    template_id = fields.Many2one('oeh.medical.prescription.template',
                                 string='Template', required=True, ondelete='cascade')
    medicine_id = fields.Many2one('oeh.medical.medicines', string='Medicine',
                                 required=True, help="Select the medicine")
    indication_id = fields.Many2one('oeh.medical.pathology', string='Indication')
    dose = fields.Float(string='Dose', default=1.0)
    dose_unit_id = fields.Many2one('oeh.medical.dose.unit', string='Dose Unit')
    qty = fields.Integer(string='Quantity', default=1)
    common_dosage_id = fields.Many2one('oeh.medical.dosage', string='Dosage')
    duration = fields.Integer(string='Duration', default=1)
    duration_period = fields.Selection([
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years'),
        ('indefinite', 'Indefinite')
    ], string='Duration Period', default='days')
    info = fields.Text(string='Extra Information')


# Medical Advice Template Management

class intarvasAdviceTemplate(models.Model):
    _name = 'oeh.medical.advice.template'
    _description = "Medical Advice Template"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Template Name', required=True, tracking=True,
                      help="Name of the advice template")
    description = fields.Text(string='Description',
                             help="Description of when to use this template")
    active = fields.Boolean(string='Active', default=True)

    # Template Lines
    advice_line_ids = fields.One2many('oeh.medical.advice.template.line',
                                     'template_id', string='Advice Lines')

    def apply_template_to_appointment(self, appointment_id):
        """Apply this template to an appointment"""
        appointment = self.env['oeh.medical.appointment'].browse(appointment_id)
        if not appointment:
            raise UserError(_("Invalid appointment"))

        # Compile advice text from template lines
        advice_text = ""
        for line in self.advice_line_ids:
            advice_prefix = f"[{dict(line._fields['advice_type'].selection)[line.advice_type]}] "
            priority_suffix = ""
            if line.priority in ['high', 'urgent']:
                priority_suffix = f" (Priority: {dict(line._fields['priority'].selection)[line.priority]})"

            followup_suffix = ""
            if line.follow_up_required:
                followup_suffix = f" - Follow up in {line.follow_up_days} days"

            advice_text += f"{advice_prefix}{line.advice_text}{priority_suffix}{followup_suffix}\n"

        # Update appointment comments field
        if advice_text:
            current_comments = appointment.comments or ""
            if current_comments:
                appointment.comments = current_comments + "\n\n" + advice_text
            else:
                appointment.comments = advice_text

        return True


class intarvasAdviceTemplateLine(models.Model):
    _name = 'oeh.medical.advice.template.line'
    _description = "Medical Advice Template Line"
    _rec_name = 'advice_text'

    template_id = fields.Many2one('oeh.medical.advice.template',
                                 string='Template', required=True, ondelete='cascade')
    advice_type = fields.Selection([
        ('diet', 'Dietary Advice'),
        ('exercise', 'Exercise/Physical Activity'),
        ('lifestyle', 'Lifestyle Changes'),
        ('medication', 'Medication Instructions'),
        ('precaution', 'Precautions'),
        ('followup', 'Follow-up Instructions'),
        ('general', 'General Advice')
    ], string='Advice Type', required=True, default='general')

    advice_text = fields.Text(string='Advice', required=True,
                             help="The actual advice text")
    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='normal')

    follow_up_required = fields.Boolean(string='Follow-up Required', default=False)
    follow_up_days = fields.Integer(string='Follow-up Days', default=7,
                                   help="Number of days after which follow-up is required")