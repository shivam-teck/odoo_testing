from odoo import models


class Http(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        IrConfigSudo = self.env["ir.config_parameter"].sudo()
        session_info = super().session_info()
        session_info.update({"access_control": IrConfigSudo.get_access_control()})
        return session_info
