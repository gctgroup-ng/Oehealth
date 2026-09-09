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
from odoo.exceptions import UserError


class AppointmentRejectionWizard(models.TransientModel):
    _name = 'oeh.appointment.rejection.wizard'
    _description = 'Appointment Rejection Wizard'

    appointment_id = fields.Many2one('oeh.medical.appointment', string='Appointment', required=True)
    rejection_reason = fields.Selection([
        ('schedule_conflict', 'Schedule Conflict'),
        ('emergency', 'Emergency'),
        ('personal_leave', 'Personal Leave'),
        ('patient_requirements', 'Patient Requirements Not Met'),
        ('other', 'Other'),
    ], string='Rejection Reason', required=True)
    rejection_notes = fields.Text(string='Additional Notes', 
                                 help='Please provide additional details about the rejection')
    suggest_alternative = fields.Boolean(string='Suggest Alternative Time', default=True)
    alternative_date = fields.Datetime(string='Alternative Date')
    alternative_notes = fields.Text(string='Alternative Notes')

    @api.model
    def default_get(self, fields):
        res = super(AppointmentRejectionWizard, self).default_get(fields)
        appointment_id = self.env.context.get('default_appointment_id')
        if appointment_id:
            res['appointment_id'] = appointment_id
        return res

    def action_confirm_rejection(self):
        """Confirm the appointment rejection"""
        self.ensure_one()
        
        if not self.appointment_id:
            raise UserError(_('No appointment specified.'))
        
        # Update appointment with rejection details
        self.appointment_id.action_doctor_reject_confirm(
            self.rejection_reason, 
            self.rejection_notes
        )
        
        # Send rejection email with alternative if suggested
        self._send_rejection_email_with_alternative()
        
        return True

    def _send_rejection_email_with_alternative(self):
        """Send rejection email with alternative appointment suggestion if applicable"""
        template_id = self.env.ref('intarvas.email_template_appointment_rejected', raise_if_not_found=False)
        
        if template_id and self.appointment_id.patient.email:
            # Prepare context for template with alternative information
            template_context = {
                'rejection_reason': dict(self._fields['rejection_reason'].selection)[self.rejection_reason],
                'rejection_notes': self.rejection_notes,
                'suggest_alternative': self.suggest_alternative,
                'alternative_date': self.alternative_date,
                'alternative_notes': self.alternative_notes,
            }
            
            # Send email with additional context
            template_id.with_context(**template_context).send_mail(self.appointment_id.id, force_send=True)