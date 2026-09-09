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
    'name': 'intarvAS - Hospital Management System',
    'version': "19.1.0",
    'author': "IntarvAS",
    'category': 'Generic Modules/Medical',
    'license': 'OPL-1',
    'summary': 'Odoo EMR & HIS based Medical, Health and Hospital Management Solutions',
    'depends': ['web', 'base', 'account', 'product', 'uom', 'hr', 'stock', 'account_edi'],
    'price': 550.00,
    'currency': 'EUR',
    'description': """
        Odoo Hospital Management System
        Hospital Management System
        Hospital Management
        Patient Management
        Patient Information Management
        Electronic Medical Records
        Electronic Health Records
        Medical Staff Management
        Doctors Management
        Therapists Management
        Nurses Management
        Appointment Scheduling
        Schedule Appointments
        Prescriptions Management
        E-prescription
        Generate Prescription
        Inpatient Admission
        Inpatient Management
        Inpatient Hospitalization
        Medical Billing
        Medical Invoicing
        EMR
        EHR 
        Telemedicine 
        Skype
        Zoom
        Jitsi
        """,
    "website": "https://www.intarvas.in",
    "data": [

        'security/oeh_security.xml',

        'oeh_navigation.xml',

        'oeh_settings/oeh_settings_view.xml',

        'oeh_medical/views/oeh_medical_inpatient_view.xml',
        'oeh_medical/views/oeh_medical_view.xml',
        'oeh_medical/views/res_partner_view.xml',
        'oeh_medical/views/product_product_view.xml',
        'oeh_medical/views/oeh_medical_medicaments_view.xml',
        'oeh_medical/views/oeh_medical_pharmacy_view.xml',
        'oeh_medical/views/oeh_medical_healthcenters_view.xml',
        'oeh_medical/views/oeh_medical_pathology_view.xml',
        'oeh_medical/views/account_invoice_view.xml',
        'oeh_medical/views/oeh_medical_insurance_view.xml',
        'oeh_medical/views/oeh_medical_ethnic_groups_view.xml',
        'oeh_medical/views/oeh_medical_genetics_view.xml',
        'oeh_medical/views/oeh_medical_complaints_view.xml',
        'oeh_medical/views/oeh_medical_templates_view.xml',
        'oeh_medical/reports/report_patient_label.xml',
        'oeh_medical/reports/report_medical_staff_badge.xml',
        'oeh_medical/reports/report_patient_medicines.xml',
        'oeh_medical/reports/report_appointment_receipt.xml',
        'oeh_medical/reports/report_patient_prescriptions.xml',
        'oeh_medical/reports/report_appointment_consultation.xml',
        'oeh_medical/reports/appointment_report_action.xml',
        'oeh_medical/views/oeh_medical_report.xml',
        'oeh_medical/wizard/oeh_medical_inpatient_wizard_view.xml',
        'oeh_medical/wizard/oeh_medical_appointment_wizard_view.xml',
        'oeh_medical/wizard/oeh_telmedicine_source_wizard_view.xml',
        'oeh_medical/wizard/oeh_appointment_rejection_wizard_view.xml',
        'oeh_medical/wizard/oeh_patient_webcam_wizard_view.xml',
        'oeh_medical/wizard/oeh_medical_admission_wizard_view.xml',
        'oeh_medical/wizard/oeh_medical_create_user_wizard_view.xml',
        'oeh_medical/views/oeh_medical_physician_user_creation_view.xml',

        # Simplified ICU Management
        'oeh_medical/data/icu_basic_data.xml',
        'oeh_medical/views/oeh_icu_basic_views.xml',

        'oeh_evaluation/views/oeh_medical_evaluation_view.xml',

        'oeh_socioeconomics/views/oeh_medical_socioeconomics_view.xml',

        'oeh_gyneco/views/oeh_medical_gyneco_view.xml',

        'oeh_lifestyle/views/oeh_medical_lifestyle_view.xml',

        'oeh_telemedicine_sources/views/oeh_telemedicine_source_views.xml',

        'oeh_patient_examination/views/oeh_medical_injury_examination.xml',

        'oeh_patient_examination/wizard/oeh_medical_injury_wiz.xml',

        'oeh_patient_examination/reports/oeh_medical_report.xml',
        'oeh_patient_examination/reports/report_injury_examination.xml',

        'oeh_followup/views/oeh_followup_view.xml',
        'oeh_followup/wizard/oeh_followup_wizard_view.xml',

        'oeh_icd10pcs/views/oeh_icd10pcs_view.xml',
        'oeh_patient_medical_history/views/oeh_medical_patient_view.xml',
        'oeh_medical_certificate/views/oeh_medical_certificate_view.xml',
        'oeh_medical_certificate/views/oeh_medical_report.xml',
        'oeh_medical_certificate/views/report_medical_certificate.xml',

        # REST API
        'oeh_rest_api/data/api_token_data.xml',
        'oeh_rest_api/data/ir_cron_data.xml',
        'oeh_rest_api/views/api_view.xml',

        # SECURITY FILES
        'security/oeh_menu_rights.xml',
        'security/ir.model.access.csv',
        'security/ir.rule.xml',
        'sequence/oeh_sequence.xml',

        # DATA FILES
        'oeh_medical/data/oeh_physician_specialities.xml',
        'oeh_medical/data/oeh_physician_degrees.xml',
        'oeh_medical/data/oeh_insurance_types.xml',
        'oeh_medical/data/oeh_ethnic_groups.xml',
        'oeh_medical/data/oeh_chief_complaints.xml',
        'oeh_medical/data/oeh_medical_complaint_templates.xml',
        'oeh_medical/data/oeh_medical_advice_templates.xml',
        'oeh_medical/data/oeh_who_medicaments.xml',
        'oeh_medical/data/oeh_dose_units.xml',
        'oeh_medical/data/oeh_drug_administration_routes.xml',
        'oeh_medical/data/oeh_drug_form.xml',
        'oeh_medical/data/oeh_dose_frequencies.xml',
        'oeh_medical/data/oeh_genetic_risks.xml',
        'oeh_medical/data/oeh_medical_prescription_templates.xml',
        'oeh_medical/data/oeh_prescription_email_template.xml',
        'oeh_medical/data/appointment_email_templates.xml',
        'oeh_medical/data/appointment_cron_job.xml',
        'oeh_socioeconomics/data/oeh_occupations.xml',
        'oeh_lifestyle/data/oeh_recreational_drugs.xml',
        'oeh_medical/data/oeh_disease_categories.xml',
        'oeh_medical/data/oeh_diseases.xml',
        'oeh_medical/data/oeh_meeting_email_template.xml',
        'oeh_icd10pcs/data/oeh_icd_10_pcs_2009_part1.xml',
        'oeh_icd10pcs/data/oeh_icd_10_pcs_2009_part2.xml',
        'oeh_icd10pcs/data/oeh_icd_10_pcs_2009_part3.xml',

        # REPORTING MODULE
        'oeh_reporting/views/appointment_report_views.xml',
        'oeh_reporting/views/patient_registration_report_views.xml',
        'oeh_reporting/views/admission_report_views.xml',
        'oeh_reporting/views/revenue_report_views.xml',
        'oeh_reporting/views/doctor_performance_report_views.xml',
        'oeh_reporting/views/disease_prevalence_report_views.xml',
        'oeh_reporting/views/bed_occupancy_report_views.xml',
        'oeh_reporting/views/appointment_wait_time_report_views.xml',
        'oeh_reporting/views/reporting_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'intarvas/static/src/css/intarvas.css',
            'intarvas/static/src/css/many2many_tags_display.css',
            'intarvas/static/src/js/many2many_tags_display.js',
            'intarvas/static/src/js/patient_webcam_wizard.js',
            'intarvas/static/src/js/widgets/many2one_avatar_patient.js',
            'intarvas/static/src/js/widgets/many2one_avatar_physician.js',
            'intarvas/static/src/js/widgets/name_avatar_patient.js',
            'intarvas/static/src/js/widgets/name_avatar_physician.js',
            'intarvas/static/src/xml/many2many_tags_display.xml',
            'intarvas/static/src/xml/many2one_avatar_widgets.xml',
        ],
    },
    "active": False,
    "sequence": 0,
}