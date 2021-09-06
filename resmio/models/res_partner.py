# Part of Odoo. See LICENSE file for full copyright and licensing details
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    cmp_source = fields.Char('CMP Source')
    cmp_medium = fields.Char('CMP Medium')
    cmp_name = fields.Char('CMP Name')
    cmp_term = fields.Char('CMP Term')
    cmp_content = fields.Char('CMP Content')
    cmp_campaign = fields.Char('CMP Campaign')
    gclid = fields.Char('GCLID')
