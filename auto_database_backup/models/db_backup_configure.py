# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import boto3
import dropbox
import errno
import ftplib
import json
import logging
import nextcloud_client
import os
import paramiko
import requests
import shutil
import subprocess
import tempfile
import odoo
from datetime import timedelta
from nextcloud import NextCloud
from requests.auth import HTTPBasicAuth
from werkzeug import urls
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import find_pg_tool, exec_pg_environ
from odoo.http import request
from odoo.service import db

_logger = logging.getLogger(__name__)

class DbBackupConfigure(models.Model):
    """DbBackupConfigure class provides an interface to manage database
       backups of Local Server, Remote Server, Google Drive, Dropbox, Onedrive,
       Nextcloud and Amazon S3"""
    _name = 'db.backup.configure'
    _description = 'Automatic Database Backup'

    name = fields.Char(string='Name', required=True, help='Add the name')
    db_name = fields.Char(string='Database Name', required=True,
                          help='Name of the database')
    master_pwd = fields.Char(string='Master Password', required=True,
                             help='Master password')
    backup_format = fields.Selection([
        ('zip', 'Zip'),
        ('dump', 'Dump')
    ], string='Backup Format', default='zip', required=True,
        help='Format of the backup')
    backup_destination = fields.Selection([
        ('local', 'Local Storage'),
    ], string='Backup Destination', help='Destination of the backup')
    backup_frequency = fields.Selection([
        ('daily', 'Daily'),
    ], default='daily', string='Backup Frequency', help='Frequency of Backup Scheduling')
    backup_path = fields.Char(string='Backup Path',
                              help='Local storage directory path')
    active = fields.Boolean(default=False, string='Active',
                            help='Activate the Scheduled Action or not')
    hide_active = fields.Boolean(string="Hide Active",
                                 help="Make active field to readonly")
    auto_remove = fields.Boolean(string='Remove Old Backups',
                                 help='Remove old backups')
    days_to_remove = fields.Integer(string='Remove After',
                                    help='Automatically delete stored backups'
                                         ' after this specified number of days')

    backup_filename = fields.Char(string='Backup Filename',
                                  help='For Storing generated backup filename')
    generated_exception = fields.Char(string='Exception',
                                      help='Exception Encountered while Backup'
                                           'generation')


    @api.constrains('db_name')
    def _check_db_credentials(self):
        """Validate entered database name and master password"""
        database_list = db.list_dbs(force=True)
        if self.db_name not in database_list:
            raise ValidationError(_("Invalid Database Name!"))
        try:
            odoo.service.db.check_super(self.master_pwd)
        except Exception:
            raise ValidationError(_("Invalid Master Password!"))

    @api.onchange('backup_destination')
    def _onchange_back_up_local(self):
        """
        On change handler for the 'backup_destination' field. This method is
        triggered when the value of 'backup_destination' is changed. If the
        chosen backup destination is 'local', it sets the 'hide_active' field
        to True which make active field to readonly to False.
         """
        if self.backup_destination == 'local':
            self.hide_active = True

    def schedule_auto_backup(self):
        """Function for generating and storing backup.
           Database backup for all the active records in backup configuration
           model will be created."""
        for rec in self:
            backup_time = fields.datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
            backup_filename = f"{rec.db_name}_{backup_time}.{rec.backup_format}"
            rec.backup_filename = backup_filename
            # Local backup
            if rec.backup_destination == 'local':
                try:
                    if not os.path.isdir(rec.backup_path):
                        os.makedirs(rec.backup_path)
                    backup_file = os.path.join(rec.backup_path,
                                               backup_filename)
                    f = open(backup_file, "wb")
                    self.dump_data(rec.db_name, f, rec.backup_format)
                    f.close()
                    # Remove older backups
                    if rec.auto_remove:
                        for filename in os.listdir(rec.backup_path):
                            file = os.path.join(rec.backup_path, filename)
                            create_time = fields.datetime.fromtimestamp(
                                os.path.getctime(file))
                            backup_duration = fields.datetime.utcnow() - create_time
                            if backup_duration.days >= rec.days_to_remove:
                                os.remove(file)

                except Exception as e:
                    rec.generated_exception = e
                    _logger.info('FTP Exception: %s', e)

    def dump_data(self, db_name, stream, backup_format):
        """Dump database `db` into file-like object `stream` if stream is None
        return a file object with the dump. """
        _logger.info('DUMP DB: %s format %s', db_name, backup_format)
        cmd = [find_pg_tool('pg_dump'), '--no-owner', db_name]
        env = exec_pg_environ()
        if backup_format == 'zip':
            with tempfile.TemporaryDirectory() as dump_dir:
                filestore = odoo.tools.config.filestore(db_name)
                cmd.insert(-1,'--file=' + os.path.join(dump_dir, 'dump.sql'))
                subprocess.run(cmd, env=env, stdout=subprocess.DEVNULL,
                               stderr=subprocess.STDOUT, check=True)
                if os.path.exists(filestore):
                    shutil.copytree(filestore,
                                    os.path.join(dump_dir, 'filestore'))
                with open(os.path.join(dump_dir, 'manifest.json'), 'w') as fh:
                    db = odoo.sql_db.db_connect(db_name)
                    with db.cursor() as cr:
                        json.dump(self._dump_db_manifest(cr), fh, indent=4)
                if stream:
                    odoo.tools.osutil.zip_dir(dump_dir, stream,
                                              include_dir=False,
                                              fnct_sort=lambda
                                                  file_name: file_name != 'dump.sql')
                else:
                    t = tempfile.TemporaryFile()
                    odoo.tools.osutil.zip_dir(dump_dir, t, include_dir=False,
                                              fnct_sort=lambda
                                                  file_name: file_name != 'dump.sql')
                    t.seek(0)
                    return t
        else:
            cmd.insert(-1,'--format=c')
            process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
            stdout, _ = process.communicate()
            if stream:
                stream.write(stdout)
            else:
                return stdout

    def _dump_db_manifest(self, cr):
        """ This function generates a manifest dictionary for database dump."""
        pg_version = "%d.%d" % divmod(cr._obj.connection.server_version / 100, 100)
        cr.execute(
            "SELECT name, latest_version FROM ir_module_module WHERE state = 'installed'")
        modules = dict(cr.fetchall())
        manifest = {
            'odoo_dump': '1',
            'db_name': cr.dbname,
            'version': odoo.release.version,
            'version_info': odoo.release.version_info,
            'major_version': odoo.release.major_version,
            'pg_version': pg_version,
            'modules': modules,
        }
        return manifest
