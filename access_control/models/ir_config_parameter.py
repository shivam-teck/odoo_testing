from odoo import api, models


class IrConfigParameter(models.Model):
    _inherit = "ir.config_parameter"

    @api.model
    def get_access_control(self):
        opts = [
            "access_control.create",
            "access_control.create_edit",
            "access_control.search_more",
            "access_control.m2o_dialog",
            "access_control.field_limit_entries",
        ]
        values = self.sudo().search_read([["key", "in", opts]], ["key", "value"])
        return {res["key"]: res["value"] for res in values}
