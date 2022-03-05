Timed QuickBackupM
-------

English | [中文](https://github.com/TISUnion/TimedQBM/blob/master/README.md)

An extension to the [QuickBackupM](https://github.com/TISUnion/QuickBackupM) plugin to trigger QBM at regular intervals and thus perform automatic backups

Backup timer resets the last backup time to the current time when the QBM backup is finished and the timer is manually started/shutdown/reset

TQBM will trigger a QBM backup whenever the time interval since the last backup is greater than the backup interval specified in the configuration file

Can be used with the `delete_protection` value in the QBM plugin configuration file to avoid TQBM from overwriting too many backups

## Requirements

- [MCDR](https://github.com/Fallen-Breath/MCDReforged) >=2.0.0

- [QuickBackupM](https://github.com/TISUnion/QuickBackupM) >=1.1.0

## Configuration

The configuration file is ``config/timed_quick_backup_multi.json``

```json
{
  "enabled": true,
  "interval": 30.0,
  "permission_requirement": 2
}
```

- `enable`: TQBM backup timer master switch
- `interval`: The interval of the TQBM backup timer in minutes
- `permission_requirement`: Use the `! !tqb` directive's minimum permission requirement

## Commands

- `!!tqb`: Display TQBM help information
- `!!tqb enable`: Start TQBM backup timer
- `!!tqb disable`: Disable the TQBM backup timer
- `!!tqb set_interval <minutes>`: Set the TQBM backup timer interval in minutes
- `!!tqb reset_timer`: Reset the TQBM backup timer
