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

# Perinantal Monitor Management
class intarvasPerinatalMonitor(models.Model):
    _name = "oeh.medical.perinatal.monitor"
    _description = "Gyneco Perinatal Monitor"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    FETUS_POSITION = [
        ('Correct','Correct'),
        ('Occiput / Cephalic Posterior', 'Occiput / Cephalic Posterior'),
        ('Frank Breech', 'Frank Breech'),
        ('Complete Breech', 'Complete Breech'),
        ('Transverse Lie', 'Transverse Lie'),
        ('Footling Breech', 'Footling Breech'),
    ]

    name = fields.Char(string='Internal Code', size=128, required=True, readonly=True, default=lambda *a: '/', tracking=True)
    date = fields.Datetime(string='Date and Time', required=True, default=datetime.datetime.now(), tracking=True)
    systolic = fields.Integer(string='Systolic Pressure', tracking=True)
    diastolic = fields.Integer(string='Diastolic Pressure', tracking=True)
    contractions = fields.Integer(string='Contractions', tracking=True)
    frequency = fields.Integer(string='Mother\'s Heart Frequency', tracking=True)
    dilation = fields.Integer(string='Cervix Dilation', tracking=True)
    f_frequency = fields.Integer(string='Fetus Heart Frequency', tracking=True)
    meconium = fields.Boolean(string='Meconium', tracking=True)
    bleeding = fields.Boolean(string='Bleeding', tracking=True)
    fundal_height = fields.Integer(string='Fundal Height', tracking=True)
    fetus_position = fields.Selection(FETUS_POSITION, string='Fetus Position', index=True, tracking=True)
    gyneco_id = fields.Many2one('oeh.medical.gyneco', string='Gynecology', ondelete='cascade', tracking=True)

    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('oeh.medical.perinatal.monitor')
        vals['name'] = sequence or '/'
        return super(intarvasPerinatalMonitor, self).create(vals)


# Puerperium Monitor Management
class intarvasPuerperiumMonitor(models.Model):
    _name = "oeh.medical.puerperium.monitor"
    _description = "Gyneco Puerperium Monitor"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    LOCHIA_AMOUNT = [
        ('Normal','Normal'),
        ('Abundant', 'Abundant'),
        ('Hemorrhage', 'Hemorrhage'),
    ]

    LOCHIA_COLOR = [
        ('Rubra','Rubra'),
        ('Serosa', 'Serosa'),
        ('Alba', 'Alba'),
    ]

    LOCHIA_ODOR = [
        ('Normal','Normal'),
        ('Offensive', 'Offensive'),
    ]

    name = fields.Char(string='Internal Code', size=128, required=True, readonly=True, default=lambda *a: '/', tracking=True)
    date = fields.Datetime(string='Date and Time', required=True, default=datetime.datetime.now(), tracking=True)
    systolic = fields.Integer(string='Systolic Pressure', tracking=True)
    diastolic = fields.Integer(string='Diastolic Pressure', tracking=True)
    frequency = fields.Integer(string='Heart Frequency', tracking=True)
    lochia_amount = fields.Selection(LOCHIA_AMOUNT, string='Lochia Amount', tracking=True)
    lochia_color = fields.Selection(LOCHIA_COLOR, string='Lochia Color', tracking=True)
    lochia_odor = fields.Selection(LOCHIA_ODOR, string='Lochia Odor', tracking=True)
    uterus_involution = fields.Integer(string='Fundal Height', help="Distance between the symphysis pubis and the uterine fundus (S-FD) in cm", tracking=True)
    temperature = fields.Float(string='Temperature', tracking=True)
    gyneco_id = fields.Many2one('oeh.medical.gyneco', string='Gynecology', ondelete='cascade', tracking=True)

    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('oeh.medical.puerperium.monitor')
        vals['name'] = sequence or '/'
        return super(intarvasPuerperiumMonitor, self).create(vals)


