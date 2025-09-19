from odoo import api, fields, models, _
from datetime import datetime, timedelta
from datetime import date


class Walking(models.Model):
    _name = 'walking.walking'
    _rec_name = 'walking_date'

    walking_count = fields.Integer(required=True)
    walking_date = fields.Date(default=date.today(), required=True)
    google_rating = fields.Integer()
    instagram_followers = fields.Integer()

    _sql_constraints = [
        ('phone_uniq', 'UNIQUE (walking_date)', 'You can not have same Date!')]
