from odoo import api, fields, models
from odoo.exceptions import AccessDenied


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    resmio_salesforcemigration_postgres_host = fields.Char('Postgres Host')
    resmio_salesforcemigration_postgres_database = fields.Char('Postgres Database')
    resmio_salesforcemigration_postgres_user = fields.Char('Postgres User')
    resmio_salesforcemigration_postgres_password = fields.Char('Postgres Password')


    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(
            resmio_salesforcemigration_postgres_host=get_param('resmio_salesforcemigration.resmio_salesforcemigration_postgres_host'),
            resmio_salesforcemigration_postgres_database=get_param('resmio_salesforcemigration.resmio_salesforcemigration_postgres_database'),
            resmio_salesforcemigration_postgres_user=get_param('resmio_salesforcemigration.resmio_salesforcemigration_postgres_user'),
            resmio_salesforcemigration_postgres_password=get_param('resmio_salesforcemigration.resmio_salesforcemigration_postgres_password'),
        )
        return res

    def set_values(self):
        if not self.env.is_admin():
            raise AccessDenied()
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param("resmio_salesforcemigration.resmio_salesforcemigration_postgres_host", self.resmio_salesforcemigration_postgres_host)
        ICPSudo.set_param("resmio_salesforcemigration.resmio_salesforcemigration_postgres_database", self.resmio_salesforcemigration_postgres_database)
        ICPSudo.set_param("resmio_salesforcemigration.resmio_salesforcemigration_postgres_user", self.resmio_salesforcemigration_postgres_user)
        ICPSudo.set_param("resmio_salesforcemigration.resmio_salesforcemigration_postgres_password", self.resmio_salesforcemigration_postgres_password)