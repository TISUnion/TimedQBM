import time
from threading import Thread, Event

from mcdreforged.api.all import *

from timed_quick_backup_multi import stored, constants


class TimedQBM(Thread):
	def __init__(self, server: PluginServerInterface):
		super().__init__()
		self.setDaemon(True)
		self.setName(self.__class__.__name__)
		self.time_since_backup = time.time()
		self.server = server
		self.stop_event = Event()
		self.is_enabled = False

	@staticmethod
	def __get_interval() -> float:
		from timed_quick_backup_multi.entry import config
		return config.interval

	@classmethod
	def get_backup_interval(cls):
		return cls.__get_interval() * 60

	def broadcast(self, message):
		rtext = RTextList('[{}] '.format(stored.metadata.name), message)
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
				self.broadcast('每§6{}§r分钟一次的定时备份触发'.format(self.__get_interval()))
				self.server.dispatch_event(constants.TRIGGER_BACKUP_EVENT, (self.server.get_plugin_command_source(), '{} 定时备份'.format(stored.metadata.name)), on_executor_thread=False)

	def stop(self):
		self.stop_event.set()

