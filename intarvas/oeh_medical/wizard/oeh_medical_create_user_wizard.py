# -*- coding: utf-8 -*-
##############################################################################
#    Copyright (C) 2015 - Present, intarvas (<https://www.intarvas.in>). All Rights Reserved
#    intarvas, Hospital Management Solutions

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class OehMedicalCreateUserWizardLine(models.TransientModel):
    _name = 'oeh.medical.create.user.wizard.line'
    _description = 'Duplicate User Line'

    wizard_id = fields.Many2one('oeh.medical.create.user.wizard', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', string='User', required=True)
    name = fields.Char(related='user_id.name', readonly=True)
    login = fields.Char(related='user_id.login', readonly=True)
    phone = fields.Char(related='user_id.phone', readonly=True)
    company_id = fields.Many2one(related='user_id.company_id', readonly=True)
    selected = fields.Boolean(string='Select')


class OehMedicalCreateUserWizard(models.TransientModel):
    _name = 'oeh.medical.create.user.wizard'
    _description = 'Create User Account Wizard'

    physician_id = fields.Many2one('oeh.medical.physician', string='Physician', required=True, readonly=True)

    duplicate_line_ids = fields.One2many(
        'oeh.medical.create.user.wizard.line',
        'wizard_id',
        string='Duplicate Accounts'
    )

    action_type = fields.Selection([
        ('link', 'Link to Existing User'),
        ('create', 'Create New User')
    ], string='Action', default='link', required=True)

    @api.onchange('duplicate_line_ids')
    def _onchange_duplicate_lines(self):
        """Ensure only one user is selected"""
        selected_lines = self.duplicate_line_ids.filtered('selected')
        if len(selected_lines) > 1:
            # Uncheck all except the last one
            for line in selected_lines[:-1]:
                line.selected = False

    def action_confirm(self):
        """Confirm the action - either link or create"""
        self.ensure_one()

        if self.action_type == 'link':
            selected_line = self.duplicate_line_ids.filtered('selected')
            if not selected_line:
                raise UserError(_('Please select a user account to link with.'))
            # Link existing user
            self.physician_id.write({'oeh_user_id': selected_line[0].user_id.id})
        else:
            # Create new user
            new_user = self.physician_id._create_user_account()

        return {'type': 'ir.actions.act_window_close'}