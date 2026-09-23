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


from odoo import api, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.depends('create_date')
    def _compute_tour_enabled(self):
        self.tour_enabled = False

    def _init_odoobot(self):
        self.ensure_one()
        self.sudo().odoobot_state = 'disabled'

    @api.model
    def _intarvas_disable_onboarding(self):
        users = self.with_context(active_test=False).sudo().search([])
        users.write({'tour_enabled': False})
        users.filtered(lambda u: u.odoobot_state in (False, 'not_initialized')).write({'odoobot_state': 'disabled'})
