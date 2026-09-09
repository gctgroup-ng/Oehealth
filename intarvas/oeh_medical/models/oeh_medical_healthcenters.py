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

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools.translate import _
from odoo.osv import expression

_logger = logging.getLogger(__name__)


# Health Center Management
class intarvasCenters(models.Model):
    _name = 'oeh.medical.health.center'
    _description = "Information about the health centers"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {
        'res.partner': 'partner_id',
    }

    HEALTH_CENTERS = [
        ('Hospital', 'Hospital'),
        ('Multi-speciality Hospital', 'Multi-speciality Hospital'),
        ('Nursing Home', 'Nursing Home'),
        ('Clinic', 'Clinic'),
        ('Community Health Center', 'Community Health Center'),
        ('Military Medical Facility', 'Military Medical Facility'),
        ('Other', 'Other'),
    ]

    def _building_count(self):
        for hec in self:
            hec.building_count = self.env['oeh.medical.health.center.building'].sudo().search_count([('institution', '=', hec.id)])

    def _pharmacy_count(self):
        for hec in self:
            hec.pharmacy_count = self.env['oeh.medical.health.center.pharmacy'].sudo().search_count([('institution', '=', hec.id)])

    partner_id = fields.Many2one('res.partner', string='Related Partner', required=True,ondelete='cascade', help='Partner-related data of the hospitals')
    health_center_type = fields.Selection(HEALTH_CENTERS, string='Type', help="Health center type", index=True)
    info = fields.Text('Extra Information')
    building_count = fields.Integer(compute=_building_count, string="Buildings")
    pharmacy_count = fields.Integer(compute=_pharmacy_count, string="Pharmacies")

    # One2many relationships for health center components
    building_ids = fields.One2many('oeh.medical.health.center.building', 'institution', string='Buildings')
    ward_ids = fields.One2many('oeh.medical.health.center.ward', 'institution', string='Wards')
    bed_ids = fields.One2many('oeh.medical.health.center.beds', 'institution', string='Accommodations')

    def create(self, vals_list):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        for vals in vals_list:
            vals["is_institution"] = True
            vals["is_company"] = True

        health_center = super(intarvasCenters, self).create(vals_list)
        return health_center

    @api.onchange('state_id')
    def onchange_state(self):
        if self.state_id:
            self.country_id = self.state_id.country_id.id


# Health Center Building
class intarvasCentersBuilding(models.Model):
    _name = 'oeh.medical.health.center.building'
    _description = "Health Centers buildings"

    def _ward_count(self):
        oe_wards = self.env['oeh.medical.health.center.ward']
        for building in self:
            domain = [('building', '=', building.id)]
            wards_ids = oe_wards.search(domain)
            wards = oe_wards.browse(wards_ids)
            wa_count = 0
            for war in wards:
                wa_count+=1
            building.ward_count = wa_count
        return True

    def _bed_count(self):
        oe_beds = self.env['oeh.medical.health.center.beds']
        for building in self:
            domain = [('building', '=', building.id)]
            beds_ids = oe_beds.search(domain)
            beds = oe_beds.browse(beds_ids)
            be_count = 0
            for bed in beds:
                be_count+=1
            building.bed_count = be_count
        return True

    name = fields.Char(string='Name', size=128, required=True, help="Name of the building within the institution")
    institution = fields.Many2one('oeh.medical.health.center', string='Health Center', required=True)
    code = fields.Char (string='Code', size=64)
    info = fields.Text (string='Extra Info')
    ward_count = fields.Integer(compute=_ward_count, string="Wards")
    bed_count = fields.Integer(compute=_bed_count, string="Beds")

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The building name must be unique !')
    ]

    def name_get(self):
        return [(building.id, '%s (%s)' % (building.name, building.institution.name)) for building in self]


# Health Center Wards Management
class intarvasCentersWards(models.Model):
    _name = "oeh.medical.health.center.ward"
    _description = "Health Center Wards Management"

    GENDER = [
        ('Men Ward','Men Ward'),
        ('Women Ward','Women Ward'),
        ('Unisex','Unisex'),
    ]

    WARD_STATES = [
        ('Beds Available','Beds Available'),
        ('Full','Full'),
    ]

    def _bed_count(self):
        oe_beds = self.env['oeh.medical.health.center.beds']
        for ward in self:
            domain = [('ward', '=', ward.id)]
            beds_ids = oe_beds.search(domain)
            beds = oe_beds.browse(beds_ids)
            be_count = 0
            for bed in beds:
                be_count+=1
            ward.bed_count = be_count
        return True

    name = fields.Char(string='Name', size=128, required=True, help="Ward / Room code")
    institution = fields.Many2one('oeh.medical.health.center',string='Health Center', required=True)
    building = fields.Many2one('oeh.medical.health.center.building',string='Building', required=True)
    floor = fields.Integer(string='Floor Number')
    private = fields.Boolean(string='Private Room',help="Check this option for private room")
    bio_hazard = fields.Boolean(string='Bio Hazard',help="Check this option if there is biological hazard")
    telephone = fields.Boolean(string='Telephone access')
    ac = fields.Boolean(string='Air Conditioning')
    private_bathroom = fields.Boolean(string='Private Bathroom')
    guest_sofa = fields.Boolean(string='Guest sofa-bed')
    tv = fields.Boolean(string='Television')
    internet = fields.Boolean(string='Internet Access')
    refrigerator = fields.Boolean(string='Refrigerator')
    microwave = fields.Boolean(string='Microwave')
    gender = fields.Selection(GENDER,string='Gender',default=lambda *a: 'Unisex')
    state = fields.Selection(WARD_STATES,string='Status',default='Beds Available')
    info = fields.Text('Extra Info')
    bed_count = fields.Integer(compute=_bed_count, string="Beds")

    # ICU Fields
    is_icu = fields.Boolean(string='Is ICU Unit', default=False)
    icu_type = fields.Selection([
        ('general_icu', 'General ICU'),
        ('cardiac_icu', 'Cardiac ICU'),
        ('neuro_icu', 'Neuro ICU'),
        ('pediatric_icu', 'Pediatric ICU')
    ], string='ICU Type')

    _sql_constraints = [
        ('name_ward_uniq', 'unique (name,building)', 'The ward name is already configured in selected building !')
    ]

    def name_get(self):
        return [(ward.id, '%s (%s)' % (ward.name, ward.building.name)) for ward in self]


