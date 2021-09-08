import requests
import json
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

    def _api_update_invoice(self, invoice_id, state, number, move_type, date, amount_untaxed, amount_total, payment_state, commercial_partner_id, reversed_entry_id , lines):

        resmio_url, resmio_basic_auth_password = self._api_creds()

        headers = {
            'Content-Type': 'application/json',
        }
        data = {
            'odoo_account_move_id': invoice_id,
            'state': state,
            'number': number,
            'move_type': move_type,
            'date': date,
            'amount_untaxed': amount_untaxed,
            'amount_total': amount_total,
            'payment_state': payment_state,
            'commercial_partner_id': commercial_partner_id,
            'reversed_entry_id': reversed_entry_id,
            'lines': lines,
        }
        path = '/odoo/invoice/'
        r = requests.put(resmio_url + path, headers=headers, data=json.dumps(data), timeout=20.0, auth=HTTPBasicAuth('odoo', resmio_basic_auth_password))
        r.raise_for_status()

        return r.json()

    def _create_or_update_invoice_at_resmio(self, forced_state=None):
        for invoice in self:
            if invoice.state == 'draft':
                continue
            if invoice.move_type not in ['out_invoice', 'out_refund']:
                continue
            if not invoice.commercial_partner_id:
                continue
            try:
                lines = []
                for line in invoice.invoice_line_ids:
                    lines.append({
                        'name': line.name,
                        'amount_total': float("{:.2f}".format(line.price_total)),
                        'amount_untaxed': float("{:.2f}".format(line.price_subtotal)),
                        'product_identifier': line.product_id.product_tmpl_id.product_identifier if line.product_id and line.product_id.product_tmpl_id.product_identifier else None
                    })

                self._api_update_invoice(
                    invoice_id=invoice.id,
                    state=invoice.state,
                    number=invoice.name,
                    move_type=invoice.move_type,
                    date=str(invoice.invoice_date),
                    amount_untaxed=float("{:.2f}".format(invoice.amount_untaxed)),
                    amount_total=float("{:.2f}".format(invoice.amount_total)),
                    payment_state=invoice.payment_state,
                    commercial_partner_id=invoice.commercial_partner_id.id,
                    reversed_entry_id=invoice.reversed_entry_id.id if invoice.reversed_entry_id else None,
                    lines=lines,
                )
            except exceptions.ValidationError:
                continue

    def action_invoice_paid(self):
        res = super(AccountMove, self).action_invoice_paid()
        self._create_or_update_invoice_at_resmio(forced_state='paid')
        return res

    def write(self, vals):
        res = super(AccountMove, self).write(vals)

        self._create_or_update_invoice_at_resmio()

        return res