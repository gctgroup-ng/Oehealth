# -*- coding: utf-8 -*-
##############################################################################
#    Copyright (C) 2015 - Present, Intarvas (<https://www.intarvas.in>). All Rights Reserved
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
    'name': 'intarvAS: Patient Portal Management',
    'version': "19.0.0.0",
    'category': 'Generic Modules/Medical',
    'license': 'OPL-1',
    'summary': 'Give secure access to your patients to view their details'
    ' and download their medical information',
    'description': """
        Customer Portal Management
        Portal
        Patient Portal
        Patient details
        Patient Records Management
        Patient Record management
        Portal Management
        Patient Portal
        
    """,
    'author': 'IntarvAS',
    'price': 99.00,
    'currency': 'EUR',
    "website": "https://www.intarvas.in",
    'depends': [
        'intarvas',
        'portal',
        'website',
        'payment',
        'account',
        'account_payment',
    ],
    'data': [
        'views/oeh_patient_portal.xml',
        'views/portal_layout_extension.xml',
        'views/modern_patient_portal.xml',
        'views/patient_pages.xml',
        'views/portal_billing_pages.xml',
        'views/portal_lab_results.xml',
        'views/gdpr_compliance.xml',
        'views/family_members.xml',
        'views/reschedule_appointment.xml',
        'views/oeh_patient_details_template.xml',
        'views/oeh_patient_profile_form.xml',
        'views/invoice_payment.xml',
        'views/invoice_minimal.xml',
        'data/oeh_patient_portal_template.xml',
    ],
    'assets': {
        'intarvas_patient_portal.assets_patient_portal': [
            'intarvas_patient_portal/static/src/scss/patient_portal.scss',
            'intarvas_patient_portal/static/src/js/navigation.js',
        ],
        'web.assets_frontend': [
            'intarvas_patient_portal/static/src/js/navigation.js',
        ],
    },
    'auto_install': False,
}