# Beds Management
class intarvasCentersBeds(models.Model):

    BED_TYPES = [
        ('Gatch Bed', 'Gatch Bed'),
        ('Electric', 'Electric'),
        ('Stretcher', 'Stretcher'),
        ('Low Bed', 'Low Bed'),
        ('Low Air Loss', 'Low Air Loss'),
        ('Circo Electric', 'Circo Electric'),
        ('Clinitron', 'Clinitron'),
    ]

    BED_STATES = [
        ('Free', 'Free'),
        ('Reserved', 'Reserved'),
        ('Occupied', 'Occupied'),
        ('Not Available', 'Not Available'),
    ]

    CHANGE_BED_STATUS = [
        ('Mark as Available', 'Mark as Available'),
        ('Mark as Reserved', 'Mark as Reserved'),
        ('Mark as Not Available', 'Mark as Not Available'),
    ]
    _name = 'oeh.medical.health.center.beds'
    _description = "Accommodation Management"
    _inherits = {
        'product.product': 'product_id',
    }

    ACCOMMODATION_TYPE = [
        ('bed', 'Bed'),
        ('room', 'Room')
    ]

    product_id = fields.Many2one('product.product', string='Related Product', required=True, ondelete='cascade', help='Product-related data of the hospital beds')
    institution = fields.Many2one('oeh.medical.health.center', string='Health Center')
    building = fields.Many2one('oeh.medical.health.center.building', string='Building')
    ward = fields.Many2one('oeh.medical.health.center.ward', 'Ward', domain="[('building', '=', building)]", help="Ward or room", ondelete='cascade')
    bed_type = fields.Selection(BED_TYPES,string='Bed Type', required=True, default=lambda *a: 'Gatch Bed')
    telephone_number = fields.Char(string='Telephone Number', size=128, help="Telephone Number / Extension")
    info = fields.Text(string='Extra Info')
    state = fields.Selection(BED_STATES, string='Status', default='Free')
    change_bed_status = fields.Selection(CHANGE_BED_STATUS, string='Change Bed Status')
    accommodation_type = fields.Selection(ACCOMMODATION_TYPE, string='Accommodation Type', default='bed')

    # ICU Fields
    is_icu_bed = fields.Boolean(string='Is ICU Bed', default=False)
    icu_bed_type = fields.Selection([
        ('standard_icu', 'Standard ICU'),
        ('isolation_icu', 'Isolation ICU'),
        ('critical_care', 'Critical Care')
    ], string='ICU Bed Type')

    def name_get(self):
        return [(bed.id, '%s (%s)' % (bed.name, bed.ward.name)) for bed in self]

    # Preventing deletion of a beds which is not in draft state
    def unlink(self):
        for accommodation in self.filtered(lambda beds: beds.state not in ['Free', 'Not Available']):
            raise UserError(_('You can not delete accommodation(s) which is in "Reserved" or "Occupied" state !!'))
        return super(intarvasCentersBeds, self).unlink()

    def create(self, vals_list):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        for vals in vals_list:
            if vals.get('name') and vals.get('ward'):
                # lang = self.env.user.lang or 'en_US'
                query_bed = _("select count(*) from oeh_medical_health_center_beds oeb, product_product pr, product_template pt where pr.id=oeb.product_id and pr.product_tmpl_id=pt.id and pt.name->>'en_US'='%s' and oeb.ward=%s")%(str(vals.get('name')), str(vals.get('ward')))
                self.env.cr.execute(query_bed)
                val = self.env.cr.fetchone()
                if val and int(val[0]) > 0:
                   raise UserError(_('The same accommodation is already configured in selected ward !'))
            vals["is_bed"] = True
            if self.env.ref('uom.product_uom_day'):
                vals["uom_id"] = self.env.ref('uom.product_uom_day').id

        beds = super(intarvasCentersBeds, self).create(vals_list)
        return beds

