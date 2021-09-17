from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    facility_id = fields.Char('Facility ID')
    salesforce_account_id = fields.Char('Salesforce Account ID', index=True)
    salesforce_contact_id = fields.Char('Salesforce Contact ID', index=True)
    enabled = fields.Boolean('Enabled')
    verified = fields.Boolean('Verified')
    in_partner_network = fields.Boolean('In partner network')
    bitburger_customer_number = fields.Char('Bitburger customer number')
    valid_payment_information = fields.Boolean('Valid payment information')
    cmp_source = fields.Char('CMP Source')
    cmp_medium = fields.Char('CMP Medium')
    cmp_name = fields.Char('CMP Name')
    cmp_term = fields.Char('CMP Term')
    cmp_content = fields.Char('CMP Content')
    cmp_campaign = fields.Char('CMP Campaign')
    gclid = fields.Char('GCLID')
    facebookpage = fields.Char('Facebook Page')
    businesspartner = fields.Char('Business Partner')