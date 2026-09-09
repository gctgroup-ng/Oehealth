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

class intarvasAdmissionWizard(models.TransientModel):
    _name = "oeh.medical.admission.wizard"
    _description = "Patient Admission Wizard"

    ADMISSION_TYPE = [
        ('Routine', 'Routine'),
        ('Maternity', 'Maternity'),
        ('Elective', 'Elective'),
        ('Urgent', 'Urgent'),
        ('Emergency', 'Emergency'),
        ('Other', 'Other'),
    ]

    patient_id = fields.Many2one('oeh.medical.patient', string='Patient', required=True, readonly=True)
    appointment_id = fields.Many2one('oeh.medical.appointment', string='Appointment', readonly=True)
    scheduled_date = fields.Datetime(string='Scheduled Date', required=True, default=fields.Datetime.now)
    admission_reason = fields.Many2one('oeh.medical.pathology', string='Reason for Admission', required=True, help="Reason for Admission")
    institution = fields.Many2one('oeh.medical.health.center', string='Health Center', required=True)
    admission_type = fields.Selection(ADMISSION_TYPE, string='Admission Type', required=True, default='Routine')
    ward = fields.Many2one('oeh.medical.health.center.ward', string='Ward', required=True, domain="[('institution', '=', institution)]")
    bed = fields.Many2one('oeh.medical.health.center.beds', string='Bed', required=True, domain="[('ward','=',ward),('state','=','Free')]")

    @api.model
    def default_get(self, fields):
        res = super(intarvasAdmissionWizard, self).default_get(fields)
        appointment_id = self._context.get('active_id')
        if appointment_id:
            appointment = self.env['oeh.medical.appointment'].browse(appointment_id)
            res.update({
                'patient_id': appointment.patient.id,
                'appointment_id': appointment_id,
                'institution': appointment.institution.id if appointment.institution else False,
            })
        return res

    @api.onchange('institution')
    def _onchange_institution(self):
        if self.institution:
            return {'domain': {'ward': [('institution', '=', self.institution.id)]}}
        else:
            return {'domain': {'ward': []}}

    @api.onchange('ward')
    def _onchange_ward(self):
        if self.ward:
            return {'domain': {'bed': [('ward', '=', self.ward.id), ('state', '=', 'Free')]}}
        else:
            return {'domain': {'bed': []}}

    def action_admit_patient(self):
        appointment = self.env['oeh.medical.appointment'].browse(self._context.get('active_id'))
        
        if not appointment:
            raise UserError(_('No appointment found!'))

        inpatient_vals = {
            'patient': self.patient_id.id,
            'appointment_id': appointment.id,
            'scheduled_date': self.scheduled_date,
            'admission_reason': self.admission_reason.id,
            'institution': self.institution.id,
            'admission_type': self.admission_type,
            'ward': self.ward.id,
            'bed': self.bed.id,
            'attending_physician': appointment.doctor.id if appointment.doctor else False,
        }

        inpatient = self.env['oeh.medical.inpatient'].create(inpatient_vals)

        appointment.write({'inpatient_id': inpatient.id})

        return {
            'type': 'ir.actions.act_window',
            'name': _('Inpatient Admission'),
            'view_mode': 'form',
            'res_model': 'oeh.medical.inpatient',
            'res_id': inpatient.id,
            'target': 'current',
        }