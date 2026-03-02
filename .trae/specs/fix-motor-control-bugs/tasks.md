# Tasks

- [x] Task 1: 修复 send_motor_pulse 方法 - 脉冲数为 0 时跳过发送命令
  - [x] SubTask 1.1: 在 `send_motor_pulse` 方法中添加脉冲数为 0 的检查
  - [x] SubTask 1.2: 添加方向判断逻辑（正转/反转）

- [x] Task 2: 修复 stop_test 方法 - 添加发送电机停止命令
  - [x] SubTask 2.1: 创建 `send_motor_stop` 方法，发送停止命令到指定电机
  - [x] SubTask 2.2: 在 `stop_test` 方法中调用 `send_motor_stop` 停止 X 轴和 Y 轴电机

- [x] Task 3: 添加电机位置跟踪功能
  - [x] SubTask 3.1: 在类中添加当前电机位置变量 `current_x_pulse` 和 `current_y_pulse`
  - [x] SubTask 3.2: 创建 `read_motor_pulse` 方法，读取电机当前脉冲数
  - [x] SubTask 3.3: 在 `send_motor_pulse` 方法中更新当前位置变量

- [x] Task 4: 优化电机移动逻辑 - 基于当前位置计算移动距离
  - [x] SubTask 4.1: 在 `run_test_cycle` 方法中，移动电机前先读取当前位置
  - [x] SubTask 4.2: 计算目标位置与当前位置的差值
  - [x] SubTask 4.3: 根据差值判断是否需要移动和移动方向

# Task Dependencies
- Task 3 依赖 Task 1
- Task 4 依赖 Task 3
