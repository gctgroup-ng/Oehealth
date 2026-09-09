# -*- coding: utf-8 -*-
##############################################################################
#    Copyright (C) 2015 - Present, Intarvas (<http://www.intarvas.com>). All Rights Reserved
#    intarvas, Hospital Management Solutions

# Odoo Proprietary License v1.0
##############################################################################

# LEGACY CONTROLLER - DEPRECATED
# This file contains only essential patient portal functionality
# Healthcare facility management and registration features have been removed
# New modern portal functionality is in modern_portal_controller.py

import base64
from datetime import datetime
from odoo import http, _
from odoo.http import request, content_disposition
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.addons.portal.controllers.portal import CustomerPortal
import dateutil.parser
import logging

_logger = logging.getLogger(__name__)


# Legacy portal integration removed - handled by modern_portal_controller.py


class LegacyPatientPortal(http.Controller):
    """Legacy patient portal controller - minimal functionality"""

    @http.route(['/patient/portal/<patient_token>'], type='http', auth="user", website=True)
    def legacy_patient_details(self, patient_token=None, **post):
        """Legacy route - redirects to modern portal"""
        patient = request.env['oeh.medical.patient'].sudo().search([
            ('patient_token', '=', patient_token)
        ])
        
        if patient and patient.oeh_patient_user_id:
            # Redirect to modern portal
            return request.redirect('/patient/portal')
        else:
            return request.redirect('/my')

    @http.route(['/patient/portal/card/<int:patient_id>'], type='http', auth='user', website=True)
    def print_patient_card(self, patient_id=False):
        """Print patient card - preserved for functionality"""
        if patient_id:
            patient = request.env['oeh.medical.patient'].sudo().browse(int(patient_id))
            
            # Check if user has access to this patient
            if patient.oeh_patient_user_id.id != request.env.user.id:
                return request.redirect('/patient/portal')
                
            try:
                report_ref = 'intarvas.action_report_patient_label'
                report_sudo = request.env.ref(report_ref).sudo()
                
                if not isinstance(report_sudo, type(request.env['ir.actions.report'])):
                    raise UserError(_("%s is not the reference of a report") % report_ref)
                
                report = request.env['ir.actions.report']
                pdf = report._render_qweb_pdf(
                    report_ref=report_sudo.report_name, 
                    res_ids=[patient_id], 
                    data={'report_type': 'pdf'}
                )[0]
                
                headers = [
                    ('Content-Type', 'application/pdf'),
                    ('Content-Length', len(pdf)),
                    ('Content-Disposition', content_disposition(f"Patient_Card_{patient.identification_code}.pdf"))
                ]
                
                return request.make_response(pdf, headers=headers)
                
            except Exception as e:
                _logger.error(f"Error generating patient card: {e}")
                return request.redirect('/patient/portal?error=card_generation_failed')
        else:
            return request.redirect('/patient/portal')

    @http.route(['/patient/portal/update/img'], type='http', auth="user", website=True)
    def update_patient_profile_img(self, **post):
        """Update patient profile image - preserved for functionality"""
        try:
            files = request.httprequest.files.getlist('attachment')
            partner_id = int(post.get('partner_id'))
            
            # Verify user has access to this partner
            if request.env.user.partner_id.id != partner_id:
                return request.redirect('/patient/portal?error=access_denied')
            
            patient = request.env['oeh.medical.patient'].sudo().search([
                ('partner_id', '=', partner_id)
            ])
            
            if partner_id and files:
                for file in files:
                    attachment = file.read()
                    encoded_image = base64.encodebytes(attachment)
                    
                    partner = request.env['res.partner'].sudo().browse(partner_id)
                    if partner:
                        partner.write({'image_1920': encoded_image})
                        request.env.user.image_1920 = encoded_image
            
            return request.redirect('/patient/portal')
            
        except Exception as e:
            _logger.error(f"Error updating profile image: {e}")
            return request.redirect('/patient/portal?error=image_update_failed')

    @http.route(['/patient/portal/remove/img'], type='http', auth="user", website=True)
    def remove_patient_profile_img(self, **post):
        """Remove patient profile image - preserved for functionality"""
        try:
            partner_id = int(post.get('partner_id'))
            
            # Verify user has access to this partner
            if request.env.user.partner_id.id != partner_id:
                return request.redirect('/patient/portal?error=access_denied')
            
            partner = request.env['res.partner'].sudo().browse(partner_id)
            if partner:
                partner.write({'image_1920': False})
                request.env.user.image_1920 = False
            
            return request.redirect('/patient/portal')
            
        except Exception as e:
            _logger.error(f"Error removing profile image: {e}")
            return request.redirect('/patient/portal?error=image_removal_failed')

    # All healthcare facility management routes have been removed
    # All patient registration routes have been removed
    # Users should use the modern patient portal interface