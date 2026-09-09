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
import json
import logging

_logger = logging.getLogger(__name__)


class intarvasMedicalImagingProtocol(models.Model):
    """Advanced Protocol Management for Medical Imaging"""
    _name = 'oeh.medical.imaging.protocol'
    _description = 'Medical Imaging Protocol'
    _inherit = ['mail.thread']
    _order = 'name'

    name = fields.Char(string='Protocol Name', required=True, tracking=True)
    code = fields.Char(string='Protocol Code', required=True, tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    
    # Protocol classification
    modality = fields.Selection([
        ('xr', 'X-Ray'),
        ('ct', 'CT Scan'),
        ('mri', 'MRI'),
        ('us', 'Ultrasound'),
        ('nm', 'Nuclear Medicine'),
        ('pet', 'PET Scan'),
        ('mg', 'Mammography'),
        ('fl', 'Fluoroscopy'),
        ('other', 'Other')
    ], string='Modality', required=True, tracking=True)
    
    body_region = fields.Selection([
        ('head_neck', 'Head & Neck'),
        ('chest', 'Chest'),
        ('abdomen', 'Abdomen'),
        ('pelvis', 'Pelvis'),
        ('spine', 'Spine'),
        ('extremity', 'Extremity'),
        ('cardiac', 'Cardiac'),
        ('vascular', 'Vascular'),
        ('whole_body', 'Whole Body')
    ], string='Body Region', tracking=True)
    
    # Protocol specifications
    contrast_required = fields.Boolean(string='Contrast Required', default=False, tracking=True)
    contrast_type = fields.Selection([
        ('oral', 'Oral Contrast'),
        ('iv', 'IV Contrast'),
        ('rectal', 'Rectal Contrast'),
        ('oral_iv', 'Oral + IV Contrast'),
        ('other', 'Other')
    ], string='Contrast Type')
    
    contrast_volume = fields.Float(string='Contrast Volume (ml)')
    contrast_delay = fields.Integer(string='Contrast Delay (seconds)')
    
    # Acquisition parameters (stored as JSON for flexibility)
    acquisition_parameters = fields.Json(string='Acquisition Parameters', default={})
    
    # Protocol instructions
    preparation_instructions = fields.Text(string='Patient Preparation Instructions',
                                         help="Instructions for patient preparation before the procedure")
    
    positioning_instructions = fields.Text(string='Patient Positioning Instructions',
                                         help="Instructions for patient positioning during the procedure")
    
    acquisition_instructions = fields.Text(string='Acquisition Instructions',
                                         help="Technical instructions for image acquisition")
    
    post_processing_instructions = fields.Text(string='Post-Processing Instructions',
                                             help="Instructions for image post-processing")
    
    # Protocol validation and quality
    requires_physician_approval = fields.Boolean(string='Requires Physician Approval', default=False)
    approved_by = fields.Many2one('oeh.medical.physician', string='Approved By',
                                domain=[('is_pharmacist', '=', False)])
    approval_date = fields.Date(string='Approval Date')
    
    # Protocol metrics and usage
    average_duration_minutes = fields.Float(string='Average Duration (minutes)',
                                          help="Average time required for this protocol")
    
    estimated_dose = fields.Float(string='Estimated Radiation Dose (mGy)',
                                help="Estimated radiation dose for this protocol")
    
    # Usage statistics
    usage_count = fields.Integer(string='Usage Count', compute='_compute_usage_statistics', store=True)
    last_used_date = fields.Date(string='Last Used Date', compute='_compute_usage_statistics', store=True)
    
    # Protocol relationships
    parent_protocol_id = fields.Many2one('oeh.medical.imaging.protocol', string='Parent Protocol')
    child_protocol_ids = fields.One2many('oeh.medical.imaging.protocol', 'parent_protocol_id', 
                                        string='Child Protocols')
    
    # Linked studies
    study_ids = fields.One2many('oeh.medical.imaging', 'imaging_protocol', string='Associated Studies')
    
    @api.depends('study_ids')
    def _compute_usage_statistics(self):
        """Compute protocol usage statistics"""
        for record in self:
            studies = record.study_ids.filtered(lambda s: s.state != 'cancelled')
            record.usage_count = len(studies)
            record.last_used_date = max(studies.mapped('date_requested'), default=False)
    
    @api.constrains('code')
    def _check_unique_code(self):
        """Ensure protocol codes are unique"""
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_("Protocol code must be unique."))
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to auto-generate code if not provided"""
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self.env['ir.sequence'].next_by_code('oeh.medical.imaging.protocol') or 'PROT0001'
        return super().create(vals_list)
    
    def action_duplicate_protocol(self):
        """Create a copy of this protocol"""
        for record in self:
            copy_vals = record.copy_data()[0]
            copy_vals.update({
                'name': f"{record.name} (Copy)",
                'code': f"{record.code}_COPY",
                'approved_by': False,
                'approval_date': False,
            })
            new_protocol = self.create(copy_vals)
            
            return {
                'type': 'ir.actions.act_window',
                'name': 'Duplicated Protocol',
                'res_model': 'oeh.medical.imaging.protocol',
                'res_id': new_protocol.id,
                'view_mode': 'form',
                'target': 'current',
            }
    
    def action_approve_protocol(self):
        """Approve this protocol"""
        for record in self:
            record.write({
                'approved_by': self.env.user.partner_id.id,
                'approval_date': fields.Date.today()
            })
    
    def get_protocol_parameters_json(self):
        """Get protocol parameters as formatted JSON string"""
        return json.dumps(self.acquisition_parameters, indent=2) if self.acquisition_parameters else "{}"


# Body parts removed - keeping protocols simple