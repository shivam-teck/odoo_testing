from odoo import fields, models
from odoo.addons.base.models.ir_ui_menu import MENU_ITEM_SEPARATOR


class CustomResUsers(models.Model):
    _inherit = 'res.users'
    description = 'Easily restrict or hide specific menu items for individual users'

    hide_menu_ids = fields.Many2many(
        'ir.ui.menu', string="Hidden Menu")
    is_admin = fields.Boolean(compute='_get_is_admin', string="Is Admin")

    def write(self, vals):
        res = super(CustomResUsers, self).write(vals)
        for record in self:
            if 'hide_menu_ids' in vals:
                all_menus = record.hide_menu_ids
                if not all_menus:
                    menus_to_update = record.env['ir.ui.menu'].search([('restrict_user_ids', '=', record.id)])
                    menus_to_update.write({
                        'restrict_user_ids': [(3, record.id)]
                    })
                else:
                    for menu in all_menus:
                        if menu.id:
                            menu.write({
                                'restrict_user_ids': [(4, record.id)]
                            })
        return res

    def _get_is_admin(self):
        for rec in self:
            rec.is_admin = False
            if rec.id == self.env.ref('base.user_admin').id:
                rec.is_admin = True


class CustomIrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'
    description = 'Easily restrict or hide specific menu items for individual users'

    restrict_user_ids = fields.Many2many(
        'res.users', string="Restricted Users")

    def _get_full_name(self, level=6):
        if level <= 0 or not self:
            return ""

        parent_name = self.parent_id._get_full_name(level - 1) if self.parent_id else ""

        menu_name = self.name if self.name else ""

        return parent_name + MENU_ITEM_SEPARATOR + menu_name if parent_name else menu_name
