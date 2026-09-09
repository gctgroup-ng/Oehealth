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
{
    'name': 'intarvAS - Radiology Management',
    'version': "19.0.0.0",
    'category': 'Generic Modules/Medical',
    'license': 'OPL-1',
    'author': 'IntarvAS',
    'website': 'https://www.intarvas.in',
    'depends': ['intarvas', 'web'],
    'price': 50.00,
    'currency': 'EUR',
    'summary': 'Complete Radiology Information System with advanced file management and modern interface.',
    'description': """
        Advanced Radiology Management System
        ====================================
        
        Base radiology management system providing:
        
        * Complete radiology information management
        * Advanced file upload and management
        * Drag-drop file upload interface
        * Mobile-responsive image gallery
        * Unlimited file attachments (images, DICOM, PDF, video, audio)
        * Bulk operations and quality management
        * Structured radiology reporting
        * Digital signatures and workflow management
        * Horizontal file display with dynamic sizing
        
        Supported Formats:
        * Medical Images: JPEG, PNG, TIFF, BMP
        * DICOM files (.dcm) - Basic storage and management
        * Reports: PDF, Word documents
        * Media: MP4 videos, WAV audio
        * Archives: ZIP files for bulk processing
        
        Features:
        * X-ray, CT Scan, MRI, PET Scan, Ultrasound record management
        * Quality assurance tools
        * Patient portal integration
        * Mobile optimization
        
        Professional DICOM Viewer:
        * For advanced DICOM viewing with measurement tools, install the 'intarvas_dicom' module
        * Provides professional medical image viewing, windowing, measurements, and export features
        """,
    'data': [
        'data/oeh_imaging_sequence.xml',
        'data/oeh_imaging_sequences_enhanced.xml',
        'data/oeh_imaging_test_types.xml',
        'data/oeh_imaging_enhanced_data.xml',
        'security/ir.model.access.csv',
        'views/oeh_medical_imaging_view.xml',
        'views/oeh_medical_imaging_protocol_view.xml',
        'views/oeh_medical_radiology_template_view.xml',
        'views/oeh_medical_imaging_report.xml',
        'views/report_patient_imaging.xml',
        'security/ir.rule.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # Medical Imaging CSS
            'intarvas_imaging/static/src/css/medical_imaging.css',
            
            # Medical Files Horizontal Layout
            'intarvas_imaging/static/src/js/medical_files_horizontal.js',
        ],
    },
    'external_dependencies': {
        'python': ['Pillow'],
    },
    'auto_install': False,
}
