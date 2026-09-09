# -*- coding: utf-8 -*-

from odoo import models, fields, api


class intarvasLabTestTemplate(models.Model):
    _name = 'oeh.medical.lab.test.template'
    _description = "Lab Test Template"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Template Name', required=True, tracking=True,
                       help="Name of the lab test template")
    description = fields.Text(string='Description',
                             help="Description of the lab test template")
    active = fields.Boolean(string='Active', default=True, tracking=True,
                           help="Set to false to hide the template without removing it")
    lab_test_line_ids = fields.One2many('oeh.medical.lab.test.template.line', 'template_id',
                                       string='Lab Test Lines')

    def apply_template_to_appointment(self, appointment_id):
        """Apply this template to an appointment"""
        appointment = self.env['oeh.medical.appointment'].browse(appointment_id)
        if appointment:
            # Clear existing lab test lines
            appointment.lab_test_ids.unlink()
            # Create new lab test lines based on template
            for line in self.lab_test_line_ids:
                self.env['oeh.medical.lab.test'].create({
                    'test_type_id': line.test_type_id.id,
                    'urgency': line.urgency,
                    'info': line.info,
                    'appointment': appointment_id,
                    'patient': appointment.patient.id,
                })


class intarvasLabTestTemplateLine(models.Model):
    _name = 'oeh.medical.lab.test.template.line'
    _description = "Lab Test Template Line"
    _rec_name = 'test_type_id'

    template_id = fields.Many2one('oeh.medical.lab.test.template', string='Template',
                                 required=True, ondelete='cascade')
    test_type_id = fields.Many2one('oeh.medical.labtest.types', string='Lab Test Type',
                                  required=True, help="Type of lab test to be performed")
    urgency = fields.Selection([
        ('a', 'Normal'),
        ('b', 'Urgent'),
        ('c', 'Very Urgent')
    ], string='Urgency', default='a', help="Priority level of the test")
    info = fields.Text(string='Additional Information',
                      help="Additional information about the test")