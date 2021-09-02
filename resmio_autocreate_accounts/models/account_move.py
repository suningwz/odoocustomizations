from odoo import api, fields, models, _

class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        if not soft:
            for move in self:
                if not move.partner_id:
                    # a later check in super() will take care of these and throw an error
                    continue
                if move.is_sale_document() and (not move.partner_id.property_account_receivable_id or move.partner_id.property_account_receivable_id.id == self.env['ir.property']._get('property_account_receivable_id', 'res.partner').id):
                    move.partner_id.property_account_receivable_id = self.env['account.account'].create_receivable(
                        {'name': move.partner_id.name})
                    move._onchange_partner_id()

                elif move.is_purchase_document() and (not move.partner_id.property_account_payable_id or move.partner_id.property_account_payable_id.id == self.env['ir.property']._get('property_account_payable_id', 'res.partner').id):
                    move.partner_id.property_account_payable_id = self.env['account.account'].create_payable(
                        {'name': move.partner_id.name})
                    move._onchange_partner_id()

        super(AccountMove, self)._post(soft=soft)