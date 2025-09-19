odoo.define('sh_pos_product_variant.ProductsWidget', function (require) {
    'use strict';

    const ProductsWidget = require("point_of_sale.ProductsWidget");
    const Registries = require("point_of_sale.Registries");

    const PosProductsWidget = (ProductsWidget) =>
        class extends ProductsWidget {
            get productsToDisplay() {
                var self = this;
                var res = super.productsToDisplay
                var products = []
                var tmpl_ids = []
                if (self.env.pos.config.sh_pos_enable_product_variants) {
                    _.each(res, function (each_product, i) {
                        if (self.env.pos.db.has_variant(each_product.product_tmpl_id)) {
                            if (!tmpl_ids.includes(each_product.product_tmpl_id)) {
                                products.push(each_product)
                                // each_product.display_name = each_product.name
                            }
                            tmpl_ids.push(each_product.product_tmpl_id)
                        } else {
                            products.push(each_product)
                        }

                    })
                    return products
                } else {
                    return res
                }
            }

        }

    Registries.Component.extend(ProductsWidget, PosProductsWidget);


});
