# Part of Odoo. See LICENSE file for full copyright and licensing details
from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    product_identifier = fields.Char('Product Identifier')