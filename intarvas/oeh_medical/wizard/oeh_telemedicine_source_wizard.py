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


class TelemedicineSources(models.TransientModel):
    _name = 'oeh.telemedicine.sources.wizard'
    _description = 'Telemedicine Resources'

    sources_id = fields.Many2one('oeh.medical.telemedicine.sources', string='Sources', required=True)
    sources_name = fields.Char()
    appointment_id = fields.Many2one('oeh.medical.appointment')
    # skype_meeting_url = fields.Char("URL For Skype Meet")
    # jitsi_meeting_url = fields.Char("URL For Jitsi Meeting")

    @api.onchange('sources_id')
    def change_sources_id(self):
        print("49===============================", self.sources_name)
        self.sources_name = self.sources_id.name
        print("50===============================", self.sources_name)

    def create_meeting(self):
        return True







    #     if self.sources_id.name == 'Skype':
    #         return {
    #             'name': _('Create Online Meeting'),
    #             'type': 'ir.actions.act_window',
    #             'res_model': 'oeh.telemedicine.sources.wizard.skype',
    #             'context': {'default_appointment_id': self.env.context.get('active_id')},
    #             'view_mode': 'form',
    #             'target': 'new',
    #         }
    #     if self.sources_id.name == 'Jitsi':
    #         return {
    #             'name': _('Create Online Meeting'),
    #             'type': 'ir.actions.act_window',
    #             'res_model': 'oeh.jitsi.wizard',
    #             'context': {'default_appointment_id': self.env.context.get('active_id')},
    #             'view_mode': 'form',
    #             'target': 'new',
    #         }
    #     if self.sources_id.name == 'Zoom':
    #         return {
    #             'name': _('Create Online Meeting'),
    #             'type': 'ir.actions.act_window',
    #             'res_model': 'zoom.meeting',
    #             'context': {'default_appointment': self.env.context.get('active_id')},
    #             'view_mode': 'form',
    #             'target': 'new',
    #         }
