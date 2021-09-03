from odoo import api, fields, models
from odoo.exceptions import AccessDenied


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    resmio_url = fields.Char('resmio URL')
    resmio_basic_auth_password = fields.Char('resmio basic auth password')


    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(
            resmio_url=get_param('resmio.resmio_url'),
            resmio_basic_auth_password=get_param('resmio.resmio_basic_auth_password'),
        )
        return res

    def set_values(self):
        if not self.env.is_admin():
            raise AccessDenied()
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param("resmio.resmio_url", self.resmio_url)
        ICPSudo.set_param("resmio.resmio_basic_auth_password", self.resmio_basic_auth_password)