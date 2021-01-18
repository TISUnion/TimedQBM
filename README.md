Timed QuickBackupM
-------

一个 [QuickBackupM](https://github.com/TISUnion/QuickBackupM) 插件的扩展，用于定时触发 QBM 从而进行自动备份

备份定时器会在 QBM 备份结束、定时器被手动启动/关闭/重置时，重置上次备份时间为当前时间

每当离上次备份的时间间隔大于了配置文件指定的备份时间间隔，TQBM 会触发一次 QBM 的备份

可配合 QBM 插件配置文件的 `delete_protection` 数值来避免 TQBM 覆盖过多备份

## 需求

- [MCDR](https://github.com/Fallen-Breath/MCDReforged) >=1.2.0

- [QuickBackupM](https://github.com/TISUnion/QuickBackupM) >=1.1.0

## 配置

配置文件为 `config/timed_quick_backup_multi.json`

```json
{
  "enabled": true,
  "interval": 30.0,
  "permission_requirement": 2
}
```

- `enable`: TQBM 备份定时器总开关
- `interval`: TQBM 备份定时器的间隔，单位为分钟
- `permission_requirement`: 使用 `!!tqb` 指令的最小权限需求

## 指令

- `!!tqb`: 显示 TQBM 帮助信息
- `!!tqb enable`: 启动 TQBM 备份定时器
- `!!tqb disable`: 关闭 TQBM 备份定时器
- `!!tqb set_interval <minutes>`: 设置 TQBM 备份定时器时间间隔，单位分钟
- `!!tqb reset_timer`: 重置 TQBM 备份定时器
