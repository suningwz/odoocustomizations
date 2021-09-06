import requests
from odoo import api, exceptions, fields, models, _
from requests.auth import HTTPBasicAuth


class AccountMove(models.Model):
    _inherit = "account.move"

    def _api_creds(self):

        resmio_url = self.env['ir.config_parameter'].sudo().get_param('resmio.resmio_url')
        resmio_basic_auth_password = self.env['ir.config_parameter'].sudo().get_param('resmio.resmio_basic_auth_password')

        if not resmio_basic_auth_password:
            raise exceptions.ValidationError('No resmio basic auth password configured. Please configure it in "General Settings > resmio Customizations".')

        if not resmio_url:
            raise exceptions.ValidationError('No resmio url configured. Please configure it in "General Settings > resmio Customizations".')

        return resmio_url, resmio_basic_auth_password

    def _api_update_invoice(self, invoice_id, state, number, date, amount_untaxed, amount_total, payment_status):

        resmio_url, resmio_basic_auth_password = self._api_creds()

        headers = {
            'Content-Type': 'application/json',
        }
        data = {
            'odoo_account_move_id': invoice_id,
            'state': state,
            'number': number,
            'date': date,
            'amount_untaxed': amount_untaxed,
            'amount_total': amount_total,
            'payment_status': payment_status,
        }
        path = '/odoo/invoice/'
        r = requests.put(resmio_url + path, headers=headers, data=json.dumps(data), timeout=self.TIMEOUT, auth=HTTPBasicAuth('odoo', resmio_basic_auth_password))
        r.raise_for_status()

        return r.json()



    def _post(self, soft=True):
        res = super(AccountMove, self)._post(soft=soft)
        if not soft:
            for invoice in self:
                self._api_update_invoice(
                    invoice_id=invoice.id,
                    state=invoice.state,
                    number=invoice.name,
                    date=str(invoice.invoice_date),
                    amount_untaxed=float("{:.2f}".format(invoice.amount_untaxed)),
                    amount_total=float("{:.2f}".format(invoice.amount_total)),
                    payment_status=invoice.payment_state,
                )

        return res