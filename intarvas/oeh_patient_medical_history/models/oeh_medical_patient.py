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

from odoo import fields, api, models, _

 # Inheriting Patient module to add fields to record patient medical histories
class intarvasPatient(models.Model):
    _inherit='oeh.medical.patient'

    hbv_infection_chk = fields.Boolean(string='HBV Infection')
    hbv_infection_remarks = fields.Text(string='HBV Infection Remarks')
    dm_chk = fields.Boolean(string='DM')
    dm_remarks = fields.Text(string='DM Remarks')
    ihd_chk = fields.Boolean(string='IHD')
    ihd_remarks = fields.Text(string='IHD Remarks')
    cold_chk = fields.Boolean(string='Cold')
    cold_remarks = fields.Text(string='Cold Remarks')
    hypertension_chk = fields.Boolean(string='Hypertension')
    hypertension_remarks = fields.Text(string='Hypertension Remarks')
    surgery_chk = fields.Boolean(string='Surgery')
    surgery_remarks = fields.Text(string='Surgery Remarks')
    others_past_illness = fields.Text(string='Others Past Illness')
    nsaids_chk = fields.Boolean(string='Nsaids')
    nsaids_remarks = fields.Text(string='Nsaids Remarks')
    aspirin_chk = fields.Boolean(string='Aspirin')
    aspirin_remarks = fields.Text(string='Aspirin Remarks')
    laxative_chk = fields.Boolean(string='Laxative')
    laxative_remarks = fields.Text(string='Laxative Remarks')
    others_drugs = fields.Text(string='Others Drugs')
    lmp_chk = fields.Boolean(string='LMP')
    lmp_dt = fields.Date(string='Date')
    menorrhagia_chk = fields.Boolean(string='Menorrhagia')
    menorrhagia_remarks = fields.Text(string='Menorrhagia Remarks')
    dysmenorrhoea_chk = fields.Boolean(string='Dysmenorrhoea')
    dysmenorrhoea_remarks = fields.Text(string='Dysmenorrhoea Remarks')
    bleeding_pv_chk = fields.Boolean(string='Bleeding PV')
    bleeding_pv_remarks = fields.Text(string='Bleeding PV Remarks')
    last_pap_smear_chk = fields.Boolean(string='Last PAP smear')
    last_pap_smear_remarks = fields.Text(string='Last PAP smear Remarks')


# Inheriting Appointment module to add fields to record patient medical histories
class intarvasAppointment(models.Model):
    _inherit='oeh.medical.appointment'

    hbv_infection_chk = fields.Boolean(string='HBV Infection')
    hbv_infection_remarks = fields.Text(string='HBV Infection Remarks')
    dm_chk = fields.Boolean(string='DM')
    dm_remarks = fields.Text(string='DM Remarks')
    ihd_chk = fields.Boolean(string='IHD')
    ihd_remarks = fields.Text(string='IHD Remarks')
    cold_chk = fields.Boolean(string='Cold')
    cold_remarks = fields.Text(string='Cold Remarks')
    hypertension_chk = fields.Boolean(string='Hypertension')
    hypertension_remarks = fields.Text(string='Hypertension Remarks')
    surgery_chk = fields.Boolean(string='Surgery')
    surgery_remarks = fields.Text(string='Surgery Remarks')
    others_past_illness = fields.Text(string='Others Past Illness')
    nsaids_chk = fields.Boolean(string='Nsaids')
    nsaids_remarks = fields.Text(string='Nsaids Remarks')
    aspirin_chk = fields.Boolean(string='Aspirin')
    aspirin_remarks = fields.Text(string='Aspirin Remarks')
    laxative_chk = fields.Boolean(string='Laxative')
    laxative_remarks = fields.Text(string='Laxative Remarks')
    others_drugs = fields.Text(string='Others Drugs')
    lmp_chk = fields.Boolean(string='LMP')
    lmp_dt = fields.Date(string='Date')
    menorrhagia_chk = fields.Boolean(string='Menorrhagia')
    menorrhagia_remarks = fields.Text(string='Menorrhagia Remarks')
    dysmenorrhoea_chk = fields.Boolean(string='Dysmenorrhoea')
    dysmenorrhoea_remarks = fields.Text(string='Dysmenorrhoea Remarks')
    bleeding_pv_chk = fields.Boolean(string='Bleeding PV')
    bleeding_pv_remarks = fields.Text(string='Bleeding PV Remarks')
    last_pap_smear_chk = fields.Boolean(string='Last PAP smear')
    last_pap_smear_remarks = fields.Text(string='Last PAP smear Remarks')


    @api.onchange('patient')
    def onchange_patient_history(self):
        if self.patient:
            self.hbv_infection_chk = self.patient.hbv_infection_chk or False
            self.hbv_infection_remarks = self.patient.hbv_infection_remarks or ''
            self.dm_chk = self.patient.dm_chk or False
            self.dm_remarks = self.patient.dm_remarks or ''
            self.ihd_chk = self.patient.ihd_chk or False
            self.ihd_remarks = self.patient.ihd_remarks or ''
            self.cold_chk = self.patient.cold_chk or False
            self.cold_remarks = self.patient.cold_remarks or ''
            self.hypertension_chk = self.patient.hypertension_chk or False
            self.hypertension_remarks = self.patient.hypertension_remarks or ''
            self.surgery_chk = self.patient.surgery_chk or False
            self.surgery_remarks = self.patient.surgery_remarks or ''
            self.others_past_illness = self.patient.others_past_illness or ''
            self.nsaids_chk = self.patient.nsaids_chk or False
            self.nsaids_remarks = self.patient.nsaids_remarks or ''
            self.aspirin_chk = self.patient.aspirin_chk or False
            self.aspirin_remarks = self.patient.aspirin_remarks or ''
            self.laxative_chk = self.patient.laxative_chk or False
            self.laxative_remarks = self.patient.laxative_remarks or ''
            self.others_drugs = self.patient.others_drugs or ''
            self.lmp_chk = self.patient.lmp_chk or False
            self.lmp_dt = self.patient.lmp_dt or ''
            self.menorrhagia_chk = self.patient.menorrhagia_chk or False
            self.menorrhagia_remarks = self.patient.menorrhagia_remarks or ''
            self.dysmenorrhoea_chk = self.patient.dysmenorrhoea_chk or False
            self.dysmenorrhoea_remarks = self.patient.dysmenorrhoea_remarks or ''
            self.bleeding_pv_chk = self.patient.bleeding_pv_chk or False
            self.bleeding_pv_remarks = self.patient.bleeding_pv_remarks or ''
            self.last_pap_smear_chk = self.patient.last_pap_smear_chk or False
            self.last_pap_smear_remarks = self.patient.last_pap_smear_remarks or ''