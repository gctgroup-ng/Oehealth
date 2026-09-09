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

from odoo import fields, models

# Chief Complaints Management

class intarvasMedicalComplaints(models.Model):
    _name = 'oeh.medical.complaints'
    _description = "Chief Complaints"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Chief Complaint', size=256, required=True)
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
            ('name_uniq', 'unique (name)', 'The chief complaint must be unique !')]


# Appointment Complaints Management

class intarvasMedicalAppointmentComplaints(models.Model):
    _name = 'oeh.medical.appointment.complaints'
    _description = "Appointment Chief Complaints"
    _rec_name = 'complaint_id'

    appointment_id = fields.Many2one('oeh.medical.appointment', string='Appointment', required=True, ondelete='cascade')
    complaint_id = fields.Many2one('oeh.medical.complaints', string='Complaint', required=True,
                                   help="Select the chief complaint")

    frequency = fields.Selection([
        ('daily', 'Daily'),
        ('alternate_day', 'Alternate Day'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-Weekly'),
        ('monthly', 'Monthly')
    ], string='Frequency', required=True, default='daily',
       help="How often does this complaint occur")

    severity = fields.Selection([
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
        ('critical', 'Critical')
    ], string='Severity', required=True, default='mild',
       help="Severity level of the complaint")

    days = fields.Integer(string='Days', required=True, default=1,
                         help="Number of days for the complaint")

    duration = fields.Selection([
        ('day', 'Day'),
        ('week', 'Week'),
        ('month', 'Month'),
        ('year', 'Year')
    ], string='Duration', required=True, default='day',
       help="Duration unit for the complaint")