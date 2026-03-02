# 修复按键绑定成功后 Cancel 按钮未隐藏问题

## Why
在 Motion Control 页面中，用户添加新的按键绑定时，成功绑定按键后，Cancel 按钮仍然显示在界面上，这不符合预期的用户体验。成功绑定后，临时状态应该结束，Cancel 按钮应该被移除。

## What Changes
- 在 `motion.py` 的 `on_key_selected` 方法中，添加移除 Cancel 按钮的逻辑
- 确保按键绑定成功后，临时绑定项转变为正式绑定项，所有临时按钮都被移除

## Impact
- Affected code: `motion.py` 中的 `on_key_selected` 方法

## ADDED Requirements
### Requirement: 按键绑定完成后的 UI 状态
系统 SHALL 在按键绑定成功完成后，移除所有临时操作按钮（包括 Select Key 和 Cancel 按钮）。

#### Scenario: 按键绑定成功
- **WHEN** 用户在按键选择窗口中选择一个按键并确认
- **THEN** 系统应该：
  1. 更新绑定项的按键名称
  2. 将临时状态标记为非临时（is_temp = False）
  3. 移除 Select Key 按钮
  4. **移除 Cancel 按钮**
  5. 保存绑定到配置文件
  6. 记录日志

## MODIFIED Requirements
### Requirement: on_key_selected 方法
在 `motion.py` 的 `on_key_selected` 方法中，完成以下操作：
1. 更新绑定项的 key_name
2. 设置 is_temp 为 False
3. 更新标签显示
4. 移除 Select Key 按钮（已有）
5. **移除 Cancel 按钮（新增）**
6. 保存绑定到配置文件
