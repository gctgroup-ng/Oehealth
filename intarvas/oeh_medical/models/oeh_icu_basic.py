##############################################################################
#    Copyright (C) 2015 - Present, intarvas (<https://www.intarvas.in>). All Rights Reserved
#    intarvas ICU Management Module - Simplified Version

##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

class intarvasICUAdmission(models.Model):
    _name = 'oeh.medical.icu.admission'
    _description = 'ICU Patient Admission'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'admission_date desc'
    _rec_name = 'display_name'

    ADMISSION_TYPES = [
        ('emergency', 'Emergency Admission'),
        ('elective', 'Elective Admission'),
        ('transfer', 'Transfer'),
        ('post_operative', 'Post-Operative'),
    ]

    ADMISSION_STATUS = [
        ('admitted', 'Admitted'),
        ('discharged', 'Discharged'),
        ('transferred', 'Transferred'),
    ]

    ACUITY_LEVELS = [
        ('level_1', 'Level 1 - Low'),
        ('level_2', 'Level 2 - Medium'),
        ('level_3', 'Level 3 - High'),
        ('level_4', 'Level 4 - Critical'),
    ]

    # Basic Information
    name = fields.Char(string='Admission Number', required=True, copy=False, readonly=True,
                      default=lambda self: _('New'))
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    patient_id = fields.Many2one('oeh.medical.patient', string='Patient', required=True, tracking=True)
    icu_unit_id = fields.Many2one('oeh.medical.health.center.ward', string='ICU Unit',
                                 domain=[('is_icu', '=', True)], required=True, tracking=True)
    bed_id = fields.Many2one('oeh.medical.health.center.beds', string='ICU Bed',
                            domain="[('ward', '=', icu_unit_id), ('is_icu_bed', '=', True)]",
                            required=True, tracking=True)

    # Admission Details
    admission_date = fields.Datetime(string='Admission Date', required=True,
                                   default=fields.Datetime.now, tracking=True)
    admission_type = fields.Selection(ADMISSION_TYPES, string='Admission Type', required=True, tracking=True)

    # Clinical Assessment
    acuity_level = fields.Selection(ACUITY_LEVELS, string='Acuity Level', required=True, tracking=True)
    chief_complaint = fields.Text(string='Chief Complaint', tracking=True)
    admission_diagnosis = fields.Text(string='Admission Diagnosis', tracking=True)

    # Scoring Systems
    glasgow_coma_scale = fields.Integer(string='Glasgow Coma Scale', default=15)
    apache_ii_score = fields.Integer(string='APACHE II Score', compute='_compute_apache_ii_score', store=True)
    sofa_score = fields.Integer(string='SOFA Score', compute='_compute_sofa_score', store=True)

    # APACHE II Components
    age = fields.Char(string='Age', related='patient_id.age', readonly=True)
    age_numeric = fields.Integer(string='Age (Numeric)', compute='_compute_age_numeric', store=True)
    chronic_health_points = fields.Integer(string='Chronic Health Points', default=0,
                                         help='0=No chronic health problems, 2=Elective surgery, 5=Emergency surgery or immunocompromised')
    worst_temperature = fields.Float(string='Worst Temperature (°C)', default=37.0)
    worst_heart_rate = fields.Integer(string='Worst Heart Rate', default=70)
    worst_respiratory_rate = fields.Integer(string='Worst Respiratory Rate', default=12)
    worst_sodium = fields.Float(string='Worst Sodium (mEq/L)', default=140.0)
    worst_potassium = fields.Float(string='Worst Potassium (mEq/L)', default=4.0)
    worst_creatinine = fields.Float(string='Worst Creatinine (mg/dL)', default=1.0)
    worst_hematocrit = fields.Float(string='Worst Hematocrit (%)', default=40.0)
    worst_wbc = fields.Float(string='Worst WBC Count (×10³/μL)', default=7.0)
    worst_arterial_ph = fields.Float(string='Worst Arterial pH', default=7.4)

    # SOFA Components
    pao2_fio2_ratio = fields.Float(string='PaO2/FiO2 Ratio', default=400.0)
    platelets = fields.Float(string='Platelets (×10³/μL)', default=300.0)
    bilirubin = fields.Float(string='Bilirubin (mg/dL)', default=1.0)
    cardiovascular_support = fields.Selection([
        ('none', 'No Support'),
        ('dopamine_5', 'Dopamine ≤5 or Dobutamine'),
        ('dopamine_15', 'Dopamine >5-15 or Epinephrine ≤0.1 or Norepinephrine ≤0.1'),
        ('dopamine_15_plus', 'Dopamine >15 or Epinephrine >0.1 or Norepinephrine >0.1'),
    ], string='Cardiovascular Support', default='none')

    # Alert System
    vital_signs_status = fields.Selection([
        ('normal', 'Normal'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ], string='Vital Signs Status', compute='_compute_vital_signs_status', store=True)
    alert_messages = fields.Text(string='Active Alerts', compute='_compute_alerts')

    # Status and Discharge
    status = fields.Selection(ADMISSION_STATUS, string='Status', default='admitted', tracking=True)
    discharge_date = fields.Datetime(string='Discharge Date', tracking=True)
    discharge_summary = fields.Text(string='Discharge Summary')

    # Current Vital Signs (Latest Monitoring)
    current_temperature = fields.Float(string='Current Temperature (°C)')
    current_heart_rate = fields.Integer(string='Current Heart Rate (bpm)')
    current_bp_systolic = fields.Integer(string='Current BP Systolic (mmHg)')
    current_bp_diastolic = fields.Integer(string='Current BP Diastolic (mmHg)')
    current_respiratory_rate = fields.Integer(string='Current Respiratory Rate (/min)')
    current_oxygen_saturation = fields.Integer(string='Current Oxygen Saturation (%)')
    current_monitoring_notes = fields.Text(string='Current Monitoring Notes')
    last_monitoring_datetime = fields.Datetime(string='Last Monitoring Date/Time')
    responsible_nurse_id = fields.Many2one('res.users', string='Responsible Nurse')

    # Monitoring History
    monitoring_ids = fields.One2many('oeh.medical.icu.monitoring', 'admission_id', string='Monitoring History')

    # Computed Fields
    length_of_stay = fields.Float(string='Length of Stay (Days)', compute='_compute_length_of_stay', store=True)
    is_active = fields.Boolean(string='Is Active', compute='_compute_is_active', store=True)

    @api.depends('name', 'patient_id')
    def _compute_display_name(self):
        for record in self:
            if record.patient_id:
                record.display_name = f"{record.name} - {record.patient_id.name}"
            else:
                record.display_name = record.name or 'New ICU Admission'

    @api.depends('admission_date', 'discharge_date')
    def _compute_length_of_stay(self):
        for record in self:
            if record.admission_date:
                end_date = record.discharge_date or fields.Datetime.now()
                delta = end_date - record.admission_date
                record.length_of_stay = delta.total_seconds() / (24 * 3600)  # Convert to days
            else:
                record.length_of_stay = 0.0

    @api.depends('status')
    def _compute_is_active(self):
        for record in self:
            record.is_active = record.status == 'admitted'

    @api.depends('age')
    def _compute_age_numeric(self):
        for record in self:
            if record.age:
                # Extract numeric age from string like "25y 3m 15d" or "25 years"
                import re
                age_match = re.search(r'(\d+)', record.age)
                if age_match:
                    record.age_numeric = int(age_match.group(1))
                else:
                    record.age_numeric = 0
            else:
                record.age_numeric = 0

    @api.depends('worst_temperature', 'worst_heart_rate', 'worst_respiratory_rate', 'worst_sodium',
                 'worst_potassium', 'worst_creatinine', 'worst_hematocrit', 'worst_wbc',
                 'worst_arterial_ph', 'glasgow_coma_scale', 'age_numeric', 'chronic_health_points')
    def _compute_apache_ii_score(self):
        for record in self:
            score = 0

            # Temperature points
            temp = record.worst_temperature
            if temp >= 41 or temp <= 29.9:
                score += 4
            elif (temp >= 39 and temp <= 40.9) or (temp >= 30 and temp <= 31.9):
                score += 3
            elif (temp >= 38.5 and temp <= 38.9) or (temp >= 32 and temp <= 33.9):
                score += 1
            elif temp >= 34 and temp <= 35.9:
                score += 2

            # Heart Rate points
            hr = record.worst_heart_rate
            if hr >= 180 or hr <= 39:
                score += 4
            elif hr >= 140 or hr <= 54:
                score += 3
            elif hr >= 110 or hr <= 69:
                score += 2

            # Respiratory Rate points
            rr = record.worst_respiratory_rate
            if rr >= 50 or rr <= 5:
                score += 4
            elif rr >= 35:
                score += 3
            elif rr >= 25 or rr <= 9:
                score += 1
            elif rr <= 11:
                score += 2

            # Glasgow Coma Scale points (15 - actual score)
            score += 15 - record.glasgow_coma_scale

            # Age points
            age = record.age_numeric or 0
            if age >= 75:
                score += 6
            elif age >= 65:
                score += 5
            elif age >= 55:
                score += 3
            elif age >= 45:
                score += 2

            # Chronic health points
            score += record.chronic_health_points

            # Lab values (simplified - would need more complex logic for full APACHE II)
            if record.worst_sodium < 130 or record.worst_sodium > 150:
                score += 2
            if record.worst_potassium < 3.0 or record.worst_potassium > 5.5:
                score += 2
            if record.worst_creatinine > 2.0:
                score += 2

            record.apache_ii_score = score

    @api.depends('pao2_fio2_ratio', 'platelets', 'bilirubin', 'current_bp_systolic',
                 'cardiovascular_support', 'glasgow_coma_scale', 'worst_creatinine')
    def _compute_sofa_score(self):
        for record in self:
            score = 0

            # Respiratory (PaO2/FiO2)
            pf_ratio = record.pao2_fio2_ratio
            if pf_ratio < 100:
                score += 4
            elif pf_ratio < 200:
                score += 3
            elif pf_ratio < 300:
                score += 2
            elif pf_ratio < 400:
                score += 1

            # Coagulation (Platelets)
            platelets = record.platelets
            if platelets < 20:
                score += 4
            elif platelets < 50:
                score += 3
            elif platelets < 100:
                score += 2
            elif platelets < 150:
                score += 1

            # Liver (Bilirubin)
            bilirubin = record.bilirubin
            if bilirubin >= 12.0:
                score += 4
            elif bilirubin >= 6.0:
                score += 3
            elif bilirubin >= 2.0:
                score += 2
            elif bilirubin >= 1.2:
                score += 1

            # Cardiovascular
            if record.cardiovascular_support == 'dopamine_15_plus':
                score += 4
            elif record.cardiovascular_support == 'dopamine_15':
                score += 3
            elif record.cardiovascular_support == 'dopamine_5':
                score += 2
            elif record.current_bp_systolic < 70:
                score += 1

            # Central Nervous System (Glasgow Coma Scale)
            gcs = record.glasgow_coma_scale
            if gcs < 6:
                score += 4
            elif gcs < 10:
                score += 3
            elif gcs < 13:
                score += 2
            elif gcs < 15:
                score += 1

            # Renal (Creatinine)
            creatinine = record.worst_creatinine
            if creatinine >= 5.0:
                score += 4
            elif creatinine >= 3.5:
                score += 3
            elif creatinine >= 2.0:
                score += 2
            elif creatinine >= 1.2:
                score += 1

            record.sofa_score = score

    @api.depends('current_temperature', 'current_heart_rate', 'current_bp_systolic',
                 'current_bp_diastolic', 'current_respiratory_rate', 'current_oxygen_saturation')
    def _compute_vital_signs_status(self):
        for record in self:
            critical_count = 0
            warning_count = 0

            # Temperature alerts
            temp = record.current_temperature
            if temp and (temp >= 40 or temp <= 35):
                critical_count += 1
            elif temp and (temp >= 38.5 or temp <= 36):
                warning_count += 1

            # Heart rate alerts
            hr = record.current_heart_rate
            if hr and (hr >= 150 or hr <= 50):
                critical_count += 1
            elif hr and (hr >= 120 or hr <= 60):
                warning_count += 1

            # Blood pressure alerts
            systolic = record.current_bp_systolic
            if systolic and (systolic >= 180 or systolic <= 80):
                critical_count += 1
            elif systolic and (systolic >= 160 or systolic <= 90):
                warning_count += 1

            # Respiratory rate alerts
            rr = record.current_respiratory_rate
            if rr and (rr >= 30 or rr <= 8):
                critical_count += 1
            elif rr and (rr >= 24 or rr <= 12):
                warning_count += 1

            # Oxygen saturation alerts
            spo2 = record.current_oxygen_saturation
            if spo2 and spo2 <= 88:
                critical_count += 1
            elif spo2 and spo2 <= 92:
                warning_count += 1

            if critical_count > 0:
                record.vital_signs_status = 'critical'
            elif warning_count > 0:
                record.vital_signs_status = 'warning'
            else:
                record.vital_signs_status = 'normal'

    @api.depends('current_temperature', 'current_heart_rate', 'current_bp_systolic',
                 'current_bp_diastolic', 'current_respiratory_rate', 'current_oxygen_saturation',
                 'apache_ii_score', 'sofa_score')
    def _compute_alerts(self):
        for record in self:
            alerts = []

            # Vital signs alerts
            if record.current_temperature and record.current_temperature >= 40:
                alerts.append("⚠️ CRITICAL: High fever (≥40°C)")
            elif record.current_temperature and record.current_temperature <= 35:
                alerts.append("⚠️ CRITICAL: Hypothermia (≤35°C)")

            if record.current_heart_rate and record.current_heart_rate >= 150:
                alerts.append("⚠️ CRITICAL: Severe tachycardia (≥150 bpm)")
            elif record.current_heart_rate and record.current_heart_rate <= 50:
                alerts.append("⚠️ CRITICAL: Severe bradycardia (≤50 bpm)")

            if record.current_bp_systolic and record.current_bp_systolic <= 80:
                alerts.append("⚠️ CRITICAL: Severe hypotension (≤80 mmHg)")
            elif record.current_bp_systolic and record.current_bp_systolic >= 180:
                alerts.append("⚠️ CRITICAL: Severe hypertension (≥180 mmHg)")

            if record.current_oxygen_saturation and record.current_oxygen_saturation <= 88:
                alerts.append("⚠️ CRITICAL: Severe hypoxemia (≤88%)")

            # Scoring alerts
            if record.apache_ii_score >= 25:
                alerts.append("🚨 HIGH RISK: APACHE II score ≥25 (mortality risk >50%)")
            elif record.apache_ii_score >= 15:
                alerts.append("⚠️ MODERATE RISK: APACHE II score ≥15")

            if record.sofa_score >= 15:
                alerts.append("🚨 CRITICAL: SOFA score ≥15 (organ failure)")
            elif record.sofa_score >= 10:
                alerts.append("⚠️ HIGH RISK: SOFA score ≥10")

            record.alert_messages = '\n'.join(alerts) if alerts else 'No active alerts'

    @api.model_create_multi
    def create(self, vals_list):
        admissions = super(intarvasICUAdmission, self).create(vals_list)
        for admission in admissions:
            if admission.name == _('New'):
                admission.name = self.env['ir.sequence'].next_by_code('oeh.medical.icu.admission') or _('New')
            # Update bed status
            if admission.bed_id:
                admission.bed_id.state = 'Occupied'
        return admissions

    def action_discharge(self):
        """Discharge patient from ICU"""
        self.ensure_one()
        if self.status != 'admitted':
            raise UserError(_('Patient is not currently admitted'))

        self.status = 'discharged'
        self.discharge_date = fields.Datetime.now()
        if self.bed_id:
            self.bed_id.state = 'Free'

        return True

    def action_auto_monitoring(self):
        """Automatically create monitoring record based on current vitals"""
        self.ensure_one()
        if self.status != 'admitted':
            raise UserError(_('Patient is not currently admitted'))

        # Auto-populate worst values if not set
        if not self.worst_temperature and self.current_temperature:
            self.worst_temperature = self.current_temperature
        if not self.worst_heart_rate and self.current_heart_rate:
            self.worst_heart_rate = self.current_heart_rate
        if not self.worst_respiratory_rate and self.current_respiratory_rate:
            self.worst_respiratory_rate = self.current_respiratory_rate

        # Create monitoring record
        monitoring_vals = {
            'admission_id': self.id,
            'monitoring_datetime': fields.Datetime.now(),
            'temperature': self.current_temperature,
            'heart_rate': self.current_heart_rate,
            'blood_pressure_systolic': self.current_bp_systolic,
            'blood_pressure_diastolic': self.current_bp_diastolic,
            'respiratory_rate': self.current_respiratory_rate,
            'oxygen_saturation': self.current_oxygen_saturation,
            'glasgow_coma_scale': self.glasgow_coma_scale,
            'notes': self.current_monitoring_notes,
            'responsible_nurse_id': self.responsible_nurse_id.id,
            'shift': 'day' if 6 <= fields.Datetime.now().hour < 18 else 'night',
            'auto_generated': True,
        }

        monitoring = self.env['oeh.medical.icu.monitoring'].create(monitoring_vals)
        self.last_monitoring_datetime = fields.Datetime.now()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Monitoring Record',
            'res_model': 'oeh.medical.icu.monitoring',
            'res_id': monitoring.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_quick_assessment(self):
        """Quick assessment wizard for rapid data entry"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Quick ICU Assessment',
            'res_model': 'oeh.medical.icu.quick.assessment',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_admission_id': self.id}
        }

    @api.model
    def auto_risk_assessment(self):
        """Cron job to automatically assess high-risk patients"""
        high_risk_admissions = self.search([
            ('status', '=', 'admitted'),
            '|', ('apache_ii_score', '>=', 15),
            ('sofa_score', '>=', 10)
        ])

        for admission in high_risk_admissions:
            # Send notification to responsible nurse
            if admission.responsible_nurse_id:
                admission.message_post(
                    body=f"High-risk patient alert: {admission.patient_id.name} has elevated risk scores. "
                         f"APACHE II: {admission.apache_ii_score}, SOFA: {admission.sofa_score}",
                    partner_ids=[admission.responsible_nurse_id.partner_id.id],
                    subject="High-Risk Patient Alert"
                )



class intarvasICUMonitoring(models.Model):
    _name = 'oeh.medical.icu.monitoring'
    _description = 'ICU Patient Monitoring'
    _order = 'monitoring_datetime desc'

    MONITORING_SHIFTS = [
        ('day', 'Day Shift'),
        ('night', 'Night Shift'),
    ]

    admission_id = fields.Many2one('oeh.medical.icu.admission', string='ICU Admission',
                                  required=True, ondelete='cascade')
    patient_id = fields.Many2one(related='admission_id.patient_id', string='Patient', readonly=True)

    monitoring_datetime = fields.Datetime(string='Monitoring Date/Time', required=True,
                                         default=fields.Datetime.now)
    shift = fields.Selection(MONITORING_SHIFTS, string='Shift', required=True, default='day')

    # Basic Vital Signs
    temperature = fields.Float(string='Temperature (°C)')
    heart_rate = fields.Integer(string='Heart Rate (bpm)')
    blood_pressure_systolic = fields.Integer(string='BP Systolic (mmHg)')
    blood_pressure_diastolic = fields.Integer(string='BP Diastolic (mmHg)')
    respiratory_rate = fields.Integer(string='Respiratory Rate (/min)')
    oxygen_saturation = fields.Integer(string='Oxygen Saturation (%)')
    glasgow_coma_scale = fields.Integer(string='Glasgow Coma Scale')

    # Notes
    notes = fields.Text(string='Monitoring Notes')
    responsible_nurse_id = fields.Many2one('res.users', string='Responsible Nurse')
    auto_generated = fields.Boolean(string='Auto Generated', default=False)


class intarvasICUQuickAssessment(models.TransientModel):
    _name = 'oeh.medical.icu.quick.assessment'
    _description = 'Quick ICU Assessment Wizard'

    admission_id = fields.Many2one('oeh.medical.icu.admission', string='ICU Admission', required=True)

    # Quick vital signs entry
    temperature = fields.Float(string='Temperature (°C)')
    heart_rate = fields.Integer(string='Heart Rate (bpm)')
    bp_systolic = fields.Integer(string='BP Systolic (mmHg)')
    bp_diastolic = fields.Integer(string='BP Diastolic (mmHg)')
    respiratory_rate = fields.Integer(string='Respiratory Rate (/min)')
    oxygen_saturation = fields.Integer(string='Oxygen Saturation (%)')

    # Quick assessment options
    consciousness_level = fields.Selection([
        ('alert', 'Alert'),
        ('verbal', 'Responds to Verbal'),
        ('pain', 'Responds to Pain'),
        ('unresponsive', 'Unresponsive'),
    ], string='Consciousness Level')

    pain_score = fields.Integer(string='Pain Score (0-10)', default=0)

    # Quick notes
    assessment_notes = fields.Text(string='Assessment Notes')

    def action_save_assessment(self):
        """Save quick assessment to admission record"""
        self.ensure_one()

        # Update admission with current vitals
        vals = {}
        if self.temperature:
            vals['current_temperature'] = self.temperature
        if self.heart_rate:
            vals['current_heart_rate'] = self.heart_rate
        if self.bp_systolic:
            vals['current_bp_systolic'] = self.bp_systolic
        if self.bp_diastolic:
            vals['current_bp_diastolic'] = self.bp_diastolic
        if self.respiratory_rate:
            vals['current_respiratory_rate'] = self.respiratory_rate
        if self.oxygen_saturation:
            vals['current_oxygen_saturation'] = self.oxygen_saturation
        if self.assessment_notes:
            vals['current_monitoring_notes'] = self.assessment_notes

        # Update Glasgow Coma Scale based on consciousness level
        gcs_mapping = {
            'alert': 15,
            'verbal': 12,
            'pain': 8,
            'unresponsive': 3,
        }
        if self.consciousness_level:
            vals['glasgow_coma_scale'] = gcs_mapping.get(self.consciousness_level, 15)

        self.admission_id.write(vals)

        # Automatically create monitoring record
        self.admission_id.action_auto_monitoring()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Quick assessment completed and monitoring record created'),
                'type': 'success',
            }
        }