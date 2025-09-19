import numpy as np
from odoo import models, api, fields, _
import pandas as pd
import pysftp
from pathlib import Path
import os
from odoo.exceptions import UserError, ValidationError
from datetime import date
import datetime as DT
import ftplib


# from ftplib import FTP


class SaleOrderFtp(models.TransientModel):
    _name = 'sale.order.ftp.wizard'
    _description = 'Send Orders to SAP using ftp'

    def send_so(self):
        pass




