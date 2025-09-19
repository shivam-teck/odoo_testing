from odoo import fields, models
from odoo.addons.base.models.ir_ui_menu import MENU_ITEM_SEPARATOR


class CustomResGroups(models.Model):
    _inherit = 'res.groups'
    description = 'Easily restrict or hide specific menu items for individual users'

    hide_menu_ids = fields.Many2many('ir.ui.menu', string="Hidden Menu")
    is_admin = fields.Boolean(compute='_get_is_admin', string="Is Admin")

    def write(self, vals):
        res = super(CustomResGroups, self).write(vals)
        updated_menus = self.mapped('hide_menu_ids')
        all_users = self.mapped('users')
        removed_menu = set()
        removed_users = set()

        if 'hide_menu_ids' in vals:
            for operation in vals['hide_menu_ids']:
                if len(operation) == 3 and operation[0] == 6:
                    menu_ids = operation[2]
                    removed_menu.update(menu_ids)
                elif len(operation) == 2 and operation[0] == 3:
                    removed_menu.add(operation[1])

        removed_menus = self.env['ir.ui.menu'].browse(removed_menu)

        for menu in removed_menus:
            menu_restrict_user_ids = []
            for user in all_users:
                menu_restrict_user_ids.append((3, user.id))
            menu.write({'restrict_user_ids': menu_restrict_user_ids})

        for menu in updated_menus:
            menu_restrict_user_ids = []
            for user in all_users:
                menu_restrict_user_ids.append((4, user.id))
            menu.write({'restrict_user_ids': menu_restrict_user_ids})

        if 'users' in vals:
            for operation in vals['users']:
                if len(operation) == 2 and operation[0] == 3:
                    removed_users.add(operation[1])

        if removed_users:
            for menu in updated_menus:
                menu_restrict_user_ids = []
                for user in removed_users:
                    menu_restrict_user_ids.append((3, user))
                menu.write({'restrict_user_ids': menu_restrict_user_ids})

        return res

    def _get_is_admin(self):
        for rec in self:
            rec.is_admin = rec.id == self.env.ref('base.group_system').id


class CustomIrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'
    description = 'Easily restrict or hide specific menu items for individual users'

    restrict_user_ids = fields.Many2many('res.users', string="Restricted Users")

    def _get_full_name(self, level=6):
        if level <= 0 or not self:
            return ""
        parent_name = self.parent_id._get_full_name(level - 1) if self.parent_id else ""
        return (parent_name + MENU_ITEM_SEPARATOR + self.name) if parent_name else self.name
