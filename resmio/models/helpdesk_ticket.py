from odoo import fields, models


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    salesforce_task_id = fields.Char('Salesforce Task ID', index=True)