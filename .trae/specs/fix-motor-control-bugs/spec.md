# 修复测试控制中电机控制相关 Bug

## Why
在 Test Control 页面中存在以下 Bug：
1. 当绑定的按键坐标为 (0,0) 时，程序仍然发送脉冲数为 0 的命令，导致电机一直运转（根据 Modbus-RTU 协议，脉冲数为 0 表示无限运行）
2. 点击 Stop 按钮后，程序只设置了停止标志，但没有发送电机停止命令，导致电机继续运转
3. 当前逻辑直接使用绑定的脉冲数作为目标，没有考虑当前电机位置，无法正确计算需要移动的距离

## What Changes
- 在 `send_motor_pulse` 方法中，当脉冲数为 0 时跳过发送命令
- 在 `stop_test` 方法中，添加发送电机停止命令的逻辑
- 添加跟踪当前电机位置的功能，计算相对移动距离

## Impact
- Affected code: `test_control.py` 中的 `send_motor_pulse`、`stop_test`、`run_test_cycle` 方法

## ADDED Requirements

### Requirement: 电机移动优化
系统 SHALL 在发送电机移动命令前检查目标脉冲数，当目标脉冲数为 0 时跳过移动命令。

#### Scenario: 目标位置为原点
- **WHEN** 绑定的按键坐标为 (0,0) 或与当前位置相同
- **THEN** 系统应该跳过该轴的电机移动命令

### Requirement: 停止测试时发送停止命令
系统 SHALL 在用户点击 Stop 按钮时，向所有已连接的电机发送停止命令（寄存器 0x03，值 1）。

#### Scenario: 停止测试
- **WHEN** 用户点击 Stop 按钮
- **THEN** 系统应该：
  1. 设置停止请求标志
  2. 向 X 轴电机发送停止命令
  3. 向 Y 轴电机发送停止命令
  4. 记录日志

### Requirement: 基于当前位置计算移动距离
系统 SHALL 跟踪当前电机位置，并计算相对于当前位置的移动距离。

#### Scenario: 计算相对移动距离
- **WHEN** 需要移动电机到目标位置
- **THEN** 系统应该：
  1. 获取当前电机位置
  2. 计算目标位置与当前位置的差值
  3. 如果差值为 0，跳过移动
  4. 如果差值不为 0，发送相应方向的移动命令

## MODIFIED Requirements

### Requirement: send_motor_pulse 方法
修改 `send_motor_pulse` 方法：
- 添加脉冲数为 0 的检查，跳过发送命令
- 添加方向判断逻辑（正转/反转）
- 记录当前电机位置

### Requirement: stop_test 方法
修改 `stop_test` 方法：
- 添加发送电机停止命令的逻辑
- 使用寄存器 0x03（停止），值为 1

### Requirement: run_test_cycle 方法
修改 `run_test_cycle` 方法：
- 在移动电机前，先读取当前电机位置
- 计算需要移动的相对距离
- 根据差值判断是否需要移动和移动方向
