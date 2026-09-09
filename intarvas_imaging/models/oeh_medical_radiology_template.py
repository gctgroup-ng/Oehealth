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
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class intarvasMedicalRadiologyTemplate(models.Model):
    """Simple Radiology Reporting Templates"""
    _name = 'oeh.medical.radiology.template'
    _description = 'Radiology Report Template'
    _order = 'name'

    name = fields.Char(string='Template Name', required=True)
    code = fields.Char(string='Template Code', required=True)
    active = fields.Boolean(string='Active', default=True)
    
    # Template classification - simplified
    modality = fields.Selection([
        ('xr', 'X-Ray'),
        ('ct', 'CT Scan'),
        ('mri', 'MRI'),
        ('us', 'Ultrasound'),
        ('other', 'Other')
    ], string='Modality')
    
    # Template content sections - only essential ones
    technique_template = fields.Text(string='Technique Template',
                                   help="Standard technique description template")
    findings_template = fields.Text(string='Findings Template',
                                  help="Template for findings section")
    impression_template = fields.Text(string='Impression Template',
                                    help="Template for impression section")
    
    # Basic tracking
    usage_count = fields.Integer(string='Usage Count', compute='_compute_usage_count', store=True)
    study_ids = fields.One2many('oeh.medical.imaging', 'reporting_template', string='Associated Studies')
    
    @api.depends('study_ids')
    def _compute_usage_count(self):
        """Compute usage count for this template"""
        for record in self:
            record.usage_count = len(record.study_ids)

    @api.constrains('code')
    def _check_unique_code(self):
        """Ensure template codes are unique"""
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_("Template code must be unique."))
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to auto-generate code if not provided"""
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self.env['ir.sequence'].next_by_code('oeh.medical.radiology.template') or 'TPL0001'
        return super().create(vals_list)