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
from datetime import date
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class intarvasInjuryResultWizard(models.TransientModel):
    _name = "oeh.medical.injury.result.wizard"
    _description = "Save Injury Examination Result"

    STATES = [
        ('Treated and Sent Home', 'Treated and Sent Home'),
        ('Admitted', 'Admitted'),
        ('Died', 'Died'),
        ('Dead on Arrival', 'Dead on Arrival'),
    ]

    name = fields.Selection(STATES, 'Choose Examination Result', default='Treated and Sent Home')
    dod = fields.Date(string='Date of Death')
    cod = fields.Many2one('oeh.medical.pathology', string='Cause of Death')
    examination_details = fields.Text(string='Examination Result')
    inpatient = fields.Many2one('oeh.medical.inpatient', string='Choose Inpatient Admission #')

    # Save result chosen in the wizard
    def save_result(self):
        injuries = self.env['oeh.medical.injury.examination'].browse(self._context.get('active_ids', []))
        injury_state = self.name
        for injury in injuries:
            if self.name in ("Died", "Dead on Arrival"):
                injury.patient.write({'deceased': True, 'dod': self.dod, 'cod': self.cod.id})
            if self.name != "Admitted":
                injury.write({'state': injury_state, 'examination_details': self.examination_details})
            else:
                injury.write({'state': injury_state, 'examination_details': self.examination_details, 'inpatient': self.inpatient.id})
