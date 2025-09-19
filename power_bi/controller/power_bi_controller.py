from odoo import http
from odoo.http import request
import ast
from jinja2 import Environment, FileSystemLoader
import os


# Renderer class
class PowerBiRenderer:
    def __init__(self, template_path, template_file):
        self.env = Environment(loader=FileSystemLoader(os.path.abspath(template_path)))
        self.template_file = template_file

    def render(self, **context):
        template = self.env.get_template(self.template_file)
        return template.render(**context)


class PowerBiController(http.Controller):

    # Helper: Prepare table data
    def _prepare_table_data(self, model_rec):
        domain = []
        if model_rec.filter:
            try:
                domain = ast.literal_eval(model_rec.filter)
            except Exception:
                return [], []

        Model = request.env[model_rec.model_id.model]
        # ✅ Removed the limit to fetch ALL records
        records = Model.search(domain)

        def get_value(record, field_expr):
            try:
                value = record
                for attr in field_expr.split('.'):
                    value = getattr(value, attr, False)
                    if value is False or value is None:
                        return ''
                if hasattr(value, '__iter__') and not isinstance(value, str):
                    return ', '.join([str(v) for v in value])
                return str(value)
            except Exception:
                return ''

        table_data = [
            {fm.display_name: get_value(rec, fm.field_name) for fm in model_rec.field_mapping_ids}
            for rec in records
        ]
        columns = [fm.display_name for fm in model_rec.field_mapping_ids]
        return columns, table_data

    # HTML rendering
    def _render_template(self, model_rec):
        module_path = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.abspath(os.path.join(module_path, '..', 'templates'))
        template_file = 'power_bi_table_template.html'

        renderer = PowerBiRenderer(template_path, template_file)
        columns, table_data = self._prepare_table_data(model_rec)
        user_name = request.env.user.name
        return renderer.render(
            model_name=model_rec.name,
            columns=columns,
            table_data=table_data,
            user_name=user_name
        )

    # Route for HTML view
    @http.route('/power_bi/view/<int:model_id>', type='http', auth='user', website=True)
    def view_html(self, model_id, **kwargs):
        model_rec = request.env['power.bi.model'].browse(model_id)
        if not model_rec.exists():
            return "Model not found!"
        return self._render_template(model_rec)

    # Route for Power BI (JSON)
    @http.route('/power_bi/data/<int:model_id>', type='json', auth='user')
    def view_json(self, model_id, **kwargs):
        model_rec = request.env['power.bi.model'].browse(model_id)
        if not model_rec.exists():
            return {"error": "Model not found!"}

        columns, table_data = self._prepare_table_data(model_rec)
        user_name = request.env.user.name
        return {
            "model_name": model_rec.name,
            "columns": columns,
            "table_data": table_data,
            "user_name": user_name
        }
