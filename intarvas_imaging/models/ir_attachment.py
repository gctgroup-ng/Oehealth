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
from odoo import api, fields, models
import json
import logging
import base64
import io

_logger = logging.getLogger(__name__)

try:
    import pydicom
    from PIL import Image
except ImportError:
    pydicom = None
    Image = None
    _logger.warning("Optional medical imaging libraries not installed")


class IrAttachmentMedical(models.Model):
    _inherit = 'ir.attachment'
    
    # Medical file classification fields
    medical_file_type = fields.Selection([
        ('image', 'Medical Image'),
        ('dicom', 'DICOM File'),
        ('report', 'Medical Report'),
        ('thumbnail', 'Thumbnail'),
        ('dicom_thumbnail', 'DICOM Thumbnail'),
        ('voice', 'Voice Recording'),
        ('video', 'Medical Video'),
        ('other', 'Other Medical File')
    ], string='Medical File Type')
    
    # Metadata storage
    image_metadata = fields.Json(string='Image Metadata')
    dicom_metadata = fields.Json(string='DICOM Metadata')
    processing_metadata = fields.Json(string='Processing Metadata')
    
    # Processing status
    processed = fields.Boolean(string='Processed', default=False)
    processing_status = fields.Selection([
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], string='Processing Status', default='pending')
    
    # File relationships
    parent_attachment_id = fields.Many2one('ir.attachment', string='Parent Attachment')
    child_attachment_ids = fields.One2many('ir.attachment', 'parent_attachment_id', string='Child Attachments')
    
    # Quality and validation
    file_quality = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'), 
        ('acceptable', 'Acceptable'),
        ('poor', 'Poor')
    ], string='File Quality')
    
    validation_status = fields.Selection([
        ('pending', 'Pending'),
        ('valid', 'Valid'),
        ('invalid', 'Invalid'),
        ('warning', 'Warning')
    ], string='Validation Status', default='pending')
    
    validation_messages = fields.Text(string='Validation Messages')
    
    # Computed fields for file type detection
    is_dicom_file = fields.Boolean(string='Is DICOM File', compute='_compute_file_types', store=True)
    is_voice = fields.Boolean(string='Is Voice Recording', compute='_compute_file_types', store=True)
    voice_duration = fields.Float(string='Voice Duration (seconds)')
    
    # Medical context fields
    patient_id = fields.Many2one('res.partner', string='Patient')
    claim_id = fields.Many2one('res.partner', string='Insurance Claim')
    
    @api.depends('mimetype', 'name')
    def _compute_file_types(self):
        for record in self:
            record.is_dicom_file = (
                record.mimetype == 'application/dicom' or 
                (record.name and record.name.lower().endswith('.dcm'))
            )
            record.is_voice = (
                record.mimetype and record.mimetype.startswith('audio/')
            )
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Auto-detect medical file type
            if 'medical_file_type' not in vals:
                vals['medical_file_type'] = self._detect_medical_file_type(vals)
        
        attachments = super().create(vals_list)
        
        # Process medical files after creation
        for attachment in attachments:
            if attachment.res_model == 'oeh.medical.imaging':
                attachment._process_medical_file()
        
        return attachments
    
    def _detect_medical_file_type(self, vals):
        """Auto-detect medical file type based on mimetype and filename."""
        mimetype = vals.get('mimetype', '')
        name = vals.get('name', '')
        
        if mimetype == 'application/dicom' or name.lower().endswith('.dcm'):
            return 'dicom'
        elif mimetype and mimetype.startswith('image/'):
            return 'image'
        elif mimetype and mimetype.startswith('audio/'):
            return 'voice'
        elif mimetype and mimetype.startswith('video/'):
            return 'video'
        elif mimetype == 'application/pdf':
            return 'report'
        else:
            return 'other'
    
    def _process_medical_file(self):
        """Process medical file for metadata extraction and validation."""
        if not self.datas:
            return
            
        try:
            if self.is_dicom_file:
                self._process_dicom_metadata()
            elif self.medical_file_type == 'image':
                self._process_image_metadata()
            elif self.is_voice:
                self._process_voice_metadata()
                
            self.validation_status = 'valid'
            
        except Exception as e:
            _logger.warning(f"Failed to process medical file {self.name}: {e}")
            self.validation_status = 'warning'
            self.validation_messages = str(e)
    
    def _process_dicom_metadata(self):
        """Extract DICOM metadata."""
        try:
            if not pydicom:
                _logger.warning("pydicom not installed, DICOM processing skipped")
                return
                
            dicom_data = base64.b64decode(self.datas)
            ds = pydicom.dcmread(io.BytesIO(dicom_data))
            
            metadata = {
                'patient_name': str(ds.get('PatientName', '')),
                'patient_id': str(ds.get('PatientID', '')),
                'study_date': str(ds.get('StudyDate', '')),
                'modality': str(ds.get('Modality', '')),
                'body_part': str(ds.get('BodyPartExamined', '')),
                'study_instance_uid': str(ds.get('StudyInstanceUID', ''))
            }
            
            self.dicom_metadata = metadata
            self.processed = True
            self.processing_status = 'completed'
            
        except Exception as e:
            _logger.error(f"DICOM processing failed: {e}")
            self.processing_status = 'failed'
    
    def _process_image_metadata(self):
        """Extract image metadata."""
        try:
            if not Image:
                _logger.warning("PIL not installed, image processing skipped")
                return
                
            image_data = base64.b64decode(self.datas)
            image = Image.open(io.BytesIO(image_data))
            
            metadata = {
                'width': image.width,
                'height': image.height,
                'format': image.format,
                'mode': image.mode,
                'size_bytes': len(image_data)
            }
            
            # Extract EXIF data if available
            if hasattr(image, '_getexif') and image._getexif():
                metadata['exif'] = dict(image._getexif())
            
            self.image_metadata = metadata
            self.processed = True
            self.processing_status = 'completed'
            
        except Exception as e:
            _logger.error(f"Image processing failed: {e}")
            self.processing_status = 'failed'
    
    def _process_voice_metadata(self):
        """Extract voice recording metadata."""
        # Basic voice metadata processing
        try:
            self.processing_metadata = {
                'processed_date': fields.Datetime.now().isoformat(),
                'file_type': 'voice_recording'
            }
            self.processed = True
            self.processing_status = 'completed'
            
        except Exception as e:
            _logger.error(f"Voice processing failed: {e}")
            self.processing_status = 'failed'
    
    def action_reprocess_file(self):
        """Action to reprocess medical file."""
        self.processed = False
        self.processing_status = 'pending'
        self.validation_status = 'pending'
        self._process_medical_file()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    
    def action_preview_medical_file(self):
        """Preview medical file with appropriate viewer"""
        self.ensure_one()
        
        # For medical imaging studies, open the professional viewer
        if self.res_model == 'oeh.medical.imaging' and self.res_id:
            study = self.env['oeh.medical.imaging'].browse(self.res_id)
            if study.exists():
                return study.action_open_professional_dicom_viewer()
        
        # Fallback to individual file preview
        if self.mimetype and self.mimetype.startswith('image/'):
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{self.id}',
                'target': 'new'
            }
        elif self.mimetype == 'application/pdf':
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{self.id}',
                'target': 'new'
            }
        else:
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{self.id}?download=true',
                'target': 'new'
            }