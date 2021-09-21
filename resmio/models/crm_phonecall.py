
from odoo import api, fields, models, _

class CrmPhonecall(models.Model):
    _inherit = "crm.phonecall"

    salesforce_task_id = fields.Char('Salesforce Task ID', index=True)