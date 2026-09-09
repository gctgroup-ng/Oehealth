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
import datetime


# Injury Examination Procedures details
class intarvasInjuryExaminationProcedure(models.Model):
    _name = 'oeh.medical.injury.examination'
    _description = 'Injury Examination Procedures'
    _order = 'id desc'

    INJURY_TYPE = [
        ('Unintentional / Accidental', 'Unintentional / Accidental'),
        ('Suicide Attempt', 'Suicide Attempt'),
        ('Violence', 'Violence'),
        ('Vehicle Accident', 'Vehicle Accident'),
        ('Traumatic', 'Traumatic')
    ]

    VEHICLE_TYPE = [
        ('Pedestrian', 'Pedestrian'),
        ('Bicycle', 'Bicycle'),
        ('Bike', 'Bike'),
        ('Car', 'Car'),
        ('Van / Pickup / Jeep', 'Van / Pickup / Jeep'),
        ('Truck / Heavy vehicle', 'Truck / Heavy vehicle'),
        ('Bus', 'Bus'),
        ('Train', 'Train'),
        ('Taxi', 'Taxi'),
        ('Aircraft', 'Aircraft'),
        ('Boat / Ship', 'Boat / Ship'),
        ('Unknown', 'Unknown')
    ]

    SAFETY_GEAR = [
        ('Yes', 'Yes'),
        ('No', 'No'),
        ('Unknown', 'Unknown')
    ]

    ALCOHOL_DRUG = [
        ('Yes', 'Yes'),
        ('No', 'No'),
        ('Suspected', 'Suspected'),
        ('Unknown', 'Unknown')
    ]

    VIOLENCE_BY = [
        ('Parent', 'Parent'),
        ('Guardian', 'Guardian'),
        ('Wife / Husband', 'Wife / Husband'),
        ('Girl Friend', 'Girl Friend'),
        ('Boy Friend', 'Boy Friend'),
        ('Friend', 'Friend'),
        ('Relative', 'Relative'),
        ('Officials', 'Officials'),
        ('Stranger', 'Stranger'),
        ('Unknown', 'Unknown'),
    ]

    CRIME_TYPE = [
        ('Fight', 'Fight'),
        ('Robbery', 'Robbery'),
        ('Because of Drugs', 'Because of Drugs'),
        ('Sexual Assault', 'Sexual Assault'),
        ('Gang Activity', 'Gang Activity'),
        ('Other', 'Other'),
        ('Unknown', 'Unknown'),
    ]

    CRIME_OBJECT = [
        ('Blunt object', 'Blunt object'),
        ('Push/body force', 'Push/body force'),
        ('Sharp objects', 'Sharp objects'),
        ('Shot by Gun', 'Shot by Gun'),
        ('Sexual Assault', 'Sexual Assault'),
        ('Choking', 'Choking'),
        ('Other', 'Other'),
        ('Unknown', 'Unknown'),
    ]

    STATES = [
        ('Draft', 'New Case'),
        ('Treated and Sent Home', 'Treated and Sent Home'),
        ('Admitted', 'Admitted'),
        ('Died', 'Died'),
        ('Dead on Arrival', 'Dead on Arrival'),
    ]

    ISS_TYPES = [
        ('0', 'No Injury'),
        ('1', 'Minor'),
        ('4', 'Moderate'),
        ('9', 'Serious'),
        ('16', 'Severe'),
        ('25', 'Critical'),
        ('75', 'Unsurvivable'),
    ]

    # Automatically detect logged in physician

    def _get_physician(self):
        """Return default physician value"""
        therapist_obj = self.env['oeh.medical.physician']
        domain = [('oeh_user_id', '=', self.env.uid)]
        user_ids = therapist_obj.search(domain, limit=1)
        if user_ids:
            return user_ids.id or False
        else:
            return False


    def _patient_age(self):
        def compute_age_from_dates(injury_date, patient_dob):
            #injury_date = datetime.datetime.strptime(str(injury_date), '%Y-%m-%d %H:%M:%S')
            if patient_dob:
                dob = patient_dob
                delta = injury_date.date() - dob
                years_months_days = str(delta.days // 365) + " years " + str(delta.days % 365) + " days"
            else:
                years_months_days = "No DoB !"

            return years_months_days
        for patient_data in self:
            patient_data.age = compute_age_from_dates(patient_data.date, patient_data.patient.dob)
        return True

    name = fields.Char(string='Case #', size=128, readonly=True, required=True, default=lambda *a: '/')
    patient = fields.Many2one('oeh.medical.patient', string='Patient', help="Patient Name", domain=[('deceased','=',False)], required=True)
    date = fields.Datetime(string='Injury Date', required=True, default=datetime.datetime.now())
    age = fields.Char(compute=_patient_age, size=64, string='Age at the time of Injury')
    doctor = fields.Many2one('oeh.medical.physician', string='Doctor', domain=[('is_pharmacist','=',False)], default=_get_physician)
    institution = fields.Many2one('oeh.medical.health.center', string='Health Center', help="Institution where doctor works")
    patient_status = fields.Char(string='Patient status when arrived')
    injury_type = fields.Selection(INJURY_TYPE, 'Type of Injury', required=True, default=lambda *a: 'Unintentional / Accidental')
    vehicle_type = fields.Selection(VEHICLE_TYPE, 'Vehicle')
    safety_gear = fields.Selection(SAFETY_GEAR, 'Was wearing safety gear?')
    alcohol = fields.Selection(ALCOHOL_DRUG, 'Evidence of Alcohol consumption', help='Is there evidence of alcohol use by the injured person on or before 6 hours of the accident?')
    drug = fields.Selection(ALCOHOL_DRUG, 'Evidence of Drug consumption', help='Is there evidence of drug use by the injured person on or before 6 hours of the accident?')
    violence_by = fields.Selection(VIOLENCE_BY, 'Violence By')
    crime_type = fields.Selection(CRIME_TYPE, 'Nature of Crime')
    crime_method = fields.Selection(CRIME_OBJECT, 'Method use in Crime')
    injury_details = fields.Text(string='Injury Details', required=True)
    address = fields.Char(string='Address of Injury Occurrence', required=True)
    examination_details = fields.Text(string='Examination Result')
    iss_head_neck_injury = fields.Selection(ISS_TYPES, string="Head and neck injury")
    iss_face_injury = fields.Selection(ISS_TYPES, string="Face injury")
    iss_chest_injury = fields.Selection(ISS_TYPES, string="Chest injury")
    iss_abdomen_injury = fields.Selection(ISS_TYPES, string="Abdomen injury")
    iss_extremity_injury = fields.Selection(ISS_TYPES, string="Extremity (including pelvis) injury")
    iss_external_injury = fields.Selection(ISS_TYPES, string="External injury")
    iss_score = fields.Integer(string="Score")
    iss_out_of_75 = fields.Char(string="out of 75 label", readonly=True, default=lambda *a: '(out of 75)')
    inpatient = fields.Many2one('oeh.medical.inpatient', string='Inpatient Admission #')
    state = fields.Selection(STATES, string='State', default=lambda *a: 'Draft')

    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('oeh.medical.injury.examination')
        vals['name'] = sequence or '/'
        injury_no = super(intarvasInjuryExaminationProcedure, self).create(vals)
        return injury_no

    @api.onchange('iss_head_neck_injury', 'iss_face_injury',
                  'iss_chest_injury', 'iss_abdomen_injury', 'iss_extremity_injury',
                  'iss_external_injury')
    def on_change_with_iss_total(self):
        iss_score_list = []
        final_iss_score = 0

        # Make list of array to temporarily store different criteria score
        if self.iss_head_neck_injury:
            iss_score_list += [int(self.iss_head_neck_injury)]
        if self.iss_face_injury:
            iss_score_list += [int(self.iss_face_injury)]
        if self.iss_chest_injury:
            iss_score_list += [int(self.iss_chest_injury)]
        if self.iss_abdomen_injury:
            iss_score_list += [int(self.iss_abdomen_injury)]
        if self.iss_extremity_injury:
            iss_score_list += [int(self.iss_extremity_injury)]
        if self.iss_external_injury:
            iss_score_list += [int(self.iss_external_injury)]

        # Calculate ISS Score
        if len(iss_score_list) > 3:
            three_highest_number = sorted(zip(iss_score_list), reverse=True)[:3]
            for iss_items in three_highest_number:
                if iss_items[0] == 75:
                    final_iss_score = iss_items[0]
                else:
                    final_iss_score += iss_items[0]
        else:
            for iss_items in iss_score_list:
                if iss_items == 75:
                    final_iss_score = iss_items
                else:
                    final_iss_score += iss_items

        # ISS Scope must not be greater than 75 as per international standards
        if final_iss_score > 75:
            self.iss_score = 75
        else:
            self.iss_score = final_iss_score

    @api.onchange('iss_score')
    def on_change_iss_score(self):
        self.on_change_with_iss_total()


    def print_injury_examination_report(self):
        return self.env.ref('intarvas.action_oeh_medical_report_injury_examination_result').report_action(self)


