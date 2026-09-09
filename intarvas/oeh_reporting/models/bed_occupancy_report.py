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

from odoo import api, fields, models, tools


class BedOccupancyReport(models.Model):
    _name = "oeh.medical.bed.occupancy.report"
    _description = "Bed Occupancy Report"
    _auto = False
    _rec_name = 'ward_id'
    _order = 'institution_id, ward_id'

    institution_id = fields.Many2one('oeh.medical.health.center', string='Institution', readonly=True)
    ward_id = fields.Many2one('oeh.medical.health.center.ward', string='Ward', readonly=True)
    ward_name = fields.Char(string='Ward Name', readonly=True)
    building_id = fields.Many2one('oeh.medical.health.center.building', string='Building', readonly=True)

    # Bed statistics
    total_beds = fields.Integer(string='Total Beds', readonly=True)
    occupied_beds = fields.Integer(string='Occupied Beds', readonly=True)
    free_beds = fields.Integer(string='Free Beds', readonly=True)
    reserved_beds = fields.Integer(string='Reserved Beds', readonly=True)
    occupancy_rate = fields.Float(string='Occupancy Rate (%)', readonly=True)

    # Admission statistics
    total_admissions = fields.Integer(string='Total Admissions', readonly=True)
    current_admissions = fields.Integer(string='Current Admissions', readonly=True)
    avg_stay_duration = fields.Float(string='Avg Stay (Days)', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """
            CREATE OR REPLACE VIEW %s AS (
                WITH bed_stats AS (
                    SELECT
                        w.institution as institution_id,
                        w.id as ward_id,
                        w.name as ward_name,
                        w.building as building_id,
                        COUNT(b.id) as total_beds,
                        COUNT(CASE WHEN b.state = 'Occupied' THEN 1 END) as occupied_beds,
                        COUNT(CASE WHEN b.state = 'Free' THEN 1 END) as free_beds,
                        COUNT(CASE WHEN b.state = 'Reserved' THEN 1 END) as reserved_beds
                    FROM
                        oeh_medical_health_center_ward w
                        LEFT JOIN oeh_medical_health_center_beds b ON (w.id = b.ward)
                    GROUP BY
                        w.institution, w.id, w.name, w.building
                ),
                admission_stats AS (
                    SELECT
                        i.ward as ward_id,
                        COUNT(i.id) as total_admissions,
                        COUNT(CASE WHEN i.state IN ('Hospitalized', 'Invoiced') THEN 1 END) as current_admissions,
                        AVG(
                            CASE
                                WHEN i.discharge_date IS NOT NULL AND i.admission_date IS NOT NULL
                                THEN EXTRACT(EPOCH FROM (i.discharge_date - i.admission_date)) / 86400
                                WHEN i.admission_date IS NOT NULL AND i.state IN ('Hospitalized', 'Invoiced')
                                THEN EXTRACT(EPOCH FROM (NOW() - i.admission_date)) / 86400
                                ELSE NULL
                            END
                        ) as avg_stay_duration
                    FROM
                        oeh_medical_inpatient i
                    GROUP BY
                        i.ward
                )
                SELECT
                    bs.ward_id as id,
                    bs.institution_id,
                    bs.ward_id,
                    bs.ward_name,
                    bs.building_id,
                    bs.total_beds,
                    bs.occupied_beds,
                    bs.free_beds,
                    bs.reserved_beds,
                    CASE
                        WHEN bs.total_beds > 0 THEN
                            (bs.occupied_beds::float / bs.total_beds::float * 100)
                        ELSE 0
                    END as occupancy_rate,
                    COALESCE(ast.total_admissions, 0) as total_admissions,
                    COALESCE(ast.current_admissions, 0) as current_admissions,
                    COALESCE(ast.avg_stay_duration, 0) as avg_stay_duration
                FROM
                    bed_stats bs
                    LEFT JOIN admission_stats ast ON (bs.ward_id = ast.ward_id)
            )
        """ % (self._table,)
        self.env.cr.execute(query)
