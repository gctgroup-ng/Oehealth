# -*- coding: utf-8 -*-
##############################################################################
#    Copyright (C) 2015 - Present, Intarvas. All Rights Reserved
#    intarvas, Hospital Management Solutions
##############################################################################

import json
import base64
import calendar
import logging
from datetime import datetime, timedelta
from io import BytesIO
import zipfile

from odoo import http, _
from odoo.http import request, content_disposition
from odoo.exceptions import UserError, AccessError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.addons.portal.controllers.portal import CustomerPortal
import dateutil.parser

# Optional imports with fallback for PDF generation
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Logger instance for the entire module
_logger = logging.getLogger(__name__)


# Portal extension disabled to prevent JavaScript errors
# The portal button will be handled differently to avoid DOM conflicts

class PatientPortalAccessChecker(http.Controller):
    """Separate controller for checking patient portal access without interfering with portal home"""
    
    @http.route(['/patient/portal/check_access'], type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def check_patient_portal_access(self):
        """JSON endpoint to check if current user has patient portal access"""
        try:
            if not request.env.user or request.env.user._is_public():
                return {'has_access': False}
            
            has_access = request.env['oeh.medical.patient'].sudo().search_count([
                ('oeh_patient_user_id', '=', request.env.user.id),
                ('is_portal_access', '=', True)
            ]) > 0
            
            return {'has_access': has_access}
        except Exception as e:
            _logger.error(f"Patient portal access check failed: {e}")
            return {'has_access': False}

class ModernPatientPortal(http.Controller):

    def _get_patient_from_user(self):
        """Get patient record for current user"""
        if not request.env.user or request.env.user._is_public():
            return None

        patient = request.env['oeh.medical.patient'].sudo().search([
            ('oeh_patient_user_id', '=', request.env.user.id)
        ], limit=1)

        return patient if patient else None

    def _format_doctor_name(self, doctor_name):
        """Format doctor name to avoid duplication of Dr. title"""
        if not doctor_name:
            return 'General Appointment'

        name = doctor_name.strip()
        # Check if name already starts with Dr. or Doctor
        if name.lower().startswith('dr.') or name.lower().startswith('doctor '):
            return name

        return f'Dr. {name}'

    def _prepare_portal_values(self, patient):
        """Prepare common values for patient portal"""
        if not patient:
            return {}
            
        values = {
            'patient': patient,
            'user': request.env.user,
            'page_name': 'patient_portal',
        }
        
        # Get upcoming appointments
        upcoming_appointments = request.env['oeh.medical.appointment'].sudo().search([
            ('patient', '=', patient.id),
            ('appointment_date', '>', datetime.today().strftime(DF))
        ], limit=5, order='appointment_date asc')
        
        # Get past appointments
        past_appointments = request.env['oeh.medical.appointment'].sudo().search([
            ('patient', '=', patient.id),
            ('appointment_date', '<', datetime.today().strftime(DF))
        ], limit=5, order='appointment_date desc')
        
        # Get today's appointments
        today_appointments = request.env['oeh.medical.appointment'].sudo().search([
            ('patient', '=', patient.id),
            ('appointment_date', '>=', datetime.today().strftime('%Y-%m-%d 00:00:00')),
            ('appointment_date', '<=', datetime.today().strftime('%Y-%m-%d 23:59:59'))
        ], order='appointment_date asc')
        
        values.update({
            'upcoming_appointments': upcoming_appointments,
            'past_appointments': past_appointments,
            'today_appointments': today_appointments,
        })
        
        return values

    @http.route(['/patient/portal', '/patient/portal/home'], type='http', auth="user", website=True)
    def patient_portal_home(self, **kwargs):
        """Modern Patient Portal Home Page"""
        patient = self._get_patient_from_user()
        if not patient:
            return request.redirect('/my')
            
        values = self._prepare_portal_values(patient)
        return request.render("intarvas_patient_portal.patient_portal_home", values)

    @http.route(['/patient/portal/profile'], type='http', auth="user", website=True)
    def patient_profile(self, **kwargs):
        """Patient Profile Management"""
        patient = self._get_patient_from_user()
        if not patient:
            return request.redirect('/my')
            
        if request.httprequest.method == 'POST':
            return self._update_patient_profile(patient, **kwargs)
            
        values = self._prepare_portal_values(patient)
        values.update({
            'page_title': 'My Profile',
            'countries': request.env['res.country'].sudo().search([]),
            'states': request.env['res.country.state'].sudo().search([]),
        })
        
        return request.render("intarvas_patient_portal.patient_profile", values)

    def _update_patient_profile(self, patient, **post):
        """Update patient profile information"""
        # Map form fields to patient model fields
        field_mapping = {
            'name': 'name',
            'email': 'email',
            'phone': 'phone',
            'mobile': 'mobile',
            'street': 'street',
            'street2': 'street2',
            'city': 'city',
            'zip': 'zip',
            'country_id': 'country_id',
            'state_id': 'state_id',
            'dob': 'dob',
            'gender': 'sex',  # Note: patient model uses 'sex' not 'gender'
            'marital_status': 'marital_status',
            'occupation': 'occupation'
        }
        
        update_vals = {}
        for form_field, model_field in field_mapping.items():
            if form_field in post and post[form_field]:
                try:
                    if model_field in ['country_id', 'state_id']:
                        # Handle Many2one fields
                        update_vals[model_field] = int(post[form_field]) if post[form_field] else False
                    elif model_field == 'dob' and post[form_field]:
                        # Handle date field
                        update_vals[model_field] = datetime.strptime(post[form_field], '%Y-%m-%d').date()
                    else:
                        # Handle regular fields
                        update_vals[model_field] = post[form_field]
                except (ValueError, TypeError) as e:
                    _logger.warning(f"Error processing field {form_field}: {e}")
                    continue
        
        try:
            if update_vals:
                _logger.info(f"Updating patient {patient.id} with values: {update_vals}")
                patient.sudo().write(update_vals)
                _logger.info(f"Successfully updated patient {patient.id}")
            else:
                _logger.warning("No valid fields to update")
            return request.redirect('/patient/portal/profile?success=1')
        except Exception as e:
            _logger.error(f"Error updating patient profile {patient.id}: {str(e)}")
            _logger.error(f"Update values were: {update_vals}")
            import traceback
            _logger.error(f"Full traceback: {traceback.format_exc()}")
            return request.redirect('/patient/portal/profile?error=1')

    @http.route(['/patient/portal/profile/upload-photo'], type='http', auth="user", methods=['POST'], csrf=False)
    def upload_profile_photo(self, **post):
        """Upload patient profile photo"""
        patient = self._get_patient_from_user()
        if not patient:
            return request.make_response(json.dumps({'success': False, 'error': 'Patient not found'}), 
                                       headers=[('Content-Type', 'application/json')])
        
        try:
            profile_photo = request.httprequest.files.get('profile_photo')
            if not profile_photo:
                return request.make_response(json.dumps({'success': False, 'error': 'No photo provided'}), 
                                           headers=[('Content-Type', 'application/json')])
            
            # Validate file type
            if not profile_photo.content_type.startswith('image/'):
                return request.make_response(json.dumps({'success': False, 'error': 'Invalid file type'}), 
                                           headers=[('Content-Type', 'application/json')])
            
            # Read file content and encode
            file_content = profile_photo.read()
            if len(file_content) > 10 * 1024 * 1024:  # 10MB limit
                return request.make_response(json.dumps({'success': False, 'error': 'File too large (max 10MB)'}), 
                                           headers=[('Content-Type', 'application/json')])
            
            image_data = base64.b64encode(file_content)
            
            # Update patient record
            patient.sudo().write({'image_1920': image_data})
            
            return request.make_response(json.dumps({'success': True}), 
                                       headers=[('Content-Type', 'application/json')])
            
        except Exception as e:
            _logger.error(f"Error uploading profile photo: {e}")
            return request.make_response(json.dumps({'success': False, 'error': 'Upload failed'}), 
                                       headers=[('Content-Type', 'application/json')])

    @http.route(['/patient/portal/profile/remove-photo'], type='http', auth="user", methods=['POST'], csrf=False)
    def remove_profile_photo(self, **post):
        """Remove patient profile photo"""
        patient = self._get_patient_from_user()
        if not patient:
            return request.make_response(json.dumps({'success': False, 'error': 'Patient not found'}), 
                                       headers=[('Content-Type', 'application/json')])
        
        try:
            # Remove the image
            patient.sudo().write({'image_1920': False})
            
            return request.make_response(json.dumps({'success': True}), 
                                       headers=[('Content-Type', 'application/json')])
            
        except Exception as e:
            _logger.error(f"Error removing profile photo: {e}")
            return request.make_response(json.dumps({'success': False, 'error': 'Remove failed'}), 
                                       headers=[('Content-Type', 'application/json')])

    @http.route(['/patient/portal/appointments'], type='http', auth="user", website=True)
    def patient_appointments(self, **kwargs):
        """Patient Appointments Management with Calendar View"""
        try:
            patient = self._get_patient_from_user()
            if not patient:
                return request.redirect('/my')
            
            # Get filter parameters
            selected_date = kwargs.get('date', datetime.today().strftime('%Y-%m-%d'))
            selected_date_param = kwargs.get('selected_date')
            doctor_filter = kwargs.get('doctor')
            status_filter = kwargs.get('status')
            
            try:
                selected_date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
            except (ValueError, TypeError) as e:
                _logger.warning(f"Invalid date format received: {selected_date}, error: {e}")
                selected_date_obj = datetime.today().date()
                selected_date = selected_date_obj.strftime('%Y-%m-%d')
            
            # Calculate date ranges for calendar navigation
            today = datetime.today().date()
            start_date = today - timedelta(days=730)  # 2 years ago
            end_date = today + timedelta(days=365)    # 1 year from now
            
            # Calculate navigation dates
            if selected_date_obj.month == 1:
                prev_month = selected_date_obj.replace(year=selected_date_obj.year - 1, month=12)
            else:
                prev_month = selected_date_obj.replace(month=selected_date_obj.month - 1)
                
            if selected_date_obj.month == 12:
                next_month = selected_date_obj.replace(year=selected_date_obj.year + 1, month=1)
            else:
                next_month = selected_date_obj.replace(month=selected_date_obj.month + 1)
            
            # Generate horizontal date bar (15 days around selected date)
            date_bar = self._generate_horizontal_date_bar(selected_date_obj, 15)
            
            # Get appointments for calendar view (expand range to cover date bar)
            date_bar_start = selected_date_obj - timedelta(days=30)  # Start 30 days before
            date_bar_end = selected_date_obj + timedelta(days=30)    # End 30 days after
            
            # Build domain for appointments query
            domain = [
                ('patient', '=', patient.id),
                ('appointment_date', '>=', date_bar_start.strftime('%Y-%m-%d 00:00:00')),
                ('appointment_date', '<=', date_bar_end.strftime('%Y-%m-%d 23:59:59'))
            ]
            
            if doctor_filter:
                try:
                    domain.append(('doctor', '=', int(doctor_filter)))
                except (ValueError, TypeError) as e:
                    _logger.warning(f"Invalid doctor_filter format: {doctor_filter}, error: {e}")
                    doctor_filter = None  # Reset to avoid further issues
            if status_filter:
                domain.append(('state', '=', status_filter))
            
            month_appointments = request.env['oeh.medical.appointment'].sudo().search(domain, order='appointment_date asc')
            _logger.info(f"Found {len(month_appointments)} appointments for patient {patient.id} between {date_bar_start} and {date_bar_end}")
            
            # Log today's appointments specifically
            today_str = datetime.now().date().strftime('%Y-%m-%d')
            today_appointments = [apt for apt in month_appointments if apt.appointment_date.date().strftime('%Y-%m-%d') == today_str]
            _logger.info(f"Today ({today_str}) appointments: {len(today_appointments)}")
            for apt in today_appointments:
                _logger.info(f"  - Appointment ID: {apt.id}, Date: {apt.appointment_date}, State: {apt.state}")
            
            # Group appointments by date for calendar display
            appointments_by_date = {}
            for appointment in month_appointments:
                app_date = appointment.appointment_date.date().strftime('%Y-%m-%d')
                if app_date not in appointments_by_date:
                    appointments_by_date[app_date] = []
                appointments_by_date[app_date].append(appointment)
            
            # Get appointments for selected date (if selected_date_param is provided)
            selected_date_appointments = []
            if selected_date_param:
                try:
                    selected_display_date = datetime.strptime(selected_date_param, '%Y-%m-%d').date()
                    selected_date_appointments = request.env['oeh.medical.appointment'].sudo().search([
                        ('patient', '=', patient.id),
                        ('appointment_date', '>=', selected_date_param + ' 00:00:00'),
                        ('appointment_date', '<=', selected_date_param + ' 23:59:59')
                    ] + ([('doctor', '=', int(doctor_filter))] if doctor_filter and doctor_filter.isdigit() else []) + 
                       ([('state', '=', status_filter)] if status_filter else []), 
                    order='appointment_date asc')
                except (ValueError, TypeError) as e:
                    _logger.warning(f"Invalid selected_date_param format: {selected_date_param}, error: {e}")
                    selected_display_date = selected_date_obj
                    selected_date_appointments = []
            else:
                # Default to current selected date
                selected_display_date = selected_date_obj
                selected_date_appointments = request.env['oeh.medical.appointment'].sudo().search([
                    ('patient', '=', patient.id),
                    ('appointment_date', '>=', selected_date + ' 00:00:00'),
                    ('appointment_date', '<=', selected_date + ' 23:59:59')
                ] + ([('doctor', '=', int(doctor_filter))] if doctor_filter and doctor_filter.isdigit() else []) + 
                   ([('state', '=', status_filter)] if status_filter else []), 
                order='appointment_date asc')
            
            # Get doctors and states for filters
            doctors = request.env['oeh.medical.physician'].sudo().search([('is_pharmacist', '=', False)], order='name')
            appointment_states = [
                ('Scheduled', 'Scheduled'),
                ('Accepted', 'Accepted'), 
                ('Completed', 'Completed'),
                ('Invoiced', 'Invoiced'),
                ('Cancelled', 'Cancelled'),
                ('Rejected', 'Rejected')
            ]
            
            values = {
                'patient': patient,
                'user': request.env.user,
                'page_name': 'appointments',
                'page_title': 'My Appointments',
                'selected_date': selected_date,
                'selected_date_obj': selected_date_obj,
                'selected_display_date': selected_display_date,
                'current_date': selected_date_obj,
                'prev_month': prev_month,
                'next_month': next_month,
                'date_bar': date_bar,
                'month_appointments': month_appointments,
                'appointments_by_date': appointments_by_date,
                'selected_date_appointments': selected_date_appointments,
                'doctors': doctors,
                'appointment_states': appointment_states,
                'doctor_filter': doctor_filter,
                'status_filter': status_filter,
                'selected_doctor': int(doctor_filter) if doctor_filter else None,
                'selected_status': status_filter,
                'start_date': start_date,
                'end_date': end_date,
                'datetime': datetime,
                'current_datetime': datetime.now(),
            }
            
            return request.render("intarvas_patient_portal.patient_appointments_calendar", values)
            
        except Exception as e:
            _logger.error(f"Error in patient_appointments: {e}")
            _logger.exception("Full traceback:")
            # Fallback to basic appointment list on error
            try:
                patient = self._get_patient_from_user()
                if not patient:
                    return request.redirect('/my')
                    
                basic_appointments = request.env['oeh.medical.appointment'].sudo().search([
                    ('patient', '=', patient.id)
                ], order='appointment_date desc', limit=10)
                
                return request.render("intarvas_patient_portal.patient_appointments", {
                    'patient': patient,
                    'upcoming_appointments': basic_appointments.filtered(lambda a: a.appointment_date >= datetime.now()),
                    'past_appointments': basic_appointments.filtered(lambda a: a.appointment_date < datetime.now()),
                })
            except:
                return request.redirect('/my')

    def _generate_calendar_weeks(self, current_date):
        """Generate calendar weeks for the entire month containing current_date"""
        try:
            # Ensure current_date is a date object, not datetime
            if isinstance(current_date, datetime):
                current_date = current_date.date()
            elif not hasattr(current_date, 'year'):
                _logger.error(f"Invalid current_date type: {type(current_date)}, value: {current_date}")
                current_date = datetime.today().date()
            
            # Get first day of the month
            first_day = current_date.replace(day=1)
            
            # Get last day of the month
            if first_day.month == 12:
                last_day = first_day.replace(year=first_day.year + 1, month=1) - timedelta(days=1)
            else:
                last_day = first_day.replace(month=first_day.month + 1) - timedelta(days=1)
            
            # Find the Monday of the week containing the first day of month
            start_week = first_day - timedelta(days=first_day.weekday())
            
            # Find the Sunday of the week containing the last day of month
            end_week = last_day + timedelta(days=(6 - last_day.weekday()))
            
            weeks = []
            current_week_start = start_week
            today = datetime.now().date()
            
            while current_week_start <= end_week:
                week_days = []
                for i in range(7):  # 7 days in a week (Monday to Sunday)
                    day = current_week_start + timedelta(days=i)
                    week_days.append({
                        'date': day,
                        'is_current_month': day.month == current_date.month,
                        'is_today': day == today,
                        'is_past': day < today,
                        'day_name': day.strftime('%a'),
                        'day_number': day.day,
                    })
                weeks.append(week_days)
                current_week_start += timedelta(days=7)
                
            return weeks
            
        except Exception as e:
            _logger.error(f"Error generating calendar weeks: {e}")
            # Return a minimal calendar for current month as fallback
            today = datetime.today().date()
            return [[{
                'date': today,
                'is_current_month': True,
                'is_today': True,
                'is_past': False,
                'day_name': today.strftime('%a'),
                'day_number': today.day,
            }]]

    def _generate_horizontal_date_bar(self, selected_date, days_count=15):
        """Generate horizontal date bar showing days around the selected date"""
        try:
            # Ensure selected_date is a date object
            if isinstance(selected_date, datetime):
                selected_date = selected_date.date()
            elif not hasattr(selected_date, 'year'):
                _logger.error(f"Invalid selected_date type: {type(selected_date)}")
                selected_date = datetime.today().date()
            
            # Calculate start date (7 days before selected date for better range)
            start_date = selected_date - timedelta(days=7)
            
            date_bar = []
            today = datetime.now().date()
            
            for i in range(days_count):
                current_date = start_date + timedelta(days=i)
                date_bar.append({
                    'date': current_date,
                    'day_name': current_date.strftime('%a').upper(),  # MON, TUE, WED, etc.
                    'day_number': current_date.day,
                    'month_name': current_date.strftime('%b'),  # Jan, Feb, Mar, etc.
                    'is_selected': current_date == selected_date,
                    'date_string': current_date.strftime('%Y-%m-%d')
                })
            
            return date_bar
            
        except Exception as e:
            _logger.error(f"Error generating horizontal date bar: {e}")
            # Return fallback date bar with just today
            today = datetime.today().date()
            return [{
                'date': today,
                'day_name': today.strftime('%a').upper(),
                'day_number': today.day,
                'month_name': today.strftime('%b'),
                'is_today': True,
                'is_selected': True,
                'is_past': False,
                'is_weekend': today.weekday() >= 5,
                'date_string': today.strftime('%Y-%m-%d')
            }]

    @http.route(['/patient/portal/appointments/ajax'], type='http', auth="user", methods=['GET'])
    def appointments_ajax(self, selected_date=None, doctor=None, status=None, **kwargs):
        """AJAX endpoint to load appointments for a specific date"""
        try:
            patient = self._get_patient_from_user()
            if not patient:
                return request.make_json_response({'error': 'Patient not found'}, status=401)
            
            # Parse the selected date
            if not selected_date:
                return request.make_json_response({'appointments': []})
                
            try:
                selected_date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
            except ValueError:
                return request.make_json_response({'error': 'Invalid date format'}, status=400)
            
            # Build appointment search domain
            domain = [
                ('patient', '=', patient.id),
                ('appointment_date', '>=', datetime.combine(selected_date_obj, datetime.min.time())),
                ('appointment_date', '<', datetime.combine(selected_date_obj + timedelta(days=1), datetime.min.time()))
            ]
            
            # Apply filters
            if doctor and doctor != '':
                domain.append(('doctor', '=', int(doctor)))
            if status and status != '':
                domain.append(('state', '=', status.lower()))
            
            # Get appointments
            _logger.info(f"Searching for appointments with domain: {domain}")
            appointments = request.env['oeh.medical.appointment'].sudo().search(
                domain, order='appointment_date asc'
            )
            _logger.info(f"Found {len(appointments)} appointments for date {selected_date}")
            
            # Format appointments for JSON response
            appointments_data = []
            for appointment in appointments:
                try:
                    _logger.info(f"Processing appointment {appointment.id} - {appointment.name}")
                    _logger.info(f"  Doctor: {appointment.doctor.name if appointment.doctor else 'None'}")
                    _logger.info(f"  Doctor specialty: {getattr(appointment.doctor, 'specialty', 'No specialty attr') if appointment.doctor else 'No doctor'}")
                    _logger.info(f"  Appointment name field: '{appointment.name}'")
                    
                    # Safe image encoding
                    doctor_image = None
                    if appointment.doctor and appointment.doctor.image_128:
                        try:
                            # image_128 is already base64 encoded in Odoo
                            doctor_image = appointment.doctor.image_128.decode() if isinstance(appointment.doctor.image_128, bytes) else appointment.doctor.image_128
                        except Exception as e:
                            _logger.warning(f"Error processing doctor image for appointment {appointment.id}: {e}")
                            doctor_image = None
                    
                    # Safe date formatting
                    appointment_date_iso = None
                    if appointment.appointment_date:
                        try:
                            appointment_date_iso = appointment.appointment_date.isoformat()
                        except Exception as e:
                            _logger.warning(f"Error formatting date for appointment {appointment.id}: {e}")
                            appointment_date_iso = str(appointment.appointment_date)
                    
                    appointments_data.append({
                        'id': appointment.id,
                        'name': appointment.name or 'Untitled Appointment',
                        'appointment_date': appointment_date_iso,
                        'doctor_name': self._format_doctor_name(appointment.doctor.name) if appointment.doctor else 'General Appointment',
                        'doctor_image': doctor_image,
                        'doctor_degrees': ', '.join(appointment.doctor.degree_id.mapped('name')) if appointment.doctor and appointment.doctor.degree_id else None,
                        'doctor_specialty': appointment.doctor.speciality.name if appointment.doctor and appointment.doctor.speciality else None,
                        'institution_name': getattr(appointment, 'institution', None) and appointment.institution.name or None,
                        'state': appointment.state or 'unknown',
                        'appointment_type': getattr(appointment, 'appointment_type', None) or getattr(appointment, 'visit_type', None) or 'Regular',
                        'priority': getattr(appointment, 'priority', None) or 'normal',
                        'online_meeting_link': getattr(appointment, 'meeting_link', None) or getattr(appointment, 'online_link', None) or None,
                        'consultation_type': getattr(appointment, 'consultation_type', None) or None,
                        'notes': getattr(appointment, 'appointment_notes', None) or getattr(appointment, 'notes', None) or '',
                        'duration': getattr(appointment, 'duration', None) or '30 min',
                    })
                    
                except Exception as e:
                    _logger.error(f"Error processing individual appointment {appointment.id}: {e}")
                    # Skip this appointment and continue with others
                    continue
            
            response_data = {
                'appointments': appointments_data,
                'selected_date': selected_date,
                'count': len(appointments_data)
            }
            return request.make_json_response(response_data)
            
        except Exception as e:
            _logger.error(f"Error in appointments AJAX for date {selected_date}: {e}")
            import traceback
            _logger.error(f"Full traceback: {traceback.format_exc()}")
            error_data = {'error': f'Failed to load appointments: {str(e)}'}
            return request.make_json_response(error_data, status=500)

    @http.route(['/patient/portal/appointments/new'], type='http', auth="user", website=True)
    def new_appointment(self, **kwargs):
        """Create New Appointment"""
        patient = self._get_patient_from_user()
        if not patient:
            return request.redirect('/my')
            
        if request.httprequest.method == 'POST':
            return self._create_appointment(patient, **kwargs)
            
        values = self._prepare_portal_values(patient)
        values.update({
            'page_title': 'Book Appointment',
            'doctors': request.env['oeh.medical.physician'].sudo().search([('is_pharmacist', '=', False)]),
            'institutions': request.env['oeh.medical.health.center'].sudo().search([]),
        })
        
        return request.render("intarvas_patient_portal.new_appointment", values)

    def _create_appointment(self, patient, **post):
        """Create new appointment"""
        
        try:
            # Log the received data for debugging
            _logger.info(f"Creating appointment with data: {post}")
            
            # Parse appointment date - handle different formats
            appointment_date = post.get('appointment_date')
            if not appointment_date:
                _logger.error("No appointment date provided")
                return request.redirect('/patient/portal/appointments/new?error=no_date')
                
            # Try to parse the datetime
            try:
                parsed_date = dateutil.parser.parse(appointment_date)
            except Exception as date_error:
                _logger.error(f"Failed to parse appointment date '{appointment_date}': {date_error}")
                return request.redirect('/patient/portal/appointments/new?error=invalid_date')
            
            appointment_vals = {
                'patient': patient.id,
                'doctor': int(post.get('doctor')) if post.get('doctor') else False,
                'institution': int(post.get('institution')) if post.get('institution') else False,
                'appointment_date': parsed_date,
                'duration': 0.5,
                'reason': post.get('reason', ''),
                'state': 'Scheduled',
                'patient_status': 'Outpatient',
                'urgency_level': post.get('priority', 'Normal'),
            }
            # Check if appointment model exists
            if 'oeh.medical.appointment' not in request.env:
                _logger.error("oeh.medical.appointment model not found")
                return request.redirect('/patient/portal/appointments/new?error=model_not_found')
            
            appointment = request.env['oeh.medical.appointment'].sudo().create(appointment_vals)
            _logger.info(f"Appointment created successfully with ID: {appointment.id}")
            
            # Handle file uploads
            files = request.httprequest.files.getlist('appointment_files')
            if files:
                self._process_appointment_files(appointment, files)
                
            return request.redirect('/patient/portal/appointments?success=appointment_created')
            
        except Exception as e:
            _logger.error(f"Failed to create appointment: {e}")
            _logger.exception("Full traceback:")
            return request.redirect('/patient/portal/appointments/new?error=creation_failed')
    
    def _process_appointment_files(self, appointment, files):
        """Process uploaded files and attach them to appointment"""
        
        try:
            for file in files:
                if file and file.filename:
                    # Read file content
                    file_content = file.read()
                    if not file_content:
                        continue
                        
                    # Create attachment
                    attachment_vals = {
                        'name': file.filename,
                        'datas': base64.b64encode(file_content),
                        'res_model': 'oeh.medical.appointment',
                        'res_id': appointment.id,
                        'mimetype': file.content_type or 'application/octet-stream',
                        'public': False,
                    }
                    
                    attachment = request.env['ir.attachment'].sudo().create(attachment_vals)
                    _logger.info(f"Created attachment {attachment.id} for appointment {appointment.id}")
                    
                    # Post message in chatter
                    appointment.sudo().message_post(
                        body=f"Document uploaded: {file.filename}",
                        attachment_ids=[attachment.id],
                        message_type='comment',
                        subtype_xmlid='mail.mt_comment'
                    )
                    
        except Exception as e:
            _logger.error(f"Error processing appointment files: {e}")
            _logger.exception("File processing error:")

    @http.route(['/patient/portal/appointment/<int:appointment_id>/reschedule'], type='http', auth="user", website=True)
    def reschedule_appointment(self, appointment_id, **kwargs):
        """Reschedule Appointment"""
        patient = self._get_patient_from_user()
        if not patient:
            return request.redirect('/my')
        
        # Get appointment and verify it belongs to current patient
        appointment = request.env['oeh.medical.appointment'].sudo().search([
            ('id', '=', appointment_id),
            ('patient', '=', patient.id)
        ], limit=1)
        
        if not appointment:
            return request.redirect('/patient/portal/appointments?error=appointment_not_found')
        
        if request.httprequest.method == 'POST':
            return self._update_appointment(appointment, **kwargs)
            
        values = self._prepare_portal_values(patient)
        values.update({
            'page_title': 'Reschedule Appointment',
            'appointment': appointment,
            'doctors': request.env['oeh.medical.physician'].sudo().search([('is_pharmacist', '=', False)]),
            'institutions': request.env['oeh.medical.health.center'].sudo().search([]),
        })
        
        return request.render("intarvas_patient_portal.reschedule_appointment", values)

    @http.route(['/patient/portal/appointment/<int:appointment_id>/cancel'], type='http', auth="user", website=True, methods=['POST'])
    def cancel_appointment(self, appointment_id, **kwargs):
        """Cancel Appointment"""
        patient = self._get_patient_from_user()
        if not patient:
            return request.redirect('/my')
        
        # Get appointment and verify it belongs to current patient
        appointment = request.env['oeh.medical.appointment'].sudo().search([
            ('id', '=', appointment_id),
            ('patient', '=', patient.id)
        ], limit=1)
        
        if not appointment:
            return request.redirect('/patient/portal/appointments?error=appointment_not_found')
        
        try:
            # Update appointment status to cancelled
            appointment.sudo().write({'state': 'Cancelled'})
            
            # Add message to chatter
            appointment.sudo().message_post(
                body="Appointment cancelled by patient via portal",
                message_type='comment',
                subtype_xmlid='mail.mt_comment'
            )
            
            return request.redirect('/patient/portal/appointments?success=appointment_cancelled')
            
        except Exception as e:
            _logger.error(f"Failed to cancel appointment: {e}")
            return request.redirect('/patient/portal/appointments?error=cancellation_failed')

    def _update_appointment(self, appointment, **post):
        """Update existing appointment"""
        
        try:
            # Parse appointment date
            appointment_date = post.get('appointment_date')
            if not appointment_date:
                return request.redirect(f'/patient/portal/appointment/{appointment.id}/reschedule?error=no_date')
                
            try:
                parsed_date = dateutil.parser.parse(appointment_date)
            except Exception as date_error:
                _logger.error(f"Failed to parse appointment date '{appointment_date}': {date_error}")
                return request.redirect(f'/patient/portal/appointment/{appointment.id}/reschedule?error=invalid_date')
            
            appointment_vals = {
                'doctor': int(post.get('doctor')) if post.get('doctor') else appointment.doctor.id,
                'institution': int(post.get('institution')) if post.get('institution') else appointment.institution.id,
                'appointment_date': parsed_date,
                'duration': float(post.get('duration', appointment.duration or 1.0)),
                'reason': post.get('reason', appointment.reason or ''),
                'urgency_level': post.get('priority', 'Normal'),
            }
            
            appointment.sudo().write(appointment_vals)
            
            # Add message to chatter
            appointment.sudo().message_post(
                body="Appointment rescheduled by patient via portal",
                message_type='comment',
                subtype_xmlid='mail.mt_comment'
            )
            
            _logger.info(f"Appointment {appointment.id} rescheduled successfully")
            return request.redirect('/patient/portal/appointments?success=appointment_rescheduled')
            
        except Exception as e:
            _logger.error(f"Failed to reschedule appointment: {e}")
            _logger.exception("Full traceback:")
            return request.redirect(f'/patient/portal/appointment/{appointment.id}/reschedule?error=update_failed')

    @http.route(['/patient/portal/medical-records'], type='http', auth="user", website=True)
    def medical_records(self, **kwargs):
        """Patient Medical Records"""
        patient = self._get_patient_from_user()
        if not patient:
            return request.redirect('/my')
            
        values = self._prepare_portal_values(patient)
        
        # Get medical evaluations
        evaluations = request.env['oeh.medical.evaluation'].sudo().search([
            ('patient', '=', patient.id)
        ], order='evaluation_start_date desc', limit=20)
        
        # Get medical certificates
        certificates = request.env['oeh.medical.patient.medical.cert'].sudo().search([
            ('patient', '=', patient.id)
        ], order='issue_date desc', limit=20)
        
        values.update({
            'page_title': 'Medical Records',
            'evaluations': evaluations,
            'certificates': certificates,
        })
        
        return request.render("intarvas_patient_portal.medical_records", values)

    @http.route(['/patient/portal/family', '/patient/portal/family-members'], type='http', auth="user", website=True)
    def family_members(self, **kwargs):
        """Patient Family Members"""
        patient = self._get_patient_from_user()
        if not patient:
            return request.redirect('/my')
            
        if request.httprequest.method == 'POST':
            return self._manage_family_member(patient, **kwargs)
            
        values = self._prepare_portal_values(patient)
        
        family_members = request.env['oeh.medical.patient.family'].sudo().search([
            ('patient_id', '=', patient.id)
        ], order='name')
        
        values.update({
            'page_title': 'Family Members',
            'family_members': family_members,
        })
        
        return request.render("intarvas_patient_portal.family_members", values)

    def _manage_family_member(self, patient, **post):
        """Add, update, or delete family member"""
        try:
            action = post.get('action', 'add')
            
            if action == 'delete':
                # Delete family member
                family_id = post.get('family_id')
                if family_id:
                    family_member = request.env['oeh.medical.patient.family'].sudo().browse(int(family_id))
                    if family_member.exists() and family_member.patient_id.id == patient.id:
                        family_member.unlink()
                        return request.redirect('/patient/portal/family-members?success=family_member_deleted')
                return request.redirect('/patient/portal/family-members?error=delete_failed')
            
            elif action in ['add', 'edit']:
                # Prepare family member data
                family_vals = {
                    'patient_id': patient.id,
                    'name': post.get('name', '').strip(),
                }
                
                # Only add non-empty optional fields
                if post.get('relation', '').strip():
                    family_vals['relation'] = post.get('relation', '').strip()
                if post.get('email', '').strip():
                    family_vals['email'] = post.get('email', '').strip()
                if post.get('phone', '').strip():
                    family_vals['contact_no'] = post.get('phone', '').strip()
                if post.get('age', '').strip():
                    try:
                        family_vals['age'] = int(post.get('age'))
                    except (ValueError, TypeError):
                        family_vals['age'] = 0
                
                if action == 'edit':
                    # Update existing family member
                    family_id = post.get('family_id')
                    if family_id:
                        try:
                            family_member = request.env['oeh.medical.patient.family'].sudo().browse(int(family_id))
                            if family_member.exists() and family_member.patient_id.id == patient.id:
                                family_member.write(family_vals)
                                return request.redirect('/patient/portal/family-members?success=family_member_updated')
                            else:
                                _logger.error("Family member not found or access denied: ID=%s, Patient=%s", family_id, patient.id)
                                return request.redirect('/patient/portal/family-members?error=access_denied')
                        except ValueError:
                            _logger.error("Invalid family_id format: %s", family_id)
                            return request.redirect('/patient/portal/family-members?error=invalid_id')
                    return request.redirect('/patient/portal/family-members?error=missing_id')
                else:
                    # Create new family member
                    if not family_vals.get('name'):
                        return request.redirect('/patient/portal/family-members?error=name_required')
                    
                    request.env['oeh.medical.patient.family'].sudo().create(family_vals)
                    return request.redirect('/patient/portal/family-members?success=family_member_added')
            
            return request.redirect('/patient/portal/family-members?error=invalid_action')
            
        except Exception as e:
            # Logging imported at top of file
            _logger.error("Family member management error: %s", str(e))
            return request.redirect('/patient/portal/family-members?error=general')

    @http.route(['/patient/portal/messages'], type='http', auth="user", website=True)
    def messages(self, **kwargs):
        """Patient Messages"""
        patient = self._get_patient_from_user()
        if not patient:
            return request.redirect('/my')
            
        values = self._prepare_portal_values(patient)
        values['page_name'] = 'messages'
        
        # Get messages from mail.message or create dummy data for demo
        try:
            messages = request.env['mail.message'].sudo().search([
                ('res_id', '=', patient.id),
                ('model', '=', 'oeh.medical.patient')
            ], order='date desc', limit=50)
        except:
            # Create some dummy messages for demo purposes
            messages = []
        
        values.update({
            'page_title': 'Messages',
            'messages': messages,
        })
        
        return request.render("intarvas_patient_portal.patient_messages", values)

    @http.route(['/patient/portal/lab-results'], type='http', auth="user", website=True)
    def lab_results(self, **kwargs):
        """Patient Lab Results"""
        patient = self._get_patient_from_user()
        if not patient:
            return request.redirect('/my')
            
        values = self._prepare_portal_values(patient)
        
        # Get lab tests with error handling
        try:
            progress_labtest = request.env['oeh.medical.lab.test'].sudo().search([
                ('patient', '=', patient.id), 
                ('state', 'in', ('Draft', 'Test In Progress'))
            ])
            
            completed_labtest = request.env['oeh.medical.lab.test'].sudo().search([
                ('patient', '=', patient.id), 
                ('state', '=', 'Completed')
            ])
        except Exception as e:
            # Logging imported at top of file
            _logger.error(f"Error fetching lab tests: {e}")
            progress_labtest = request.env['oeh.medical.lab.test'].sudo().browse([])
            completed_labtest = request.env['oeh.medical.lab.test'].sudo().browse([])
        
        # Get lab requests with error handling
        try:
            lab_requests = request.env['oeh.medical.lab.request'].sudo().search([
                ('patient', '=', patient.id)
            ])
        except Exception as e:
            # Logging imported at top of file
            _logger.error(f"Error fetching lab requests: {e}")
            lab_requests = request.env['oeh.medical.lab.request'].sudo().browse([])
        
        values.update({
            'page_title': 'Lab Results',
            'progress_labtest': progress_labtest,
            'completed_labtest': completed_labtest,
            'lab_requests': lab_requests,
            'labtest_available': bool(progress_labtest or completed_labtest),
            'lab_request_available': bool(lab_requests),
        })
        
        return request.render("intarvas_patient_portal.lab_results", values)

    @http.route(['/patient/portal/prescriptions'], type='http', auth="user", website=True)
    def prescriptions(self, **kwargs):
        """Patient prescriptions page"""
        patient = self._get_patient_from_user()
        if not patient:
            return request.redirect('/my')
            
        values = self._prepare_portal_values(patient)
        values['page_name'] = 'prescriptions'
        
        # Get prescriptions - check if oeh.medical.prescription model exists
        try:
            current_prescriptions = request.env['oeh.medical.prescription'].sudo().search([
                ('patient', '=', patient.id),
                ('state', 'in', ['Draft', 'Invoiced', 'Sent to Pharmacy'])
            ], order='create_date desc', limit=50)
            
            past_prescriptions = request.env['oeh.medical.prescription'].sudo().search([
                ('patient', '=', patient.id)
            ], order='create_date desc', limit=50)
        except Exception as e:
            # If prescription model doesn't exist or error, return empty list
            current_prescriptions = []
            past_prescriptions = []
        
        values.update({
            'page_title': 'Prescriptions',
            'current_prescriptions': current_prescriptions,
            'past_prescriptions': past_prescriptions,
            'prescriptions': current_prescriptions + past_prescriptions,
        })
        
        return request.render("intarvas_patient_portal.patient_prescriptions", values)

    @http.route(['/patient/portal/prescription/<int:prescription_id>'], type='http', auth="user", website=True)
    def prescription_detail(self, prescription_id, **kwargs):
        """Prescription detail page"""
        patient = self._get_patient_from_user()
        if not patient:
            return request.redirect('/my')
        
        try:
            # Get the prescription and verify it belongs to this patient
            prescription = request.env['oeh.medical.prescription'].sudo().search([
                ('id', '=', prescription_id),
                ('patient', '=', patient.id)
            ], limit=1)
            
            if not prescription:
                return request.redirect('/patient/portal/prescriptions?error=prescription_not_found')
            
            values = self._prepare_portal_values(patient)
            values.update({
                'page_title': f'Prescription {prescription.name}',
                'prescription': prescription,
                'page_name': 'prescriptions'
            })
            
            return request.render("intarvas_patient_portal.prescription_detail", values)
            
        except Exception as e:
            _logger.error(f"Error loading prescription {prescription_id}: {e}")
            return request.redirect('/patient/portal/prescriptions?error=access_denied')

    @http.route(['/patient/portal/prescription/<int:prescription_id>/download'], type='http', auth="user")
    def prescription_download(self, prescription_id, **kwargs):
        """Download prescription as PDF"""
        patient = self._get_patient_from_user()
        if not patient:
            return request.redirect('/my')
        
        try:
            # Get the prescription and verify it belongs to this patient
            prescription = request.env['oeh.medical.prescription'].sudo().search([
                ('id', '=', prescription_id),
                ('patient', '=', patient.id)
            ], limit=1)
            
            if not prescription:
                return request.redirect('/patient/portal/prescriptions?error=prescription_not_found')
            
            # Check if prescription report exists
            report = request.env.ref('intarvas.action_oeh_medical_report_patient_prescriptions', raise_if_not_found=False)
            if report:
                # Use existing prescription report
                pdf_content, content_type = report.sudo()._render_qweb_pdf([prescription.id])
                filename = f"prescription_{prescription.name.replace('/', '_')}.pdf"
                
                return request.make_response(
                    pdf_content,
                    headers=[
                        ('Content-Type', content_type),
                        ('Content-Disposition', f'attachment; filename="{filename}"')
                    ]
                )
            else:
                # Fallback: Generate simple HTML prescription report
                return self._generate_prescription_html_report(prescription)
                
        except Exception as e:
            _logger.error(f"Error downloading prescription {prescription_id}: {e}")
            return request.redirect('/patient/portal/prescriptions?error=download_failed')
    
    def _generate_prescription_html_report(self, prescription):
        """Generate simple HTML prescription report when PDF report is not available"""
        try:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Prescription - {prescription.name}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }}
                    .prescription-info {{ margin-bottom: 30px; }}
                    .medicine-item {{ border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; border-radius: 5px; }}
                    .medicine-name {{ font-weight: bold; color: #333; font-size: 16px; }}
                    .dosage {{ color: #666; margin: 5px 0; }}
                    .instructions {{ background: #f9f9f9; padding: 10px; border-left: 4px solid #007bff; margin-top: 10px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Prescription</h1>
                    <p><strong>Prescription No:</strong> {prescription.name}</p>
                    <p><strong>Date:</strong> {prescription.date.strftime('%B %d, %Y') if prescription.date else 'N/A'}</p>
                    {f"<p><strong>Doctor:</strong> {self._format_doctor_name(prescription.doctor.name)}</p>" if prescription.doctor else ""}
                </div>
                
                <div class="prescription-info">
                    <p><strong>Patient:</strong> {prescription.patient.name if prescription.patient else 'N/A'}</p>
                    <p><strong>Status:</strong> {prescription.state.title() if prescription.state else 'N/A'}</p>
                    {f"<p><strong>Notes:</strong> {prescription.info}</p>" if prescription.info else ""}
                </div>
                
                <h2>Prescribed Medicines</h2>
            """
            
            if prescription.prescription_line:
                for line in prescription.prescription_line:
                    medicine_name = line.name.name if line.name else 'Unknown Medicine'
                    composition = f"<br><small>Composition: {line.name.composition}</small>" if line.name and line.name.composition else ""
                    
                    html_content += f"""
                    <div class="medicine-item">
                        <div class="medicine-name">{medicine_name}{composition}</div>
                        <div class="dosage">
                            <strong>Quantity:</strong> {line.qty or 'N/A'}
                            {f" {line.dose_unit.name}" if line.dose_unit else ""}
                        </div>
                        {f'<div class="dosage"><strong>Dose:</strong> {line.dose} {line.dose_unit.name if line.dose_unit else ""}</div>' if line.dose else ''}
                        {f'<div class="dosage"><strong>Frequency:</strong> {line.frequency} per {line.frequency_unit}</div>' if line.frequency else ''}
                        {f'<div class="dosage"><strong>Duration:</strong> {line.duration} {line.duration_period}</div>' if line.duration else ''}
                        {f'<div class="instructions"><strong>Instructions:</strong> {line.info}</div>' if line.info else ''}
                        {f'<div class="instructions"><strong>Indication:</strong> {line.indication.name}</div>' if line.indication else ''}
                    </div>
                    """
            else:
                html_content += "<p>No medicines prescribed.</p>"
            
            html_content += """
                </body>
            </html>
            """
            
            filename = f"prescription_{prescription.name.replace('/', '_')}.html"
            return request.make_response(
                html_content,
                headers=[
                    ('Content-Type', 'text/html'),
                    ('Content-Disposition', f'attachment; filename="{filename}"')
                ]
            )
            
        except Exception as e:
            _logger.error(f"Error generating HTML prescription report: {e}")
            return request.redirect('/patient/portal/prescriptions?error=report_generation_failed')

    @http.route(['/patient/portal/evaluations'], type='http', auth="user", website=True)
    def evaluations(self, **kwargs):
        """Patient evaluations page"""
        patient = self._get_patient_from_user()
        if not patient:
            return request.redirect('/my')
            
        values = self._prepare_portal_values(patient)
        values['page_name'] = 'evaluations'
        
        # Get medical evaluations
        evaluations = request.env['oeh.medical.evaluation'].sudo().search([
            ('patient', '=', patient.id)
        ], order='evaluation_start_date desc', limit=50)
        
        values.update({
            'page_title': 'Medical Evaluations',
            'evaluations': evaluations,
        })
        
        return request.render("intarvas_patient_portal.patient_evaluations", values)

    @http.route(['/patient/portal/billing'], type='http', auth="user", website=True)
    def billing(self, **kwargs):
        """Patient billing page"""
        patient = self._get_patient_from_user()
        if not patient:
            return request.redirect('/my')
            
        values = self._prepare_portal_values(patient)
        values['page_name'] = 'billing'
        
        # Get outstanding bills (invoices)
        try:
            outstanding_bills = request.env['account.move'].sudo().search([
                ('partner_id', '=', patient.partner_id.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial'])
            ], order='invoice_date desc')
            
            # Create demo invoice if none exist (for testing)
            if not outstanding_bills:
                demo_invoice = request.env['account.move'].sudo().create({
                    'move_type': 'out_invoice',
                    'partner_id': patient.partner_id.id,
                    'currency_id': request.env.company.currency_id.id,
                    'invoice_date': fields.Date.today(),
                    'invoice_line_ids': [(0, 0, {
                        'name': 'Medical Consultation',
                        'quantity': 1,
                        'price_unit': 150.00,
                    })],
                })
                demo_invoice.action_post()
                outstanding_bills = demo_invoice
            
            payment_history = request.env['account.payment'].sudo().search([
                ('partner_id', '=', patient.partner_id.id),
                ('state', '=', 'posted')
            ], order='date desc', limit=20)
            
            
        except Exception as e:
            _logger.error(f"Error in billing: {e}")
            outstanding_bills = []
            payment_history = []
        
        values.update({
            'page_title': 'Billing & Insurance',
            'outstanding_bills': outstanding_bills,
            'payment_history': payment_history,
        })
        
        return request.render("intarvas_patient_portal.patient_billing", values)

    @http.route(['/patient/portal/invoice/<int:invoice_id>/pay'], type='http', auth="user", website=True, methods=['GET'])
    def invoice_payment(self, invoice_id, **kwargs):
        """Display invoice detail page with payment modal (standard Odoo behavior)"""
        patient = self._get_patient_from_user()
        if not patient:
            return request.redirect('/my')
        
        try:
            # Verify the invoice belongs to this patient
            invoice = request.env['account.move'].sudo().search([
                ('id', '=', invoice_id),
                ('partner_id', '=', patient.partner_id.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted')
            ], limit=1)
            
            if not invoice:
                return request.redirect('/patient/portal/billing?error=invoice_not_found')
            
            # Get invoice portal URL using access token
            access_token = invoice._portal_ensure_token()
            
            # Get compatible payment providers using Odoo's native method
            payment_providers = request.env['payment.provider'].sudo()._get_compatible_providers(
                invoice.company_id.id,
                patient.partner_id.id,
                invoice.amount_residual,
                currency_id=invoice.currency_id.id,
                force_tokenization=False,
                is_validation=False,
            )
            
            # Get payment methods for the compatible providers
            payment_methods = request.env['payment.method'].sudo().search([
                ('provider_ids', 'in', payment_providers.ids)
            ])
            
            # Get existing payment tokens for the patient (saved payment methods)
            payment_tokens = request.env['payment.token'].sudo().search([
                ('partner_id', '=', patient.partner_id.id),
                ('provider_id', 'in', payment_providers.ids)
            ])
            
            # Set up payment context like standard Odoo payment portal
            payment_context = {
                'reference_prefix': invoice.name,
                'amount': invoice.amount_residual,
                'currency': invoice.currency_id,
                'partner_id': patient.partner_id.id,
                'providers_sudo': payment_providers,
                'payment_methods_sudo': payment_methods,
                'tokens_sudo': payment_tokens,
                'transaction_route': f'/invoice/transaction/{invoice.id}',
                'landing_route': f'{invoice.access_url}?access_token={access_token}',
                'access_token': access_token,
                'show_tokenize_input_mapping': {},
            }
            
            values = self._prepare_portal_values(patient)
            values.update({
                'page_title': f'Invoice #{invoice.name}',
                'invoice': invoice,
                'partner': patient.partner_id,
                'report_type': 'html',
                'download_url': f'/my/invoices/{invoice.id}?access_token={access_token}&report_type=pdf&download=true',
                'bootstrap_formatting': True,
                **payment_context,  # Add payment context variables to template context
            })
            
            return request.render("intarvas_patient_portal.patient_invoice_payment", values)
            
        except Exception as e:
            _logger.error(f"Error accessing invoice {invoice_id}: {e}")
            return request.redirect('/patient/portal/billing?error=invoice_access_failed')

    @http.route(['/patient/portal/payment/pay'], type='http', auth='user', methods=['GET'], website=True)
    def patient_payment_pay(self, **kwargs):
        """Handle payment pay requests from patient portal"""
        try:
            # Get parameters
            reference = kwargs.get('reference')
            amount = kwargs.get('amount')
            currency_id = kwargs.get('currency_id')
            partner_id = kwargs.get('partner_id')
            
            if not all([reference, amount, currency_id, partner_id]):
                return request.redirect('/patient/portal/billing?error=missing_parameters')
            
            # Extract invoice ID from reference
            invoice_id = None
            if reference.startswith('INV-'):
                try:
                    invoice_id = int(reference.split('-')[1])
                except (IndexError, ValueError):
                    pass
            
            if invoice_id:
                return request.redirect(f'/patient/portal/invoice/{invoice_id}/payment')
            else:
                return request.redirect('/patient/portal/billing?error=invalid_reference')
                
        except Exception as e:
            _logger.error(f"Error in patient payment pay: {e}")
            return request.redirect('/patient/portal/billing?error=payment_failed')

    @http.route(['/patient/portal/payment/transaction'], type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def patient_payment_transaction(self, **kwargs):
        """Override payment transaction creation for patient portal"""
        try:
            patient = self._get_patient_from_user()
            if not patient:
                return {'error': 'Patient not found'}

            # This route is specifically for patient portal payments
            reference_prefix = kwargs.get('reference_prefix', '')
            if not reference_prefix.startswith('INV-'):
                return {'error': 'Invalid reference prefix for patient portal payment'}

            # Extract invoice ID from reference
            invoice_id_str = reference_prefix.replace('INV-', '').replace('-', '')
            try:
                invoice_id = int(invoice_id_str)
            except:
                return {'error': 'Invalid invoice ID'}

            # Verify invoice belongs to patient
            invoice = request.env['account.move'].sudo().search([
                ('id', '=', invoice_id),
                ('partner_id', '=', patient.partner_id.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial'])
            ], limit=1)

            if not invoice:
                return {'error': 'Invoice not found'}

            # Check if transaction already exists, if so use it
            existing_transaction = request.env['payment.transaction'].sudo().search([
                ('reference', '=', f"INV-{invoice.name}"),
                ('partner_id', '=', patient.partner_id.id),
                ('state', 'in', ['draft', 'pending']),
            ], limit=1)
            
            if existing_transaction:
                transaction = existing_transaction
                # Update provider if changed
                transaction.sudo().write({
                    'provider_id': int(kwargs.get('provider_id')),
                    'payment_method_id': kwargs.get('payment_method_id') and int(kwargs.get('payment_method_id')),
                })
            else:
                # Create new transaction with unique reference
                unique_ref = f"INV-{invoice.name}-{request.env['payment.transaction']._get_next_reference()}"
                transaction_values = {
                    'provider_id': int(kwargs.get('provider_id')),
                    'payment_method_id': kwargs.get('payment_method_id') and int(kwargs.get('payment_method_id')),
                    'reference': unique_ref,
                    'amount': invoice.amount_residual,
                    'currency_id': invoice.currency_id.id,
                    'partner_id': patient.partner_id.id,
                    'invoice_ids': [(6, 0, [invoice.id])],
                    'operation': 'online_direct',
                }

                transaction = request.env['payment.transaction'].sudo().create(transaction_values)
            
            # Get processing values and return them
            processing_values = transaction._get_processing_values()
            
            # Return success response in the format expected by payment form
            result = {
                'transaction_id': transaction.id,
                'provider_id': transaction.provider_id.id,
                'reference': transaction.reference,
                'state': transaction.state,
                'landing_route': kwargs.get('landing_route', '/patient/portal/billing'),
            }
            
            # Add processing values if they exist
            if processing_values:
                result.update(processing_values)
                
            # Ensure we have the redirect form HTML if needed
            if 'redirect_form_html' not in result and transaction.provider_id.redirect_form_view_id:
                result['redirect_form_html'] = f'''
                    <form method="post" action="/payment/return">
                        <input type="hidden" name="reference" value="{transaction.reference}"/>
                        <input type="hidden" name="csrf_token" value="{request.csrf_token()}"/>
                        <input type="hidden" name="landing_route" value="/patient/portal/billing"/>
                        <script>document.forms[0].submit();</script>
                    </form>
                '''
            
            return result

        except Exception as e:
            _logger.error(f"Error in patient payment transaction: {e}")
            return {'error': str(e)}

    @http.route(['/payment/return'], type='http', auth='user', methods=['GET', 'POST'], csrf=False)
    def patient_payment_return(self, **kwargs):
        """Handle payment return for patient portal payments"""
        try:
            _logger.info(f"Payment return received with data: {kwargs}")
            
            # Get the transaction reference from the return data
            reference = kwargs.get('reference') or kwargs.get('tx_reference') or kwargs.get('merchantReference')
            
            if not reference:
                _logger.error("No reference found in payment return data")
                return request.redirect('/patient/portal/billing?error=no_reference')
            
            # Find the transaction
            transaction = request.env['payment.transaction'].sudo().search([
                ('reference', '=', reference)
            ], limit=1)
            
            if not transaction:
                _logger.error(f"Transaction not found for reference: {reference}")
                return request.redirect('/patient/portal/billing?error=transaction_not_found')
            
            # Verify this is a patient portal transaction (has linked invoice)
            if not transaction.invoice_ids:
                _logger.error(f"Transaction {reference} has no linked invoices")
                return request.redirect('/patient/portal/billing?error=no_invoice')
            
            # Let the payment provider handle the return data
            try:
                # This will update the transaction state based on provider response
                transaction._handle_notification_data('return', kwargs)
            except Exception as e:
                _logger.error(f"Error handling payment notification: {e}")
            
            # Check transaction state and redirect accordingly
            if transaction.state == 'done':
                _logger.info(f"Payment successful for transaction {reference}")
                return request.redirect('/patient/portal/billing?payment=success')
            elif transaction.state in ['pending', 'authorized']:
                _logger.info(f"Payment pending for transaction {reference}")
                return request.redirect('/patient/portal/billing?payment=pending')
            else:
                _logger.warning(f"Payment failed or cancelled for transaction {reference}, state: {transaction.state}")
                return request.redirect('/patient/portal/billing?payment=failed')
                
        except Exception as e:
            _logger.error(f"Error in payment return handler: {e}")
            return request.redirect('/patient/portal/billing?error=return_error')

    @http.route(['/payment/cancel'], type='http', auth='user', methods=['GET', 'POST'], csrf=False)
    def patient_payment_cancel(self, **kwargs):
        """Handle payment cancellation for patient portal payments"""
        try:
            _logger.info(f"Payment cancelled with data: {kwargs}")
            
            reference = kwargs.get('reference') or kwargs.get('tx_reference')
            if reference:
                transaction = request.env['payment.transaction'].sudo().search([
                    ('reference', '=', reference)
                ], limit=1)
                if transaction:
                    transaction.sudo().write({'state': 'cancel'})
                    
            return request.redirect('/patient/portal/billing?payment=cancelled')
            
        except Exception as e:
            _logger.error(f"Error in payment cancel handler: {e}")
            return request.redirect('/patient/portal/billing?error=cancel_error')


    @http.route(['/patient/portal/invoice/<int:invoice_id>/view'], type='http', auth="user", website=False, csrf=False)
    def invoice_view_minimal(self, invoice_id, access_token=None, **kwargs):
        """Minimal invoice view for iframe embedding (no headers, footers, navigation)"""
        patient = self._get_patient_from_user()
        if not patient:
            return request.make_response('<html><body><h1>Patient not found</h1></body></html>')
        
        try:
            # First, try to find any invoice for this patient with this ID (for testing)
            invoice = request.env['account.move'].sudo().search([
                ('id', '=', invoice_id),
                ('partner_id', '=', patient.partner_id.id),
                ('move_type', '=', 'out_invoice')
            ], limit=1)
            
            if not invoice:
                # Let's create a demo invoice for testing
                invoice = request.env['account.move'].sudo().create({
                    'move_type': 'out_invoice',
                    'partner_id': patient.partner_id.id,
                    'currency_id': request.env.company.currency_id.id,
                    'invoice_line_ids': [(0, 0, {
                        'name': 'Medical Consultation',
                        'quantity': 1,
                        'price_unit': 150.00,
                    })],
                })
                invoice.action_post()
                
            # Generate access token if not provided
            if not access_token:
                access_token = invoice._portal_ensure_token()
            
            # Get payment acquirers for this invoice
            try:
                acquirers = request.env['payment.provider'].sudo().search([
                    ('state', '=', 'enabled'),
                    ('company_id', '=', invoice.company_id.id)
                ])
            except:
                # Fallback for older versions
                acquirers = request.env['payment.acquirer'].sudo().search([
                    ('state', '=', 'enabled'),
                    ('company_id', '=', invoice.company_id.id)
                ])
            
            values = {
                'invoice': invoice,
                'access_token': access_token,
                'acquirers': acquirers,
                'partner': patient.partner_id,
                'bootstrap_formatting': True,
                'report_type': 'html',
            }
            
            return request.render("intarvas_patient_portal.invoice_minimal_view", values, headers={'X-Frame-Options': 'SAMEORIGIN'})
            
        except Exception as e:
            _logger.error(f"Error in minimal invoice view {invoice_id}: {e}")
            import traceback
            _logger.error(f"Full traceback: {traceback.format_exc()}")
            return request.make_response(f'<html><body><h1>Error loading invoice</h1><p>{str(e)}</p></body></html>')

    @http.route(['/patient/portal/help'], type='http', auth="user", website=True)
    def help_support(self, **kwargs):
        """Patient help and support page"""
        patient = self._get_patient_from_user()
        if not patient:
            return request.redirect('/my')
            
        values = self._prepare_portal_values(patient)
        values['page_name'] = 'help'
        
        values.update({
            'page_title': 'Help & Support',
        })
        
        return request.render("intarvas_patient_portal.patient_help", values)

    # GDPR Compliance Routes
    @http.route(['/patient/portal/privacy'], type='http', auth="user", website=True)
    def privacy_settings(self, **kwargs):
        """GDPR Privacy Settings"""
        patient = self._get_patient_from_user()
        if not patient:
            return request.redirect('/my')
            
        values = self._prepare_portal_values(patient)
        values.update({
            'page_title': 'Privacy & GDPR Settings',
        })
        
        return request.render("intarvas_patient_portal.privacy_settings", values)

    @http.route(['/patient/portal/privacy-policy'], type='http', auth="public", website=True)
    def privacy_policy(self, **kwargs):
        """Privacy Policy Page"""
        return request.render("intarvas_patient_portal.privacy_policy", {
            'page_title': 'Privacy Policy',
        })

    @http.route(['/patient/portal/export-data'], type='http', auth="user", methods=['POST'])
    def export_patient_data(self, **kwargs):
        """Export patient data for GDPR compliance"""
        patient = self._get_patient_from_user()
        if not patient:
            return request.not_found()
            
        try:
            data_type = request.get_json_data().get('data_type', 'all')
            export_data = self._prepare_export_data(patient, data_type)
            
            json_data = json.dumps(export_data, indent=2, default=str)
            
            return request.make_response(
                json_data,
                headers=[
                    ('Content-Type', 'application/json'),
                    ('Content-Disposition', content_disposition(f'patient_data_{data_type}.json')),
                ]
            )
        except Exception as e:
            return request.make_response(
                json.dumps({'error': str(e)}),
                status=500,
                headers=[('Content-Type', 'application/json')]
            )

    def _prepare_export_data(self, patient, data_type='all'):
        """Prepare patient data for export"""
        export_data = {
            'export_date': datetime.now().isoformat(),
            'patient_id': patient.identification_code,
            'data_type': data_type,
        }
        
        if data_type == 'all' or data_type == 'personal':
            export_data['personal_information'] = {
                'name': patient.name,
                'email': patient.email,
                'phone': patient.phone,
                'dob': patient.dob.isoformat() if patient.dob else None,
                'gender': patient.gender,
                'address': {
                    'street': patient.street,
                    'city': patient.city,
                    'zip': patient.zip,
                    'country': patient.country_id.name if patient.country_id else None,
                }
            }
        
        if data_type == 'all' or data_type == 'appointments':
            appointments = request.env['oeh.medical.appointment'].sudo().search([
                ('patient', '=', patient.id)
            ])
            export_data['appointments'] = [{
                'date': apt.appointment_date.isoformat() if apt.appointment_date else None,
                'doctor': self._format_doctor_name(apt.doctor.name) if apt.doctor else None,
                'institution': apt.institution.name if apt.institution else None,
                'reason': apt.reason,
                'state': apt.state,
            } for apt in appointments]
        
        if data_type == 'all' or data_type == 'medical':
            evaluations = request.env['oeh.medical.evaluation'].sudo().search([
                ('patient', '=', patient.id)
            ])
            export_data['medical_evaluations'] = [{
                'date': eval.evaluation_date.isoformat() if eval.evaluation_date else None,
                'diagnosis': eval.diagnosis,
                'symptoms': eval.chief_complaint,
            } for eval in evaluations]
        
        return export_data

    @http.route(['/patient/portal/privacy-settings'], type='jsonrpc', auth="user")
    def update_privacy_settings(self, **kwargs):
        """Update privacy settings via AJAX"""
        patient = self._get_patient_from_user()
        if not patient:
            return {'success': False, 'error': 'Patient not found'}
            
        try:
            setting = kwargs.get('setting')
            value = kwargs.get('value')
            
            # Store privacy settings (you might want to create a dedicated model for this)
            # For now, we'll use partner fields or create custom fields as needed
            
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route(['/patient/portal/delete-account'], type='http', auth="user", website=True, methods=['POST'])
    def delete_account_request(self, **kwargs):
        """GDPR Right to be Forgotten - Account Deletion Request"""
        patient = self._get_patient_from_user()
        if not patient:
            return request.redirect('/my')
            
        # Create a deletion request record (you might want to create a specific model for this)
        # This should trigger a workflow for manual review before actual deletion
        
        try:
            # Log the deletion request
            patient.message_post(
                body="Patient requested account deletion (GDPR Right to be Forgotten)",
                message_type='notification'
            )
            
            # You might want to deactivate the account immediately and schedule deletion
            # patient.oeh_patient_user_id.sudo().write({'active': False})
            
            return request.redirect('/patient/portal/privacy?deletion_requested=1')
        except Exception as e:
            return request.redirect('/patient/portal/privacy?error=deletion_failed')


class CustomerPortalPatientExtension(CustomerPortal):
    """Extend the standard customer portal"""
    
    @http.route(['/my', '/my/home'], type='http', auth="user", website=True)
    def home(self, redirect=None, **post):
        """Override portal home to add patient portal count"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        
        # Check if user is a patient
        patient = request.env['oeh.medical.patient'].sudo().search([
            ('oeh_patient_user_id', '=', request.env.user.id)
        ], limit=1)
        
        if patient:
            values['patient_portal_count'] = 1
            values['patient'] = patient
        else:
            values['patient_portal_count'] = 0
            
        return request.render("portal.portal_my_home", values)


# Action Button Controllers for Patient Portal
class PatientPortalActions(http.Controller):
    
    def _get_patient_from_user(self):
        """Get patient record for current user"""
        if not request.env.user or request.env.user._is_public():
            return None
        
        patient = request.env['oeh.medical.patient'].sudo().search([
            ('oeh_patient_user_id', '=', request.env.user.id)
        ], limit=1)
        
        return patient if patient else None

    @http.route(['/patient/portal/evaluation/<int:evaluation_id>'], type='http', auth="user", website=True)
    def view_evaluation_details(self, evaluation_id, **kwargs):
        """View detailed evaluation information"""
        patient = self._get_patient_from_user()
        if not patient:
            return request.redirect('/my')
        
        # Get the evaluation and verify it belongs to this patient
        evaluation = request.env['oeh.medical.evaluation'].sudo().search([
            ('id', '=', evaluation_id),
            ('patient', '=', patient.id)
        ], limit=1)
        
        if not evaluation:
            return request.not_found()
        
        values = {
            'patient': patient,
            'page_title': 'Evaluation Details',
            'evaluation': evaluation,
        }
        
        return request.render("intarvas_patient_portal.evaluation_details", values)

    @http.route(['/patient/portal/certificate/<int:certificate_id>/download'], type='http', auth="user")
    def download_certificate(self, certificate_id, **kwargs):
        """Download medical certificate"""
        patient = self._get_patient_from_user()
        if not patient:
            return request.redirect('/my')
        
        certificate = request.env['oeh.medical.patient.medical.cert'].sudo().search([
            ('id', '=', certificate_id),
            ('patient', '=', patient.id)
        ], limit=1)
        
        if not certificate:
            return request.not_found()
        
        # Generate PDF for the certificate
        try:
            pdf_content = self._generate_certificate_pdf(certificate)
            filename = f"medical_certificate_{certificate.name}.pdf"
            
            return request.make_response(
                pdf_content,
                headers=[
                    ('Content-Type', 'application/pdf'),
                    ('Content-Disposition', content_disposition(filename))
                ]
            )
        except Exception as e:
            # Logging imported at top of file
            _logger.error(f"Error generating certificate PDF: {e}")
            return request.redirect('/patient/portal/medical-records?error=download_failed')

    def _generate_certificate_pdf(self, certificate):
        """Generate PDF for medical certificate"""
        # This is a simplified version using basic text
        if not REPORTLAB_AVAILABLE:
            raise UserError("ReportLab is required for PDF generation")
        
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Add content to PDF
        p.drawString(100, 750, f"MEDICAL CERTIFICATE")
        p.drawString(100, 700, f"Certificate #: {certificate.name}")
        p.drawString(100, 670, f"Patient: {certificate.patient.name}")
        p.drawString(100, 640, f"Doctor: {self._format_doctor_name(certificate.doctor.name) if certificate.doctor else 'N/A'}")
        p.drawString(100, 610, f"Issue Date: {certificate.issue_date.strftime('%B %d, %Y') if certificate.issue_date else 'N/A'}")
        p.drawString(100, 580, f"From: {certificate.start_date.strftime('%B %d, %Y') if certificate.start_date else 'N/A'}")
        p.drawString(100, 550, f"To: {certificate.end_date.strftime('%B %d, %Y') if certificate.end_date else 'N/A'}")
        p.drawString(100, 520, f"Reason: {certificate.reason or 'N/A'}")
        
        p.showPage()
        p.save()
        
        buffer.seek(0)
        return buffer.read()

    @http.route(['/patient/portal/download-all-records'], type='http', auth="user")
    def download_all_records(self, **kwargs):
        """Download all medical records as ZIP file"""
        patient = self._get_patient_from_user()
        if not patient:
            return request.redirect('/my')
        
        try:
            zip_content = self._generate_all_records_zip(patient)
            filename = f"medical_records_{patient.name.replace(' ', '_')}.zip"
            
            return request.make_response(
                zip_content,
                headers=[
                    ('Content-Type', 'application/zip'),
                    ('Content-Disposition', content_disposition(filename))
                ]
            )
        except Exception as e:
            # Logging imported at top of file
            _logger.error(f"Error generating records ZIP: {e}")
            return request.redirect('/patient/portal/medical-records?error=download_failed')

    def _generate_all_records_zip(self, patient):
        """Generate ZIP file with all patient records"""
        
        buffer = BytesIO()
        
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add patient summary
            patient_info = f"""PATIENT SUMMARY
            
Name: {patient.name}
Patient ID: {patient.identification_code or 'N/A'}
Date of Birth: {patient.dob.strftime('%B %d, %Y') if patient.dob else 'N/A'}
Gender: {patient.sex or 'N/A'}
Blood Type: {patient.blood_type or 'N/A'}
Emergency Contact: {patient.emergency_name or 'N/A'} - {patient.emergency_phone or 'N/A'}

Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
"""
            zip_file.writestr('patient_summary.txt', patient_info)
            
            # Add evaluations
            evaluations = request.env['oeh.medical.evaluation'].sudo().search([
                ('patient', '=', patient.id)
            ])
            for i, evaluation in enumerate(evaluations, 1):
                eval_content = f"""MEDICAL EVALUATION #{i}
                
Date: {evaluation.evaluation_start_date.strftime('%B %d, %Y') if evaluation.evaluation_start_date else 'N/A'}
Type: {evaluation.evaluation_type or 'N/A'}
Doctor: {self._format_doctor_name(evaluation.doctor.name) if evaluation.doctor else 'N/A'}
Chief Complaint: {evaluation.chief_complaint or 'N/A'}
Diagnosis: {evaluation.info_diagnosis or 'N/A'}
Notes: {evaluation.notes or 'N/A'}
"""
                zip_file.writestr(f'evaluations/evaluation_{i}.txt', eval_content)
            
            # Add prescriptions
            prescriptions = request.env['oeh.medical.prescription'].sudo().search([
                ('patient', '=', patient.id)
            ])
            for i, prescription in enumerate(prescriptions, 1):
                presc_content = f"""PRESCRIPTION #{i}
                
Date: {prescription.date.strftime('%B %d, %Y') if prescription.date else 'N/A'}
Doctor: {self._format_doctor_name(prescription.doctor.name) if prescription.doctor else 'N/A'}
Status: {prescription.state or 'N/A'}
Notes: {prescription.info or 'N/A'}

MEDICATIONS:
"""
                for line in prescription.prescription_line:
                    presc_content += f"- {line.name.name if line.name else 'N/A'}: {line.dose or 'N/A'} {line.dose_unit or ''}, {line.common_dosage or 'N/A'}\n"
                
                zip_file.writestr(f'prescriptions/prescription_{i}.txt', presc_content)
        
        buffer.seek(0)
        return buffer.read()

    @http.route(['/patient/portal/appointment/<int:appointment_id>/cancel'], type='http', auth="user", methods=['POST'])
    def cancel_appointment(self, appointment_id, **kwargs):
        """Cancel an appointment"""
        patient = self._get_patient_from_user()
        if not patient:
            return request.redirect('/my')
        
        appointment = request.env['oeh.medical.appointment'].sudo().search([
            ('id', '=', appointment_id),
            ('patient', '=', patient.id),
            ('state', 'in', ['Scheduled', 'Accepted'])  # Only allow canceling scheduled/accepted appointments
        ], limit=1)
        
        if not appointment:
            return request.redirect('/patient/portal/appointments?error=appointment_not_found')
        
        try:
            # Update appointment state
            appointment.sudo().write({'state': 'Cancelled'})
            
            # Log the cancellation
            appointment.message_post(
                body=f"Appointment cancelled by patient {patient.name}",
                message_type='notification'
            )
            
            return request.redirect('/patient/portal/appointments?success=appointment_cancelled')
        except Exception as e:
            # Logging imported at top of file
            _logger.error(f"Error cancelling appointment: {e}")
            return request.redirect('/patient/portal/appointments?error=cancellation_failed')

    @http.route(['/patient/portal/evaluation/<int:evaluation_id>/print'], type='http', auth="user", website=True)
    def print_evaluation(self, evaluation_id, **kwargs):
        """Print-only view for evaluation details"""
        patient = self._get_patient_from_user()
        if not patient:
            return request.redirect('/my')
        
        # Get the evaluation and verify it belongs to this patient
        evaluation = request.env['oeh.medical.evaluation'].sudo().search([
            ('id', '=', evaluation_id),
            ('patient', '=', patient.id)
        ], limit=1)
        
        if not evaluation:
            return request.not_found()
        
        values = {
            'patient': patient,
            'evaluation': evaluation,
            'datetime': datetime,
        }
        
        return request.render("intarvas_patient_portal.evaluation_print", values)

    @http.route(['/patient/portal/labtest-report/<int:test_id>'], type='http', auth="user")
    def download_labtest_report(self, test_id, **kwargs):
        """Download lab test report PDF using existing Odoo report"""
        patient = self._get_patient_from_user()
        if not patient:
            return request.redirect('/my')
        
        # Get the lab test and verify it belongs to this patient
        try:
            lab_test = request.env['oeh.medical.lab.test'].sudo().search([
                ('id', '=', test_id),
                ('patient', '=', patient.id)
            ], limit=1)
            
            if not lab_test:
                return request.not_found()
        except Exception as e:
            # Logging imported at top of file
            _logger.error(f"Error accessing lab test {test_id}: {e}")
            return request.redirect('/patient/portal/lab-results?error=access_denied')
        
        try:
            # Use the existing Odoo report system to get the same report as backend
            report = request.env.ref('intarvas_lab.action_report_patient_labtest').sudo()
            pdf_content, _ = report._render_qweb_pdf([lab_test.id])
            
            filename = f"lab_test_report_{lab_test.name or test_id}.pdf"
            
            return request.make_response(
                pdf_content,
                headers=[
                    ('Content-Type', 'application/pdf'),
                    ('Content-Disposition', content_disposition(filename))
                ]
            )
        except Exception as e:
            # Logging imported at top of file
            _logger.error(f"Error generating lab test report: {e}")
            return request.redirect('/patient/portal/lab-results?error=download_failed')

    @http.route(['/patient/portal/appointment/<int:appointment_id>'], type='http', auth="user", website=True)
    def appointment_detail(self, appointment_id, **kwargs):
        """Appointment Detail Page"""
        patient = self._get_patient_from_user()
        if not patient:
            return request.redirect('/my')
        
        # Get appointment and verify it belongs to current patient
        appointment = request.env['oeh.medical.appointment'].sudo().search([
            ('id', '=', appointment_id),
            ('patient', '=', patient.id)
        ], limit=1)
        
        if not appointment:
            return request.redirect('/patient/portal/appointments?error=appointment_not_found')
        
        values = {
            'patient': patient,
            'user': request.env.user,
            'page_name': 'appointments',
            'page_title': f'Appointment Details - {appointment.name}',
            'appointment': appointment,
        }
        
        return request.render("intarvas_patient_portal.appointment_detail", values)