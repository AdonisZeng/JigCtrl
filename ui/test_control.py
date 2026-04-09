import tkinter as tk
from tkinter import ttk
import datetime
import time
import threading
import struct
from core.key_manager import KeyManager
from core.language import tr

class TestControlFrame(ttk.Frame):
    """
    TestControlFrame 类：负责测试流程的控制与监控。
    包含测试状态显示、启动/暂停/停止控制，以及核心测试循环逻辑。
    """
    def __init__(self, master=None, settings_source=None, log_callback=None):
        """
        初始化测试控制面板。
        
        :param master: 父容器组件
        :param settings_source: 设置信息来源（通常是 SettingsFrame 实例），用于获取测试参数和串口连接
        :param log_callback: 日志回调函数，用于输出测试过程中的信息
        """
        super().__init__(master)
        # --- 成员变量初始化 ---
        self.settings_source = settings_source
        self.log = log_callback if log_callback else print  # 如果未提供回调，则默认打印到控制台
        self.key_manager = KeyManager() # 初始化按键管理器
        self.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # --- 测试状态变量 ---
        self.timer_id = None            # Tkinter 定时器 ID，用于倒计时更新
        self.remaining_seconds = 0      # 剩余测试时间（秒）
        self.remaining_counts = 0       # 剩余测试次数
        self.current_item_index = 0     # 当前测试项索引
        self.test_flow = []             # 测试流程
        self.is_running = False         # 标志：测试是否正在运行
        self.is_paused = False          # 标志：测试是否处于暂停状态
        self.stop_requested = False     # 标志：用户是否请求停止测试
        self.pause_requested = False    # 标志：用户是否请求暂停测试
        self.skip_item_requested = False # 标志：用户是否请求跳过当前测试项
        self.current_test_thread = None # 当前运行测试逻辑的后台线程
        
        # --- 多键测试专用变量 ---
        self.multi_key_pause_pending = False  # 标志：多键测试暂停请求（用于区分普通暂停）
        self.multi_key_test_active = False    # 标志：是否正在执行多键测试
        
        # --- 电机位置跟踪变量 ---
        self.current_x_pulse = 0        # X 轴当前脉冲位置
        self.current_y_pulse = 0        # Y 轴当前脉冲位置
        
        # --- 循环测试相关变量 ---
        self.total_rounds = 1           # 总轮次
        self.current_round = 1          # 当前轮次
        self.loop_enabled = False       # 是否启用循环测试
        
        self.create_widgets()

    # ==========================================
    # 界面构建分区
    # ==========================================
    def create_widgets(self):
        """创建并布局测试控制界面的所有组件"""
        
        # --- 状态监控显示区 ---
        self.status_frame = ttk.LabelFrame(self, text=tr("test_status_monitor"), padding=30)
        self.status_frame.pack(fill=tk.X, pady=10)

        # 使用一个容器来居中显示内容
        monitor_container = ttk.Frame(self.status_frame)
        monitor_container.pack(expand=True)

        # 当前运行状态标签
        self.lbl_status = ttk.Label(monitor_container, text=tr("test_current_state"), font=("Cambria", 16, "bold"), foreground="#605e5c")
        self.lbl_status.pack(pady=10)

        # 进度指示器容器
        progress_info = ttk.Frame(monitor_container)
        progress_info.pack(pady=10)

        self.lbl_remaining = ttk.Label(progress_info, text=tr("test_remaining") + ": --", font=("Cambria", 14))
        self.lbl_remaining.pack()

        # --- 控制按钮区 ---
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=30)

        self.btn_start = ttk.Button(btn_frame, text=tr("test_start"), style="Success.TButton", command=self.start_test)
        self.btn_pause = ttk.Button(btn_frame, text=tr("test_pause"), command=self.pause_test, state=tk.DISABLED)
        self.btn_skip = ttk.Button(btn_frame, text=tr("test_skip"), command=self.skip_to_next, state=tk.DISABLED)
        self.btn_stop = ttk.Button(btn_frame, text=tr("test_stop"), style="Danger.TButton", command=self.stop_test, state=tk.DISABLED)

        # 统一设置按钮宽度
        self.btn_start.pack(side=tk.LEFT, padx=15, ipadx=10)
        self.btn_pause.pack(side=tk.LEFT, padx=15, ipadx=10)
        self.btn_skip.pack(side=tk.LEFT, padx=15, ipadx=10)
        self.btn_stop.pack(side=tk.LEFT, padx=15, ipadx=10)

    # ==========================================
    # 测试控制逻辑分区
    # ==========================================
    def start_test(self):
        """
        启动测试按钮的回调函数。
        根据当前状态，可能是开启新测试或恢复已暂停的测试。
        """
        if self.btn_start['text'] == "Resume":
            # 如果当前是暂停状态，则执行恢复逻辑
            self.resume_test()
        else:
            # 执行新测试启动逻辑
            if not self.settings_source:
                self.log("Error: Settings source not available", "ERR")
                return

            # 从设置源获取当前配置快照
            settings = self.settings_source.get_current_state()
            self.test_flow = settings.get('test_flow', [])
            
            if not self.test_flow:
                self.log("Error: Test flow is empty. Please add test items in Settings.", "ERR")
                return

            self.current_item_index = 0
            
            # 读取循环测试配置
            loop_enabled = settings.get('loop_enabled', False)
            loop_count = settings.get('loop_count', 1)
            loop_locked = settings.get('loop_locked', False)
            
            # 只有当 loop_enabled 和 loop_locked 都为 True 时才启用循环
            self.loop_enabled = loop_enabled and loop_locked
            self.total_rounds = loop_count if self.loop_enabled else 1
            self.current_round = 1
            
            # 重置所有控制标志位
            self.is_running = True
            self.is_paused = False
            self.stop_requested = False
            self.pause_requested = False
            
            # 开启后台线程执行核心测试循环
            self.current_test_thread = threading.Thread(target=self.run_test_cycle, daemon=True)
            self.current_test_thread.start()
            
        # 更新 UI 状态为“测试中”
        self.update_ui_state("TESTING")
        self.log("Test Started", "TEST")

    def update_ui_state(self, state):
        """
        根据测试阶段更新 UI 组件的状态。
        """
        if state == "TESTING":
            self.lbl_status.config(text=tr("test_testing"), foreground="#107c10")
            self.btn_start.config(state=tk.DISABLED)
            self.btn_pause.config(state=tk.NORMAL, text=tr("test_pause"))
            self.btn_skip.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.NORMAL)
        elif state == "PAUSED":
            self.lbl_status.config(text=tr("test_paused"), foreground="#d13438")
            self.btn_start.config(state=tk.NORMAL, text=tr("test_resume"))
            self.btn_pause.config(state=tk.DISABLED)
            self.btn_skip.config(state=tk.NORMAL)
        elif state == "STANDBY":
            self.lbl_status.config(text=tr("test_standby"), foreground="#605e5c")
            self.btn_start.config(state=tk.NORMAL, text=tr("test_start"))
            self.btn_pause.config(state=tk.DISABLED, text=tr("test_pause"))
            self.btn_skip.config(state=tk.DISABLED)
            self.btn_stop.config(state=tk.DISABLED)
            self.lbl_remaining.config(text=tr("test_remaining") + ": --")

    def run_test_cycle(self):
        """
        核心测试循环逻辑。遍历测试流程中的每一个测试项。
        支持多轮次循环测试。
        """
        settings = self.settings_source.get_current_state()
        relay_conn = self.settings_source.get_serial_connection("Relay (Solenoid)")
        motor_x_conn = self.settings_source.get_serial_connection("X-Axis Motor")
        motor_y_conn = self.settings_source.get_serial_connection("Y-Axis Motor")
        
        # --- 串口连接检查 ---
        missing_ports = []
        if not relay_conn or not relay_conn.is_open: missing_ports.append("Relay")
        if not motor_x_conn or not motor_x_conn.is_open: missing_ports.append("X-Axis Motor")
        if not motor_y_conn or not motor_y_conn.is_open: missing_ports.append("Y-Axis Motor")
        
        if missing_ports:
            self.log(f"Error: The following serial ports are not open: {', '.join(missing_ports)}", "ERR")
            self.log("Please open all required serial ports in 'Parameter Settings' tab before starting the test.", "ERR")
            self.is_running = False
            self.lbl_remaining.after(0, self.finish_test)
            return

        # --- 读取电机当前位置 ---
        self.log("Reading current motor positions...", "MOT")
        
        x_pulse = self.read_motor_pulse(motor_x_conn, "X")
        if x_pulse is not None:
            self.current_x_pulse = x_pulse
        
        y_pulse = self.read_motor_pulse(motor_y_conn, "Y")
        if y_pulse is not None:
            self.current_y_pulse = y_pulse
        
        self.log(f"Current positions - X: {self.current_x_pulse}, Y: {self.current_y_pulse}", "MOT")

        press_duration = settings.get('press_duration', 100) / 1000.0
        interval = settings.get('press_interval', 500) / 1000.0

        # 继电器控制指令
        CMD_OPEN = bytes.fromhex("A0 01 01 A2")
        CMD_CLOSE = bytes.fromhex("A0 01 00 A1")

        all_bindings = self.key_manager.get_bindings()
        binding_dict = {b['key_name']: b for b in all_bindings}

        # --- 轮次循环 ---
        total_rounds = self.total_rounds
        for round_num in range(1, total_rounds + 1):
            if self.stop_requested:
                break
            
            # 更新当前轮次
            self.current_round = round_num
            
            # 显示轮次信息
            if self.loop_enabled:
                self.log(f"{tr('test_round')} {round_num}/{total_rounds}", "TEST")
            
            # 重置测试项索引（每轮重新开始）
            self.current_item_index = 0
            
            for i in range(len(self.test_flow)):
                if self.stop_requested:
                    break
                
                self.current_item_index = i
                item = self.test_flow[i]
                key_name = item['key_name']
                is_multi_key = item.get('type') == 'multi'
                
                # 通知设置页刷新显示（更新正在测试/已完成状态）
                if hasattr(self.settings_source, 'render_test_flow'):
                    self.lbl_remaining.after(0, self.settings_source.render_test_flow)
                
                self.log(f"Testing item {i+1}/{len(self.test_flow)}: {key_name} ({'Multi-Key' if is_multi_key else 'Single Key'})", "TEST")
                
                # 1. 移动电机到指定位置
                if is_multi_key:
                    # 多键测试：计算两个按键的中点坐标
                    key_names = item.get('key_names', [])
                    if len(key_names) >= 2:
                        binding1 = binding_dict.get(key_names[0])
                        binding2 = binding_dict.get(key_names[1])
                        if binding1 and binding2:
                            x1, y1 = binding1.get('x_pulse', 0), binding1.get('y_pulse', 0)
                            x2, y2 = binding2.get('x_pulse', 0), binding2.get('y_pulse', 0)
                            # 计算中点坐标（正确处理负数坐标，使用round进行四舍五入）
                            x_pulse = round((x1 + x2) / 2)
                            y_pulse = round((y1 + y2) / 2)
                            self.log(f"Multi-key center position: ({x_pulse}, {y_pulse}) from ({key_names[0]}: {x1},{y1}) and ({key_names[1]}: {x2},{y2})", "MOT")
                        else:
                            self.log(f"Warning: Missing binding for multi-key test", "WRN")
                            x_pulse, y_pulse = 0, 0
                    else:
                        self.log(f"Warning: Invalid multi-key configuration", "WRN")
                        x_pulse, y_pulse = 0, 0
                else:
                    # 单键测试：直接获取按键坐标
                    binding = binding_dict.get(key_name)
                    if binding:
                        x_pulse = binding.get('x_pulse', 0)
                        y_pulse = binding.get('y_pulse', 0)
                    else:
                        self.log(f"Warning: No binding found for {key_name}", "WRN")
                        x_pulse, y_pulse = 0, 0
                
                # 移动电机到目标位置（send_motor_pulse 内部会检查是否需要移动）
                self.log(f"Target position (X:{x_pulse}, Y:{y_pulse})", "MOT")
                self.send_motor_pulse(motor_x_conn, x_pulse, "X")
                self.send_motor_pulse(motor_y_conn, y_pulse, "Y")
                
                self.wait_for_motor_arrival(motor_x_conn, x_pulse, "X")
                if self.stop_requested or self.skip_item_requested:
                    if hasattr(self, 'motion_control') and self.motion_control:
                        self.lbl_remaining.after(0, self.motion_control.refresh_positions)
                    if self.stop_requested: break
                    if self.skip_item_requested:
                        self.skip_item_requested = False
                        continue
                
                self.wait_for_motor_arrival(motor_y_conn, y_pulse, "Y")
                
                # 电机移动完成后刷新运动控制页面的位置显示
                if hasattr(self, 'motion_control') and self.motion_control:
                    self.lbl_remaining.after(0, self.motion_control.refresh_positions)

                if self.stop_requested: break
                if self.skip_item_requested:
                    self.skip_item_requested = False
                    continue

                # 2. 多键测试：移动到位置后自动暂停，等待用户手动操作
                if is_multi_key:
                    self.multi_key_test_active = True
                    self.multi_key_pause_pending = True
                    self.log("Multi-key test: Auto-paused. Please press the keys manually, then click 'Resume' to continue.", "TEST")
                    
                    # 在UI线程中更新暂停状态
                    self.lbl_remaining.after(0, lambda: self.update_ui_state("PAUSED"))
                    
                    # 等待用户继续
                    while self.multi_key_pause_pending and not self.stop_requested and not self.skip_item_requested:
                        time.sleep(0.1)
                    
                    self.multi_key_test_active = False
                    self.multi_key_pause_pending = False
                    
                    if self.stop_requested: break
                    if self.skip_item_requested:
                        self.skip_item_requested = False
                        continue
                    
                    # 用户继续后，继续执行后续的继电器测试逻辑
                    self.lbl_remaining.after(0, lambda: self.update_ui_state("TESTING"))
                    self.log("Multi-key test: Resumed, starting relay test cycle.", "TEST")

                # 3. 初始化该项的剩余值
                mode = item.get('mode')
                target = item.get('target', 0)
                
                if mode == 'time':
                    unit = item.get('unit', 'Seconds')
                    seconds = target
                    if unit == 'Minutes': seconds = target * 60
                    elif unit == 'Hours': seconds = target * 3600
                    self.remaining_seconds = seconds
                    self.lbl_remaining.after(0, lambda: self.update_remaining_display(mode))
                    
                    # 启动时间模式下的 UI 倒计时
                    self.lbl_remaining.after(0, self.run_timer_async)
                else:
                    self.remaining_counts = target
                    self.lbl_remaining.after(0, lambda: self.update_remaining_display(mode))

                # 4. 执行单项测试循环
                while self.is_running:
                    if self.stop_requested or self.skip_item_requested: break
                    
                    # 检查暂停（普通暂停）
                    if self.pause_requested:
                        self.is_paused = True
                        while self.pause_requested and not self.stop_requested:
                            time.sleep(0.1)
                        self.is_paused = False
                        if self.stop_requested: break

                    # 执行动作
                    try:
                        # 吸合继电器
                        relay_conn.write(CMD_OPEN)
                        self.log(f"Relay ON: {CMD_OPEN.hex(' ').upper()}", "COM")
                        time.sleep(press_duration)
                        
                        # 断开继电器
                        relay_conn.write(CMD_CLOSE)
                        self.log(f"Relay OFF: {CMD_CLOSE.hex(' ').upper()}", "COM")
                        time.sleep(interval)
                    except Exception as e:
                        self.log(f"Relay Error: {e}", "ERR")
                        break

                    if mode == 'count':
                        self.remaining_counts -= 1
                        self.lbl_remaining.after(0, lambda: self.update_remaining_display(mode))
                        if self.remaining_counts <= 0:
                            break
                    else:
                        if self.remaining_seconds <= 0:
                            break
                
                self.skip_item_requested = False
                if self.stop_requested: break
            
            # 轮次结束检查
            if self.stop_requested: break

        # 收尾
        self.is_running = False
        self.multi_key_test_active = False
        self.multi_key_pause_pending = False
        self.current_item_index = len(self.test_flow) # 全部标记为已完成
        if hasattr(self.settings_source, 'render_test_flow'):
            self.lbl_remaining.after(0, self.settings_source.render_test_flow)
        self.lbl_remaining.after(0, self.finish_test)

    def update_remaining_display(self, mode):
        """更新剩余时间/次数显示"""
        # 构建轮次前缀（仅在启用循环测试时显示）
        round_prefix = ""
        if self.loop_enabled:
            round_prefix = f"[{tr('test_current_round')} {self.current_round}/{self.total_rounds}] "
        
        if mode == 'time':
            m, s = divmod(self.remaining_seconds, 60)
            h, m = divmod(m, 60)
            self.lbl_remaining.config(text=f"{round_prefix}{tr('test_item')} {self.current_item_index+1}: {h:02d}:{m:02d}:{s:02d}")
        else:
            self.lbl_remaining.config(text=f"{round_prefix}{tr('test_item')} {self.current_item_index+1}: {self.remaining_counts} {tr('test_counts')}")

    def run_timer_async(self):
        """异步更新时间"""
        if not self.is_running or self.is_paused:
            if self.is_running: # 如果还在运行只是暂停，1秒后再试
                self.timer_id = self.after(1000, self.run_timer_async)
            return

        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.update_remaining_display('time')
            self.timer_id = self.after(1000, self.run_timer_async)
        else:
            self.timer_id = None

    def send_motor_pulse(self, conn, pulse, axis_name=""):
        """
        发送电机脉冲指令 (Modbus RTU)
        支持分段移动，当脉冲数超过 65535 时自动拆分
        
        :param conn: 串口连接
        :param pulse: 目标脉冲数（绝对位置）
        :param axis_name: 轴名称 ("X" 或 "Y")
        """
        if not conn or not conn.is_open:
            return
        
        MAX_PULSE_PER_MOVE = 65000
        
        # 获取当前位置
        current_pulse = self.current_x_pulse if axis_name == "X" else self.current_y_pulse
        
        # 计算需要移动的距离
        delta = pulse - current_pulse
        
        # 如果目标位置与当前位置相同，跳过移动
        if delta == 0:
            self.log(f"Motor {axis_name}: Already at target position ({pulse}), skipping movement", "MOT")
            return
        
        # 确定移动方向：delta > 0 正转(1)，delta < 0 反转(0)
        direction = 1 if delta > 0 else 0
        abs_delta = abs(delta)
        
        # 计算需要的分段数
        if abs_delta > 65535:
            segments = (abs_delta + MAX_PULSE_PER_MOVE - 1) // MAX_PULSE_PER_MOVE
            self.log(f"Motor {axis_name}: Large move ({abs_delta} pulses), splitting into {segments} segments", "MOT")
        
        try:
            remaining = abs_delta
            segment_num = 0
            local_current = current_pulse
            
            while remaining > 0:
                segment_num += 1
                # 本次要移动的脉冲数
                move_pulse = min(remaining, MAX_PULSE_PER_MOVE)
                
                # 设置方向（只在第一次设置）
                if segment_num == 1:
                    data = struct.pack('>BBHH', 0x01, 0x06, 0x01, direction)
                    crc = self.calculate_crc(data)
                    full_msg = data + struct.pack('<H', crc)
                    conn.write(full_msg)
                    direction_text = "CW" if direction == 1 else "CCW"
                    self.log(f"Motor {axis_name} Set Direction ({direction_text}): {full_msg.hex(' ').upper()}", "COM")
                    time.sleep(0.05)
                
                # 设置脉冲数 (寄存器 0x05)
                data = struct.pack('>BBHH', 0x01, 0x06, 0x05, move_pulse)
                crc = self.calculate_crc(data)
                full_msg = data + struct.pack('<H', crc)
                conn.write(full_msg)
                self.log(f"Motor {axis_name} Segment {segment_num}: Set Pulse ({move_pulse}): {full_msg.hex(' ').upper()}", "COM")
                
                # 发送运行指令 (寄存器 0x02, 值 1)
                time.sleep(0.05)
                data = struct.pack('>BBHH', 0x01, 0x06, 0x02, 0x0001)
                crc = self.calculate_crc(data)
                full_msg = data + struct.pack('<H', crc)
                conn.write(full_msg)
                self.log(f"Motor {axis_name} Segment {segment_num}: Run", "COM")
                
                # 立即更新位置（预测值），供 wait_for_motor_arrival() 使用
                if direction == 1:
                    local_current += move_pulse
                else:
                    local_current -= move_pulse
                
                if axis_name == "X":
                    self.current_x_pulse = local_current
                else:
                    self.current_y_pulse = local_current
                
                # 如果还有剩余脉冲，等待当前段移动完成后再发送下一段
                remaining -= move_pulse
                if remaining > 0:
                    self.wait_for_segment_complete(conn, axis_name)
            
        except Exception as e:
            self.log(f"Motor {axis_name} Command Error: {e}", "ERR")

    def wait_for_segment_complete(self, conn, axis_name=""):
        """
        等待电机当前段移动完成
        使用双重判断：运行状态(0x02) + 位置变化(0x18)
        
        :param conn: 串口连接
        :param axis_name: 轴名称 ("X" 或 "Y")
        """
        if not conn or not conn.is_open:
            return
        
        POLL_INTERVAL = 0.5
        MAX_WAIT_TIME = 60
        start_time = time.time()
        last_position = None
        stable_count = 0
        
        target_position = self.current_x_pulse if axis_name == "X" else self.current_y_pulse
        
        self.log(f"Motor {axis_name}: Waiting for segment to complete (target: {target_position})...", "MOT")
        
        while True:
            if self.stop_requested or self.skip_item_requested:
                self.log(f"Motor {axis_name}: Wait interrupted by stop/skip request", "MOT")
                return
            
            elapsed = time.time() - start_time
            if elapsed >= MAX_WAIT_TIME:
                self.log(f"Motor {axis_name}: Segment wait timeout ({MAX_WAIT_TIME}s)", "WRN")
                return
            
            try:
                is_running = False
                current_position = None
                
                conn.reset_input_buffer()
                
                time.sleep(0.5)
                
                data = struct.pack('>BBHH', 0x01, 0x03, 0x02, 0x01)
                crc = self.calculate_crc(data)
                full_msg = data + struct.pack('<H', crc)
                conn.write(full_msg)
                
                time.sleep(0.3)
                
                if conn.in_waiting >= 7:
                    response = conn.read(7)
                    status = response[4]
                    if status == 1:
                        is_running = True
                
                time.sleep(0.2)
                
                conn.reset_input_buffer()
                data = struct.pack('>BBHH', 0x01, 0x03, 0x18, 0x02)
                crc = self.calculate_crc(data)
                full_msg = data + struct.pack('<H', crc)
                conn.write(full_msg)
                
                time.sleep(0.3)
                
                if conn.in_waiting >= 9:
                    response = conn.read(9)
                    current_position = int.from_bytes(response[3:7], 'big', signed=True)
                    
                    self.log(f"Motor {axis_name}: Position {current_position}, Target {target_position}, Running {is_running}", "MOT")
                    
                    if current_position == target_position:
                        self.log(f"Motor {axis_name}: Segment complete", "MOT")
                        return
                    
                    if last_position is not None and current_position == last_position and not is_running:
                        stable_count += 1
                        if stable_count >= 2:
                            self.log(f"Motor {axis_name}: Segment complete (stable)", "MOT")
                            return
                    else:
                        stable_count = 0
                    
                    last_position = current_position
                else:
                    self.log(f"Motor {axis_name}: No response from motor", "WRN")
                    
            except Exception as e:
                self.log(f"Motor {axis_name} Segment Wait Error: {e}", "ERR")
            
            time.sleep(POLL_INTERVAL)

    def send_motor_stop(self, conn, axis_name=""):
        """
        发送电机停止指令 (Modbus RTU)
        使用寄存器 0x03（停止），值为 1
        
        :param conn: 串口连接
        :param axis_name: 轴名称 ("X" 或 "Y")
        """
        if not conn or not conn.is_open:
            return
        
        try:
            # 发送停止指令 (寄存器 0x03, 值 1)
            data = struct.pack('>BBHH', 0x01, 0x06, 0x03, 0x0001)
            crc = self.calculate_crc(data)
            full_msg = data + struct.pack('<H', crc)
            conn.write(full_msg)
            self.log(f"Motor {axis_name} Stop: {full_msg.hex(' ').upper()}", "COM")
        except Exception as e:
            self.log(f"Motor {axis_name} Stop Error: {e}", "ERR")

    def read_motor_pulse(self, conn, axis_name=""):
        """
        读取电机当前脉冲位置 (Modbus RTU)
        读取寄存器 0x18，返回 4 字节脉冲数据
        
        :param conn: 串口连接
        :param axis_name: 轴名称 ("X" 或 "Y")
        :return: 当前脉冲位置，读取失败返回 None
        """
        if not conn or not conn.is_open:
            return None
        
        try:
            # 清空接收缓冲区
            conn.reset_input_buffer()
            
            # 发送读取命令 (功能码 0x03, 寄存器 0x18, 读取 2 个寄存器 = 4 字节)
            data = struct.pack('>BBHH', 0x01, 0x03, 0x18, 0x02)
            crc = self.calculate_crc(data)
            full_msg = data + struct.pack('<H', crc)
            conn.write(full_msg)
            self.log(f"Motor {axis_name} Query Pulse: {full_msg.hex(' ').upper()}", "COM")
            
            # 等待响应 (9字节：地址+功能码+字节数+4字节数据+2字节CRC)
            time.sleep(0.1)
            if conn.in_waiting >= 9:
                response = conn.read(9)
                # 解析响应：第3-6字节是脉冲数据（大端模式，4字节，有符号整数）
                pulse = int.from_bytes(response[3:7], 'big', signed=True)
                self.log(f"Motor {axis_name} Current Pulse: {pulse}", "MOT")
                return pulse
            else:
                self.log(f"Motor {axis_name} Query Pulse: No response", "WRN")
                return None
                
        except Exception as e:
            self.log(f"Motor {axis_name} Query Pulse Error: {e}", "ERR")
            return None

    def wait_for_motor_arrival(self, conn, target_pulse, axis_name=""):
        """
        等待电机移动到目标位置
        通过轮询读取寄存器 0x18 检测当前位置，直到到达目标或超时
        
        :param conn: 串口连接
        :param target_pulse: 目标脉冲数
        :param axis_name: 轴名称 ("X" 或 "Y")
        """
        if not conn or not conn.is_open:
            return
        
        POLL_INTERVAL = 0.5
        MAX_WAIT_TIME = 30
        start_time = time.time()
        
        self.log(f"Motor {axis_name}: Waiting for arrival at target {target_pulse}...", "MOT")
        
        while True:
            if self.stop_requested or self.skip_item_requested:
                self.log(f"Motor {axis_name}: Wait interrupted by stop/skip request", "MOT")
                return
            
            elapsed = time.time() - start_time
            if elapsed >= MAX_WAIT_TIME:
                self.log(f"Motor {axis_name}: Wait timeout ({MAX_WAIT_TIME}s) for target {target_pulse}", "WRN")
                return
            
            try:
                conn.reset_input_buffer()
                
                data = struct.pack('>BBHH', 0x01, 0x03, 0x18, 0x02)
                crc = self.calculate_crc(data)
                full_msg = data + struct.pack('<H', crc)
                conn.write(full_msg)
                
                time.sleep(0.5)
                
                if conn.in_waiting >= 9:
                    response = conn.read(9)
                    current_pulse = int.from_bytes(response[3:7], 'big', signed=True)
                    
                    if current_pulse == target_pulse:
                        self.log(f"Motor {axis_name}: Arrived at target {target_pulse}", "MOT")
                        return
                    else:
                        remaining = abs(target_pulse - current_pulse)
                        self.log(f"Motor {axis_name}: Moving... Position {current_pulse}, Target {target_pulse}, Remaining {remaining}", "MOT")
                else:
                    self.log(f"Motor {axis_name}: No response from motor", "WRN")
                    
            except Exception as e:
                self.log(f"Motor {axis_name} Wait Error: {e}", "ERR")
            
            time.sleep(POLL_INTERVAL)

    def calculate_crc(self, data):
        """计算 Modbus CRC16"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc

    # ==========================================
    # 辅助与生命周期管理分区
    # ==========================================
    def finish_test(self):
        """测试完成或被手动停止后的清理工作，重置界面状态。"""
        if self.timer_id:
            self.after_cancel(self.timer_id)
            self.timer_id = None
        
        # 重置循环测试相关变量
        self.loop_enabled = False
        self.total_rounds = 1
        self.current_round = 1
        
        # 测试完成后刷新运动控制页面的位置显示
        if hasattr(self, 'motion_control') and self.motion_control:
            self.after(100, self.motion_control.refresh_positions)
        
        self.update_ui_state("STANDBY")
        self.log("Test Finished/Stopped", "TEST")

    def pause_test(self):
        """暂停测试按钮的回调。设置请求标志并停止 UI 定时器。"""
        self.pause_requested = True
        if self.timer_id:
            self.after_cancel(self.timer_id)
            self.timer_id = None
        self.update_ui_state("PAUSED")
        self.log("Test Pause Requested (waiting for cycle to finish)", "TEST")

    def resume_test(self):
        """恢复测试按钮的回调。清除请求标志并重启 UI 定时器（如果需要）。"""
        # 检查是否是多键测试暂停
        if self.multi_key_pause_pending:
            self.multi_key_pause_pending = False  # 解除多键测试暂停
            self.log("Multi-key test resumed by user", "TEST")
            # 注意：多键测试的继续逻辑在 run_test_cycle 中处理
        else:
            # 普通暂停恢复
            self.pause_requested = False # 解除后台线程的阻塞
            settings = self.settings_source.get_current_state()
            if settings.get('test_mode') == 'time':
                self.run_timer_async()
            self.log("Test Resumed", "TEST")
        
        self.update_ui_state("TESTING")

    def stop_test(self):
        """
        停止测试按钮的回调。
        设置停止请求标志，发送电机停止命令，并确保暂停状态被解除。
        """
        self.stop_requested = True
        self.pause_requested = False  # 如果处于暂停状态，先解封线程使其能检测到停止标志并退出
        
        # 发送电机停止命令
        motor_x_conn = self.settings_source.get_serial_connection("X-Axis Motor")
        motor_y_conn = self.settings_source.get_serial_connection("Y-Axis Motor")
        
        if motor_x_conn and motor_x_conn.is_open:
            self.send_motor_stop(motor_x_conn, "X")
        
        if motor_y_conn and motor_y_conn.is_open:
            self.send_motor_stop(motor_y_conn, "Y")
        
        self.log("Test Stop Requested - Motors stopped", "TEST")

    def skip_to_next(self):
        """跳过当前测试项"""
        if self.is_running:
            self.skip_item_requested = True
            self.log("Skipping to next test item...", "TEST")
    
    def refresh_texts(self):
        """刷新界面文本（语言切换时调用）"""
        # 更新 LabelFrame 标题
        self.status_frame.config(text=tr("test_status_monitor"))

        # 更新按钮文本
        self.btn_start.config(text=tr("test_start"))
        self.btn_pause.config(text=tr("test_pause"))
        self.btn_skip.config(text=tr("test_skip"))
        self.btn_stop.config(text=tr("test_stop"))

        # 更新状态标签
        if self.is_running and not self.is_paused:
            self.lbl_status.config(text=tr("test_testing"))
        elif self.is_paused:
            self.lbl_status.config(text=tr("test_paused"))
        else:
            self.lbl_status.config(text=tr("test_current_state"))

        # 更新剩余显示（仅在待机状态下更新，运行中由其他逻辑控制）
        if not self.is_running:
            self.lbl_remaining.config(text=tr("test_remaining") + ": --")
