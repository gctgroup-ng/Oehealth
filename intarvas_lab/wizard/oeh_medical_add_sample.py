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


class intarvasSamplesWizard(models.TransientModel):
    _name = "oeh.medical.samples.wizard"
    _description = "Lab  Samples"

    comments = fields.Text(string='Comments')
    samples_ids = fields.Many2many('oeh.medical.labtest.types', string='Lab Tests')
    sample_type = fields.Many2one('oeh.medical.sample.types', required=True, string='Sample Type')
    sample_id = fields.Many2one('oeh.medical.lab.request')

    def action_submit(self):
        test_lines = self.env['oeh.medical.lab.request'].browse(self._context.get('active_ids', []))
        lines = self.env['oeh.medical.lab.samples'].sudo().create({
            'sample_type': self.sample_type.id,
            'samples_ids': self.samples_ids,
            'sample_id': test_lines.id,
            'comments': self.comments,
        })
        self.sample_id.lab_sample_ids = lines
