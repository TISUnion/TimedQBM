import os
from typing import Optional

from mcdreforged.api.all import *

from timed_quick_backup_multi import constants, stored
from timed_quick_backup_multi.clock import TimedQBM


class Config(Serializable):
	enabled: bool = True
	interval: float = 30.0  # minutes
	permission_requirement: int = 2
	require_online_players: bool = False


config: Config
CONFIG_FILE = os.path.join('config', 'timed_quick_backup_multi.json')
clock = None  # type: Optional[TimedQBM]
player_count = 0
flag_count_correct = False


def save_config():
	stored.server.save_config_simple(config, CONFIG_FILE, in_data_folder=False)


def has_online_player():
	if flag_count_correct and player_count >= 1:
		return True
	else:
		return False


def player_online_clock_state_sync():
	if config.require_online_players:
		if flag_count_correct:
			clock.set_enabled(has_online_player())
		else:
			clock.set_enabled(False)


def set_player_count(count: int):
	if config.require_online_players:
		if flag_count_correct:  # only maintain the player count if the flag is true
			global player_count
			player_count = count
			player_online_clock_state_sync()


# ------------------
#   Commands Impls
# ------------------


def set_enabled(source: CommandSource, value: bool):
	config.enabled = value
	clock.set_enabled(value)
	save_config()
	source.reply(TimedQBM.tr('set_enabled.timer', TimedQBM.tr('set_enabled.start') if value else TimedQBM.tr('set_enabled.stop')))
	if value:
		clock.broadcast_next_backup_time()


def set_interval(source: CommandSource, interval: float):
	config.interval = interval
	save_config()
	source.reply(TimedQBM.tr('set_interval', interval))
	clock.broadcast_next_backup_time()


def reset_timer(source: CommandSource):
	clock.reset_timer()
	source.reply(TimedQBM.tr('reset_timer'))
	clock.broadcast_next_backup_time()


def show_status(source: CommandSource):
	source.reply(TimedQBM.tr('status.config_enabled', config.enabled))
	if config.enabled:
		source.reply(TimedQBM.tr('status.clock_enabled', clock.is_enabled))
		if clock.is_enabled:
			source.reply(TimedQBM.tr('status.clock_interval', round(config.interval, 2)))
			source.reply(clock.get_next_backup_message())
		if config.require_online_players:
			source.reply(TimedQBM.tr('status.has_online_player', has_online_player()))


def register_things(server: PluginServerInterface):
	HELP_MESSAGE = TimedQBM.tr('help_message', constants.PREFIX, stored.metadata.name, stored.metadata.version, stored.metadata.get_description_rtext())
	server.register_event_listener(constants.BACKUP_DONE_EVENT, lambda svr, src, slot_info: clock.on_backup_created(slot_info))
	server.register_help_message(constants.PREFIX, TimedQBM.tr('info'), permission=config.permission_requirement)
	server.register_command(
		Literal(constants.PREFIX).
		requires(lambda src: src.has_permission(config.permission_requirement)).
		on_error(RequirementNotMet, lambda src: src.reply(RText(TimedQBM.tr('no_permission'), color=RColor.red)), handled=True).
		on_error(UnknownArgument, lambda src: src.reply(RText(TimedQBM.tr('unknown_command', constants.PREFIX)))).
		runs(lambda src: (src.reply(HELP_MESSAGE), src.reply(clock.get_next_backup_message()))).
		then(Literal('enable').runs(lambda src: set_enabled(src, True))).
		then(Literal('disable').runs(lambda src: set_enabled(src, False))).
		then(Literal('set_interval').then(Float('interval').at_min(0.1).runs(lambda src, ctx: set_interval(src, ctx['interval'])))).
		then(Literal('reset_timer').runs(reset_timer)).
		then(Literal('status').runs(show_status))
	)


# ---------------
#   MCDR Events
# ---------------

def on_load(server: PluginServerInterface, prev):
	global config
	stored.server = server
	stored.metadata = server.get_self_metadata()
	config = server.load_config_simple(CONFIG_FILE, target_class=Config, in_data_folder=False)

	global clock, player_count, flag_count_correct
	clock = TimedQBM(server)
	try:
		clock.time_since_backup = float(prev.clock.time_since_backup)
		player_count = int(prev.player_count)
		flag_count_correct = bool(prev.flag_count_correct)
	except (AttributeError, ValueError):
		pass

	clock.set_enabled(config.enabled)
	player_online_clock_state_sync()
	clock.start()

	register_things(server)


def on_server_start(server: PluginServerInterface):
	"""
	disable backup if online player is required until someone joins the server
	putting logic here to avoid unintended behavior from reload/load plugin after server started
	"""
	global config, clock, flag_count_correct
	if config.require_online_players:
		server.logger.info('Server start detected, enabling online player requirement testing')
	flag_count_correct = True  # yeah we are loaded before minecraft server, thus playercount is right!
	set_player_count(0)


def on_player_joined(server: PluginServerInterface, player: str, info: Info):
	set_player_count(player_count + 1)


def on_player_left(server: PluginServerInterface, info: Info):
	set_player_count(player_count - 1)


def on_unload(server):
	server.logger.info(TimedQBM.tr('on_unload'))
	clock.stop()


def on_remove(server):
	server.logger.info(TimedQBM.tr('on_remove'))
	clock.stop()
