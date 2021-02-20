import json
import os
import time
from threading import Thread, Event
from typing import Optional, Any

from mcdreforged.api.all import *

QBM_PID = 'quick_backup_multi'
PLUGIN_METADATA = {
	'id': 'timed_quick_backup_multi',
	'version': '1.0.0',
	'name': 'Timed QBM',
	'description': '一个QuickBackupM插件的扩展，用于定时触发QBM从而进行自动备份',
	'author': 'Fallen_Breath',
	'link': 'https://github.com/TISUnion/TimedQBM',
	'dependencies': {
		'mcdreforged': '>=1.2.0',
		QBM_PID: '>=1.1.0',
	}
}

PREFIX = '!!tqb'
HELP_MESSAGE = '''
-------- {1} v{2} -------
{3}
§7{0}§r 显示此条帮助信息
§7{0} enable§r 启动备份定时器
§7{0} disable§r 关闭备份定时器
§7{0} set_interval §6<minutes>§r 设置备份定时器时间间隔，单位分钟
§7{0} reset_timer§r 重置备份定时器
'''.strip().format(PREFIX, PLUGIN_METADATA['name'], PLUGIN_METADATA['version'], PLUGIN_METADATA['description'])

TRIGGER_BACKUP_EVENT 	= LiteralEvent('{}.trigger_backup'.format(QBM_PID))  # <- source, comment
BACKUP_DONE_EVENT 		= LiteralEvent('{}.backup_done'.format(QBM_PID))  # -> source, slot_info

config = {
	'enabled': True,
	'interval': 30.0,  # minutes
	'permission_requirement': 2
}
default_config = config.copy()
CONFIG_FILE = os.path.join('config', '{}.json'.format(PLUGIN_METADATA['id']))


class TimedQBMCommandSource(CommandSource):
	def __init__(self, server: ServerInterface):
		self.server = server

	@property
	def is_player(self):
		return False

	@property
	def is_console(self) -> bool:
		return False

	def get_permission_level(self) -> int:
		return PermissionLevel.CONSOLE_LEVEL

	def get_server(self) -> ServerInterface:
		return self.server

	def reply(self, message: Any, **kwargs) -> None:
		self.server.logger.info(str(message))

	def __str__(self):
		return self.__class__.__name__


class TimedQBM(Thread):
	def __init__(self, server: ServerInterface):
		super().__init__()
		self.setDaemon(True)
		self.setName(self.__class__.__name__)
		self.time_since_backup = time.time()
		self.server = server
		self.command_source = TimedQBMCommandSource(server)
		self.stop_event = Event()
		self.is_enabled = False

	@classmethod
	def get_backup_interval(cls):
		return config['interval'] * 60

	def broadcast(self, message):
		rtext = RTextList('[{}] '.format(PLUGIN_METADATA['name']), message)
		if self.server.is_server_startup():
			self.server.broadcast(rtext)
		else:
			self.server.logger.info(rtext)

	def set_enabled(self, value: bool):
		self.is_enabled = value
		self.reset_timer()

	def reset_timer(self):
		self.time_since_backup = time.time()

	def get_next_backup_message(self):
		return '下次自动备份时间: §3{}§r'.format(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(self.time_since_backup + self.get_backup_interval())))

	def broadcast_next_backup_time(self):
		self.broadcast(self.get_next_backup_message())

	def on_backup_created(self, slot_info: dict):
		self.broadcast('检测到新增的备份，重置定时器')
		self.reset_timer()
		self.broadcast_next_backup_time()

	def run(self):
		while True:  # loop until stop
			while True:  # loop for backup interval
				if self.stop_event.wait(1):
					return
				if time.time() - self.time_since_backup > self.get_backup_interval():
					break
			if self.is_enabled and self.server.is_server_startup():
				self.broadcast('每§6{}§r分钟一次的定时备份触发'.format(config['interval']))
				self.server.dispatch_event(TRIGGER_BACKUP_EVENT, (self.command_source, '{} 定时备份'.format(PLUGIN_METADATA['name'])), on_executor_thread=False)

	def stop(self):
		self.stop_event.set()


clock = None  # type: Optional[TimedQBM]


# ------------------
#   Configs things
# ------------------


def load_config(server: ServerInterface):
	global config
	config = default_config.copy()
	if not os.path.isfile(CONFIG_FILE):
		server.logger.info('配置文件未找到，使用默认配置')
	else:
		with open(CONFIG_FILE, 'r') as f:
			config.update(json.load(f))
	save_config()
	server.logger.info('是否启动: {}; 定时备份间隔: {} 分钟'.format(config['enabled'], config['interval']))


def save_config():
	with open(CONFIG_FILE, 'w') as f:
		json.dump(config, f, indent=2)


# ------------------
#   Commands Impls
# ------------------


def set_enabled(source: CommandSource, value: bool):
	config['enabled'] = value
	clock.set_enabled(value)
	save_config()
	source.reply('定时器已{}'.format('启动' if value else '关闭'))
	if value:
		clock.broadcast_next_backup_time()


def set_interval(source: CommandSource, itv: float):
	config['interval'] = itv
	save_config()
	source.reply('定时器触发间隔已设置为§6{}§r分钟'.format(itv))
	clock.broadcast_next_backup_time()


def reset_timer(source: CommandSource):
	clock.reset_timer()
	source.reply('定时器已重置')
	clock.broadcast_next_backup_time()


def register_things(server: ServerInterface):
	server.register_event_listener(BACKUP_DONE_EVENT, lambda svr, src, slot_info: clock.on_backup_created(slot_info))
	server.register_help_message(PREFIX, '定时备份插件，基于QuickBackupM', permission=config['permission_requirement'])
	server.register_command(
		Literal(PREFIX).
		requires(lambda src: src.has_permission(config['permission_requirement'])).
		on_error(RequirementNotMet, lambda src: src.reply(RText('权限不足！', color=RColor.red)), handled=True).
		on_error(UnknownArgument, lambda src: src.reply(RText('未知指令，输入{}以查看帮助'.format(PREFIX)))).
		runs(lambda src: (src.reply(HELP_MESSAGE), src.reply(clock.get_next_backup_message()))).
		then(Literal('enable').runs(lambda src: set_enabled(src, True))).
		then(Literal('disable').runs(lambda src: set_enabled(src, False))).
		then(Literal('set_interval').then(Float('i').at_min(0.1).runs(lambda src, ctx: set_interval(src, ctx['i'])))).
		then(Literal('reset_timer').runs(reset_timer))
	)


# ---------------
#   MCDR Events
# ---------------


def on_load(server: ServerInterface, prev):
	load_config(server)

	global clock
	clock = TimedQBM(server)
	try:
		clock.time_since_backup = float(prev.clock.time_since_backup)
	except (AttributeError, ValueError):
		pass

	clock.set_enabled(config['enabled'])
	clock.start()

	register_things(server)


def on_unload(server):
	server.logger.info('插件卸载，停止时钟')
	clock.stop()


def on_remove(server):
	server.logger.info('插件被移除，停止时钟')
	clock.stop()
