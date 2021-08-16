from mcdreforged.api.all import *

QBM_PID = 'quick_backup_multi'
PREFIX = '!!tqb'

TRIGGER_BACKUP_EVENT 	= LiteralEvent('{}.trigger_backup'.format(QBM_PID))  # <- source, comment
BACKUP_DONE_EVENT 		= LiteralEvent('{}.backup_done'.format(QBM_PID))  # -> source, slot_info
