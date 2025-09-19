from odoo import models, api, fields, _


class MaterialMaster(models.Model):
    _name = 'material.master'
    _rec_name = 'material'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    material_group = fields.Selection([('leather', 'Leather'), ('fabric', 'Fabric'), ('pvc', 'PVC')],tracking=True)
    material = fields.Char(string="Material", tracking=True)
    material_description = fields.Text(string="Material Description",tracking=True)


class MaterialCode(models.Model):
    _name = 'material.code'
    _rec_name = 'material_code'

    material_code = fields.Char(string='Material Code', company_dependent=True)
    margin = fields.Float(string='Margin%', company_dependent=True)

    # _sql_constraints = [
    #     ('material_code_uniq', 'UNIQUE (material_code)',
    #      'You can not have two different Margin for same Material code !')]


    _sql_constraints = [
        ('material_code_uniq', 'UNIQUE (margin)', 'You can not have two different Margin for same Material code !')]
