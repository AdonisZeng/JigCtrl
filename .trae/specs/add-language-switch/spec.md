# 完善中英文切换功能

## Why
之前实现的中英文切换功能只覆盖了少部分文案，还有很多界面文本没有实现切换。需要完善所有界面文本的中英文翻译。

## What Changes
- 完善 `language.py` 中的翻译字典，添加所有缺失的文本
- 更新 `motion.py` 中所有硬编码的文本
- 更新 `test_control.py` 中所有硬编码的文本
- 更新 `log.py` 中所有硬编码的文本
- 更新 `motor_debug.py` 中所有硬编码的文本
- 更新 `settings.py` 中所有硬编码的文本

## Impact
- Affected code: `language.py`, `motion.py`, `test_control.py`, `log.py`, `motor_debug.py`, `settings.py`

## ADDED Requirements

### Requirement: 完整的翻译覆盖
系统 SHALL 为所有界面文本提供中英文翻译。

### Requirement: motion.py 完整翻译
以下文本需要添加翻译：
- "Manual Control" → motion_manual_control
- "▲ Up" → motion_up
- "◀ Left" → motion_left  
- "▼ Down" → motion_down
- "▶ Right" → motion_right
- "Coordinate System" → motion_coordinate_system
- "Homing Speed (RPM):" → motion_homing_speed
- "Get" → motion_get
- "Set" → motion_set
- "X-Axis Position" → motion_x_position
- "Y-Axis Position" → motion_y_position
- "Refresh" → motion_refresh
- "Manage key positions for automated testing" → motion_binding_hint
- "Key:" → motion_key_label
- "X:" → motion_x_label
- "Y:" → motion_y_label
- "Select Key" → motion_select_key
- "Cancel" → motion_cancel
- "按键:" → motion_key_label (中文)

### Requirement: test_control.py 完整翻译
以下文本需要添加翻译：
- "Test Mode:" → test_mode_label
- "Count Mode" → test_count_mode
- "Time Mode" → test_time_mode
- "Test Count:" → test_count_label
- "Duration (seconds):" → test_duration_label
- "Remaining:" → test_remaining_label
- "Current Item:" → test_current_item_label
- "times" → test_times
- "seconds" → test_seconds

### Requirement: log.py 完整翻译
以下文本需要添加翻译：
- "Time Range:" → log_time_range
- "Category:" → log_category
- "Keyword:" → log_keyword
- "All" → log_all
- "Apply Filter" → log_apply_filter

### Requirement: motor_debug.py 完整翻译
以下文本需要添加翻译：
- "Serial Configuration" → debug_serial_config
- "Port:" → debug_port
- "Baud:" → debug_baud
- "Open" → debug_open
- "Close" → debug_close
- "Refresh" → debug_refresh
- "Quick Commands" → debug_quick_commands
- "Run" → debug_run
- "Pause" → debug_pause
- "Stop" → debug_stop
- "Status" → debug_status
- "Speed:" → debug_speed
- "Direction:" → debug_direction
- "CW" → debug_cw
- "CCW" → debug_ccw
- "Travel (Pulse/Rev/Angle):" → debug_travel
- "Pulse" → debug_pulse
- "Rev" → debug_rev
- "Angle" → debug_angle
- "Get All Params" → debug_get_all
- "Manual Command" → debug_manual
- "Send Manual Command" → debug_send
- "Communication Log" → debug_log
- "Clear" → debug_clear
- "Copy" → debug_copy
- "ASCII" → debug_ascii

### Requirement: settings.py 完整翻译
以下文本需要添加翻译：
- "X-Axis Motor" → settings_x_motor
- "Y-Axis Motor" → settings_y_motor
- "Relay (Solenoid)" → settings_relay
- "Port:" → settings_port
- "Baud Rate:" → settings_baud
- "Open Port" → settings_open_port
- "Close Port" → settings_close_port
- "Press Settings" → settings_press
- "Press Duration (ms):" → settings_press_duration
- "Interval (ms):" → settings_interval
- "Test Flow" → settings_test_flow
- "Add Test Item" → settings_add_item
- "Item Name" → settings_item_name
- "Key" → settings_key
- "Move Up" → settings_move_up
- "Move Down" → settings_move_down
- "Remove" → settings_remove
- "Apply" → settings_apply
