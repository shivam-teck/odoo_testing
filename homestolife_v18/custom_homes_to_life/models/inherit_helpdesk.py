from odoo import models, api, fields, _


class InheritHelpdesk(models.Model):
    _inherit = 'helpdesk.ticket'

    order_id = fields.Many2one('sale.order', domain="[('partner_id', '=', partner_id)]")
    product_ids = fields.Many2many('product.product', compute='compute_product_ids')
    product_id = fields.Many2one('product.product', domain="[('id', 'in', product_ids)]", )
    company_name = fields.Char('Company Name')
    closer_date = fields.Date('Closer Date')
    mc = fields.Char('MC')
    remark1 = fields.Char('Remark1')
    remark2 = fields.Char('Remark2')
    oc_no = fields.Char('OC Number',related='order_id.oc_no', store=True)
    order_line_ids = fields.One2many('sale.order.line', 'help_desk_id', related='order_id.order_line', readonly=True)


    business_format = fields.Selection([
        ('htl_coco', 'HomesToLife COCO'),
        ('htl_fofo', 'HomesToLife FOFO'),
        ('htl_brands', 'HomesToLife Brands')
    ])
    # customer_name = fields.Char('Customer Name')
    order_number = fields.Char('Order Number')
    article_description = fields.Char('Article Description')

    disposition = fields.Selection([('damage_material_delivered', 'Damage Material Delivered'),
                                    ('assembly_request', 'Assembly Request'),
                                    ('delayed_delivery', 'Delayed Delivery'),
                                    ('technical_issue', 'Technical Issue'),
                                    ('early_delivery_request', 'Early Delivery Request'),
                                    ('manufacturing_defect', 'Manufacturing Defect'),
                                    ('behavior_issue', 'Behavior Issue')
                                    ])

    @api.depends('order_id')
    def compute_product_ids(self):
        for rec in self:
            if rec.order_id:
                product_list = []
                for i in rec.order_id.order_line:
                    product_list.append(i.product_id.id)
                rec.product_ids = [(6, 0, product_list)]
            else:
                rec.product_ids = False
