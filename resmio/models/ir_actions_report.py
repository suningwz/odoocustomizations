import base64
from odoo import models, fields, api, _


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def resmio_render_pdf(self, res_ids, data=None):
        return_value = super(IrActionsReport, self)._render(res_ids, data)
        return base64.b64encode(return_value[0])