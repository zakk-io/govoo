import odoo
import odoo.tools.config as config
config.parse_config(['--db_host=db', '--db_port=5432', '--db_user=odoo', '--db_password=odoo'])
from odoo.modules import db as db_module
dbnames = db_module.exp_list(config.get_config())
print('Available databases:', dbnames)