# Gynecology Management
class intarvasGyneco(models.Model):
    _name = "oeh.medical.gyneco"
    _description = "Gynecology Management"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    LABOR_MODE = [
        ('Normal','Normal'),
        ('Induced', 'Induced'),
        ('C-section', 'C-section'),
    ]

    FETUS = [
        ('Correct','Correct'),
        ('Occiput / Cephalic Posterior', 'Occiput / Cephalic Posterior'),
        ('Frank Breech', 'Frank Breech'),
        ('Complete Breech', 'Complete Breech'),
        ('Transverse Lie', 'Transverse Lie'),
        ('Footling Breech','Footling Breech'),
    ]

    FETUS_POSITION = [
        ('Correct', 'Correct'),
        ('Occiput / Cephalic Posterior', 'Occiput / Cephalic Posterior'),
        ('Frank Breech', 'Frank Breech'),
        ('Complete Breech', 'Complete Breech'),
        ('Transverse Lie', 'Transverse Lie'),
        ('Footling Breech', 'Footling Breech'),
    ]

    LOCHIA_AMOUNT = [
        ('Normal', 'Normal'),
        ('Abundant', 'Abundant'),
        ('Hemorrhage', 'Hemorrhage'),
    ]
    LOCHIA_COLOR = [
        ('Rubra', 'Rubra'),
        ('Serosa', 'Serosa'),
        ('Alba', 'Alba'),
    ]

    LOCHIA_ODOR = [
        ('Normal', 'Normal'),
        ('Offensive', 'Offensive'),
    ]

    lochia_odor = fields.Selection(LOCHIA_ODOR, string='Lochia Odor')
    lochia_color = fields.Selection(LOCHIA_COLOR, string='Lochia Color')
    lochia_amount = fields.Selection(LOCHIA_AMOUNT, string='Lochia Amount')
    uterus_involution = fields.Integer(string='Fundal Height',
        help="Distance between the symphysis pubis and the uterine fundus (S-FD) in cm")
    temperature = fields.Float(string='Temperature')
    meconium = fields.Boolean(string='Meconium')
    bleeding = fields.Boolean(string='Bleeding')
    f_frequency = fields.Integer(string='Fetus Heart Frequency')
    fetus_position = fields.Selection(FETUS_POSITION, string='Fetus Position', index=True)
    systolic = fields.Integer(string='Systolic Pressure')
    date = fields.Datetime(string='Date and Time', required=True, default=datetime.datetime.now())
    diastolic = fields.Integer(string='Diastolic Pressure')
    frequency = fields.Integer(string='Mother\'s Heart Frequency')
    dilation = fields.Integer(string='Cervix Dilation')


    name = fields.Char(string='Internal Code', size=128, required=True, readonly=True, default=lambda *a: '/', tracking=True)
    gravida_number = fields.Integer(string='Gravida #', tracking=True)
    abortion = fields.Boolean(string='Abortion', tracking=True)
    abortion_reason = fields.Char(string='Abortion Reason', size=128, tracking=True)
    admission_date = fields.Datetime(string='Admission Date', help="Date when she was admitted to give birth", tracking=True)
    prenatal_evaluations = fields.Integer(string='# of Visit to Doctor', help="Number of visits to the doctor during pregnancy", tracking=True)
    labor_mode = fields.Selection(LABOR_MODE, string='Labor Starting Mode', tracking=True)
    gestational_weeks = fields.Integer(string='Gestational Weeks', tracking=True)
    gestational_days = fields.Integer(string='Gestational Days', tracking=True)
    fetus_presentation = fields.Selection(FETUS, string='Fetus Presentation', tracking=True)
    placenta_incomplete = fields.Boolean(string='Incomplete Placenta', tracking=True)
    placenta_retained = fields.Boolean(string='Retained Placenta', tracking=True)
    episiotomy = fields.Boolean(string='Episiotomy', tracking=True)
    vaginal_tearing = fields.Boolean(string='Vaginal Tearing', tracking=True)
    forceps = fields.Boolean(string='Use of Forceps', tracking=True)
    perinatal_ids = fields.One2many('oeh.medical.perinatal.monitor','gyneco_id', string='Perinatal', tracking=True)
    puerperium_ids = fields.One2many('oeh.medical.puerperium.monitor','gyneco_id', string='Puerperium', tracking=True)
    dismissed = fields.Datetime(string='Dismissed from Hospital', tracking=True)
    died_at_delivery = fields.Boolean(string='Died at Delivery Room', tracking=True)
    died_at_the_hospital = fields.Boolean(string='Died at the Hospital', tracking=True)
    died_being_transferred = fields.Boolean(string='Died being Transferred', help="The mother died being transferred to another health institution", tracking=True)
    notes = fields.Text(string='Notes', tracking=True)
    patient = fields.Many2one('oeh.medical.patient', string='Patient', ondelete='cascade', tracking=True)

    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('oeh.medical.gyneco')
        vals['name'] = sequence or '/'
        return super(intarvasGyneco, self).create(vals)


# Inheriting Patient module to add "Gyanecology" screen reference
class intarvasPatient(models.Model):
    _inherit = 'oeh.medical.patient'

    currently_pregnant = fields.Boolean(string='Currently Pregnant')
    fertile = fields.Boolean(string='Fertile', help="Check if patient is in fertile age")
    menarche = fields.Integer(string='Menarche Age')
    menopausal = fields.Boolean(string='Menopausal')
    menopause = fields.Integer(string='Menopause Age')
    mammography = fields.Boolean(string='Mammography', help="Check if the patient does periodic mammographys")
    mammography_last = fields.Date(string='Last Mammography', help="Enter the date of the last mammography")
    breast_self_examination = fields.Boolean(string='Breast Self-examination', help="Check if the patient does and knows how to self examine her breasts")
    pap_test = fields.Boolean(string='PAP Test', help="Check if the patient does periodic cytologic pelvic smear screening")
    pap_test_last = fields.Date(string='Last PAP Test', help="Enter the date of the last Papanicolau test")
    colposcopy = fields.Boolean(string='Colposcopy', help="Check if the patient has done a colposcopy exam")
    colposcopy_last = fields.Date('Last Colposcopy', help="Enter the date of the last colposcopy")
    gravida = fields.Integer(string='Gravida', help="Number of pregnancies")
    premature = fields.Integer(string='Premature', help="Premature Deliveries")
    abortions = fields.Integer(string='No of Abortions')
    full_term = fields.Integer(string='Full Term', help="Full term pregnancies")
    gpa = fields.Char(string='GPA', size=32, help="Gravida, Para, Abortus Notation. For example G4P3A1 : 4 Pregnancies, 3 viable and 1 abortion")
    born_alive = fields.Integer(string='Born Alive')
    deaths_1st_week = fields.Integer(string='Deceased during 1st week', help="Number of babies that die in the first week")
    deaths_2nd_week = fields.Integer(string='Deceased after 2nd week', help="Number of babies that die after the second week")
    gyneco_ids = fields.One2many('oeh.medical.gyneco', 'patient', string='Perinatal', tracking=True)
