# 修复中英文切换后部分文案未切换回英文的问题

## Why
用户反馈在点击切换回英文后，有部分文案没有切换回英文。经过检查发现，`SerialConfigFrame` 的标题是通过参数传入的硬编码字符串，而不是使用翻译函数。

## What Changes
- 修改 `SettingsFrame` 中创建 `SerialConfigFrame` 时传入的标题，使用翻译函数获取
- 更新 `language.py` 添加缺失的串口配置标题翻译
- 确保 `SerialConfigFrame` 的标题在语言切换时正确更新

## Impact
- Affected code: `settings.py`, `language.py`

## ADDED Requirements

### Requirement: 串口配置标题翻译
系统 SHALL 为串口配置框架的标题提供中英文翻译。

#### Scenario: 切换语言时更新串口配置标题
- **WHEN** 用户切换语言
- **THEN** 串口配置框架的标题应该正确切换为对应语言

## MODIFIED Requirements

### Requirement: SettingsFrame 串口配置标题
修改 `SettingsFrame` 中创建 `SerialConfigFrame` 的代码：
- 使用翻译函数获取标题文本
- 在 `refresh_texts` 方法中更新串口配置框架的标题
