
from odoo import api, fields, models, _

class CrmLead(models.Model):
    _inherit = "crm.lead"

    salesforce_lead_id = fields.Char('Salesforce Lead ID', index=True)
    cmp_source = fields.Char('CMP Source')
    cmp_medium = fields.Char('CMP Medium')
    cmp_name = fields.Char('CMP Name')
    cmp_term = fields.Char('CMP Term')
    cmp_content = fields.Char('CMP Content')
    cmp_campaign = fields.Char('CMP Campaign')
    gclid = fields.Char('GCLID')
    facebookpage = fields.Char('Facebook Page')

