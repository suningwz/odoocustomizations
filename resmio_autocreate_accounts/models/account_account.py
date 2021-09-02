from odoo import api, fields, models, _

class AccountAccount(models.Model):
    _inherit = "account.account"

    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create_receivable(self, vals_list):
        if not vals_list:
            return self.browse()
        account_type_rcv = self.env.ref('account.data_account_type_receivable')
        for vals in vals_list:
            vals['user_type_id'] = account_type_rcv.id
            vals['reconcile'] = True
            if 'code' not in vals:
                vals['code'] = self.env['ir.sequence'].next_by_code('receivable.account')

        return self.create(vals_list)

    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create_payable(self, vals_list):
        if not vals_list:
            return self.browse()
        account_type_rcv = self.env.ref('account.data_account_type_payable')
        for vals in vals_list:
            vals['user_type_id'] = account_type_rcv.id
            vals['reconcile'] = True
            if 'code' not in vals:
                vals['code'] = self.env['ir.sequence'].next_by_code('payable.account')

        return self.create(vals_list)
