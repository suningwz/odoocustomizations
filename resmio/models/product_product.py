from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    product_identifier = fields.Char('Product Identifier')