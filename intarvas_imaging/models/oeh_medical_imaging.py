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
import time
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


# Supporting Models
class intarvasImagingTestDepartment(models.Model):
    """Imaging Test Departments"""
    _name = 'oeh.medical.imagingtest.department'
    _description = 'Imaging Test Department'

    name = fields.Char(string='Department Name', size=128, required=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Department name must be unique!')
    ]


class intarvasImagingTestType(models.Model):
    """Imaging Test Types"""
    _name = 'oeh.medical.imaging.test.type'
    _description = 'Imaging Test Types'

    name = fields.Char(string='Test Type Name', size=128, required=True)
    code = fields.Char(string='Test Code', size=64, required=True)
    imaging_department = fields.Many2one('oeh.medical.imagingtest.department', string='Department')
    test_charge = fields.Float(string='Test Charge', default=0.0)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Test type name must be unique!')
    ]


# Main Model
class intarvasImagingTypeManagement(models.Model):
    _name = 'oeh.medical.imaging'
    _description = 'Imaging Test Management'
    _inherit = ['mail.thread']
    _order = 'id desc'

    # Original workflow states - restored for backward compatibility
    IMAGING_STATE = [
        ('Draft', 'Draft'),
        ('Test In Progress', 'Test In Progress'),
        ('Completed', 'Completed'),
        ('Invoiced', 'Invoiced'),
    ]

    PRIORITY_LEVELS = [
        ('routine', 'Routine'),
        ('urgent', 'Urgent'),
        ('stat', 'STAT'),
    ]

    # Basic fields (keep existing)
    name = fields.Char(string='Test #', size=16, required=True, readonly=True, default=lambda *a: '/')
    patient = fields.Many2one('oeh.medical.patient', string='Patient', help="Patient Name", required=True, tracking=True)
    test_type = fields.Many2one('oeh.medical.imaging.test.type', string='Test Type', required=True)
    imaging_department = fields.Many2one('oeh.medical.imagingtest.department', string='Department', required=True)
    requestor = fields.Many2one('oeh.medical.physician', string='Doctor', help="Doctor who requested the test", required=True, 
                               domain=[('is_pharmacist', '=', False)], tracking=True)
    date_requested = fields.Datetime(string='Date requested', default=lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'), tracking=True)
    date_analysis = fields.Datetime(string='Date of the Analysis', tracking=True)
    state = fields.Selection(IMAGING_STATE, string='State', readonly=True, default='Draft', tracking=True)
    
    # Essential enhancements
    priority = fields.Selection(PRIORITY_LEVELS, string='Priority', default='routine', tracking=True)
    clinical_indication = fields.Text(string='Clinical Indication', help="Clinical reason for the imaging study")
    imaging_protocol = fields.Many2one('oeh.medical.imaging.protocol', string='Protocol')
    reporting_template = fields.Many2one('oeh.medical.radiology.template', string='Report Template')
    
    # Enhanced reporting fields
    technique = fields.Text(string='Technique', help="Imaging technique used")
    impression = fields.Text(string='Impression', help="Diagnostic impression")
    recommendations = fields.Text(string='Recommendations', help="Follow-up recommendations")
    
    # Quality control
    primary_reader = fields.Many2one('oeh.medical.physician', string='Primary Reader',
                                    domain=[('is_pharmacist', '=', False)], tracking=True)
    peer_reviewer = fields.Many2one('oeh.medical.physician', string='Peer Reviewer',
                                  domain=[('is_pharmacist', '=', False)], tracking=True)
    critical_result = fields.Boolean(string='Critical Result', default=False, tracking=True)
    
    # Keep original fields for compatibility
    analysis = fields.Text(string='Analysis')
    conclusion = fields.Text(string='Conclusion')
    
    # Legacy image fields for backward compatibility
    image1 = fields.Binary(string="Image 1 (Legacy)", help="Legacy field - use attachment system instead")
    image2 = fields.Binary(string="Image 2 (Legacy)", help="Legacy field - use attachment system instead") 
    image3 = fields.Binary(string="Image 3 (Legacy)", help="Legacy field - use attachment system instead")
    image4 = fields.Binary(string="Image 4 (Legacy)", help="Legacy field - use attachment system instead")
    image5 = fields.Binary(string="Image 5 (Legacy)", help="Legacy field - use attachment system instead")
    image6 = fields.Binary(string="Image 6 (Legacy)", help="Legacy field - use attachment system instead")
    
    # Enhanced attachment system
    attachment_ids = fields.One2many(
        'ir.attachment',
        'res_id',
        domain=[('res_model', '=', 'oeh.medical.imaging')],
        string='Medical Files',
        help="All medical images and documents for this radiology study"
    )
    
    # Study metadata for DICOM integration
    study_metadata = fields.Json('Study Metadata', default={})
    
    # Invoice integration fields
    move_id = fields.Many2one('account.move', string="Invoice", readonly=True)
    product_id = fields.Many2one('product.product', 
                                string="Product", 
                                default=lambda self: self._get_default_product())
    
    def _get_default_product(self):
        """Get default imaging product if available"""
        try:
            return self.env.ref('intarvas_imaging.product_medical_imaging').id
        except ValueError:
            return False

    # Original workflow actions - restored for backward compatibility
    def action_start_test(self):
        """Start the imaging test"""
        for record in self:
            record.write({'state': 'Test In Progress'})
        return True
    
    def action_complete_test(self):
        """Complete the imaging test"""
        for record in self:
            record.write({
                'state': 'Completed',
                'date_analysis': fields.Datetime.now()
            })
        return True

    # Invoice creation
    def action_imaging_invoice_create(self):
        invoice_obj = self.env["account.move"]
        invoice_lines = []
        for imaging in self:
            if imaging.patient:
                if imaging.test_type:
                    test_charge = imaging.test_type.test_charge
                else:
                    test_charge = 0.0

                invoice_lines.append((0, 0, {
                    'product_id': imaging.product_id.id if imaging.product_id else False,
                    'name': imaging.test_type.name if imaging.test_type else 'Medical Imaging',
                    'price_unit': test_charge,
                    'quantity': 1.0,
                    'product_uom_id': imaging.product_id.uom_id.id if imaging.product_id else False,
                }))

                invoice_id = invoice_obj.create({
                    'partner_id': imaging.patient.partner_id.id,
                    'patient': imaging.patient.id,
                    'move_type': 'out_invoice',
                    'invoice_line_ids': invoice_lines,
                    'invoice_date': datetime.now().strftime('%Y-%m-%d'),
                })
                
                imaging.write({'move_id': invoice_id.id, 'state': 'Invoiced'})
        return True

    def action_view_invoice(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        if self.move_id:
            action['res_id'] = self.move_id.id
            action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
        return action

    def print_patient_imaging(self):
        """Print radiology report"""
        self.ensure_one()
        return self.env.ref('intarvas_imaging.action_report_patient_imaging').report_action(self)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == '/':
                sequence = self.env['ir.sequence'].next_by_code('oeh.medical.imaging')
                vals['name'] = sequence
        return super().create(vals_list)