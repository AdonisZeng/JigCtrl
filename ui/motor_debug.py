import tkinter as tk
from tkinter import ttk, scrolledtext
import serial
import serial.tools.list_ports
import struct
from core.language import tr


class MotorDebugFrame(ttk.Frame):
    """
    MotorDebugFrame 类：电机命令调试界面，继承自 ttk.Frame。
    提供串口连接、Modbus-RTU 指令编辑发送、以及响应接收显示功能。
    """

    def __init__(self, master=None, log_callback=None):
        super().__init__(master)
        self.log = log_callback if log_callback else print
        self.serial_conn = None
        self.is_open = False

        self.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.create_widgets()

    def create_widgets(self):
        """创建调试界面的所有组件"""

        # --- 左侧：带滚动条的串口配置和快速指令区 ---
        left_container = ttk.Frame(self)
        left_container.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10), expand=False)

        # 创建 Canvas 和滚动条
        left_canvas = tk.Canvas(left_container, background="#f0f2f5", highlightthickness=0)
        left_scrollbar = ttk.Scrollbar(left_container, orient="vertical", command=left_canvas.yview)
        left_canvas.configure(yscrollcommand=left_scrollbar.set)

        left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 在 Canvas 中创建可滚动的 Frame
        left_frame = ttk.Frame(left_canvas)
        left_canvas_window = left_canvas.create_window((0, 0), window=left_frame, anchor="nw", width=360)

        # 绑定滚动事件
        def on_frame_configure(event):
            left_canvas.configure(scrollregion=left_canvas.bbox("all"))

        def on_canvas_configure(event):
            left_canvas.itemconfig(left_canvas_window, width=event.width)

        def on_mousewheel(event):
            left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        left_frame.bind("<Configure>", on_frame_configure)
        left_canvas.bind("<Configure>", on_canvas_configure)
        left_canvas.bind_all("<MouseWheel>", on_mousewheel)

        self.left_canvas = left_canvas
        self.create_serial_config(left_frame)
        self.create_quick_commands(left_frame)
        self.create_manual_command(left_frame)

        # --- 右侧：日志显示区 ---
        right_frame = ttk.Frame(self)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.create_log_area(right_frame)

    def create_serial_config(self, parent):
        """创建串口配置区域"""
        self.serial_frame = ttk.LabelFrame(parent, text=tr("debug_serial_connection"), padding=15)
        self.serial_frame.pack(fill=tk.X, pady=5)

        grid_frame = ttk.Frame(self.serial_frame)
        grid_frame.pack(fill=tk.X)
        grid_frame.columnconfigure(1, weight=1)

        # 端口选择
        self.lbl_port = ttk.Label(grid_frame, text=tr("debug_port_label"))
        self.lbl_port.grid(row=0, column=0, sticky=tk.W, pady=5)
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(grid_frame, textvariable=self.port_var, state="readonly")
        self.port_combo.grid(row=0, column=1, sticky=tk.EW, padx=10, pady=5)
        self.port_combo.bind('<Button-1>', self.refresh_ports)

        # 波特率
        self.lbl_baud = ttk.Label(grid_frame, text=tr("debug_baud_label"))
        self.lbl_baud.grid(row=1, column=0, sticky=tk.W, pady=5)
        self.baud_var = tk.IntVar(value=9600)
        ttk.Combobox(grid_frame, textvariable=self.baud_var,
                     values=[9600, 19200, 38400, 115200], state="readonly").grid(row=1, column=1, sticky=tk.EW, padx=10, pady=5)

        # 控制按钮
        btn_frame = ttk.Frame(self.serial_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        self.btn_open = ttk.Button(btn_frame, text=tr("debug_open_port"), style="Primary.TButton", command=self.toggle_port)
        self.btn_open.pack(side=tk.LEFT, padx=5)
        
        self.btn_get_all = ttk.Button(btn_frame, text=tr("debug_get_all_params"), command=self.get_all_parameters)
        self.btn_get_all.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.device_addr = 0x01
        self.refresh_ports(initial=True)

    def create_quick_commands(self, parent):
        """创建快速指令按钮区域"""
        self.quick_frame = ttk.LabelFrame(parent, text=tr("debug_quick_commands"), padding=15)
        self.quick_frame.pack(fill=tk.X, pady=5)

        # 1. 运行控制 (Row 1)
        row1 = ttk.Frame(self.quick_frame)
        row1.pack(fill=tk.X, pady=5)

        self.btn_run = ttk.Button(row1, text=tr("debug_run_btn"), width=8, command=lambda: self.send_quick_command(0x02, 1))
        self.btn_run.pack(side=tk.LEFT, padx=2)
        self.btn_pause = ttk.Button(row1, text=tr("debug_pause_btn"), width=8, command=lambda: self.send_quick_command(0x02, 0))
        self.btn_pause.pack(side=tk.LEFT, padx=2)
        self.btn_stop = ttk.Button(row1, text=tr("debug_stop_btn"), width=8, style="Danger.TButton", command=lambda: self.send_quick_command(0x03, 1))
        self.btn_stop.pack(side=tk.LEFT, padx=2)
        self.btn_status = ttk.Button(row1, text=tr("debug_status_btn"), width=8, command=lambda: self.send_query_command(0x02))
        self.btn_status.pack(side=tk.RIGHT, padx=2)

        # 2. 速度和方向 (Row 2)
        row2 = ttk.Frame(self.quick_frame)
        row2.pack(fill=tk.X, pady=10)

        self.lbl_speed = ttk.Label(row2, text=tr("debug_speed_label"))
        self.lbl_speed.pack(side=tk.LEFT)
        self.speed_var = tk.IntVar(value=100)
        ttk.Entry(row2, textvariable=self.speed_var, width=6).pack(side=tk.LEFT, padx=5)
        self.btn_set_speed = ttk.Button(row2, text=tr("debug_set_btn"), width=5, command=self.set_speed)
        self.btn_set_speed.pack(side=tk.LEFT)

        self.lbl_dir = ttk.Label(row2, text=tr("debug_dir_label"))
        self.lbl_dir.pack(side=tk.LEFT, padx=(15, 0))
        self.dir_var = tk.IntVar(value=1)
        ttk.Combobox(row2, textvariable=self.dir_var, values=[0, 1], state="readonly", width=3).pack(side=tk.LEFT, padx=5)
        self.btn_set_dir = ttk.Button(row2, text=tr("debug_set_btn"), width=5, command=lambda: self.send_quick_command(0x01, self.dir_var.get()))
        self.btn_set_dir.pack(side=tk.LEFT)

        # 3. 行程设置 (Group)
        travel_frame = tk.Frame(self.quick_frame, bg="#f8f9fa", padx=10, pady=10, highlightthickness=1, highlightbackground="#edebe9")
        travel_frame.pack(fill=tk.X, pady=5)

        # Revolutions
        rev_row = ttk.Frame(travel_frame)
        rev_row.pack(fill=tk.X, pady=2)
        self.lbl_rev = ttk.Label(rev_row, text=tr("debug_rev_label"), background="#f8f9fa")
        self.lbl_rev.pack(side=tk.LEFT)
        self.rev_var = tk.IntVar(value=1)
        ttk.Entry(rev_row, textvariable=self.rev_var, width=6, background="white").pack(side=tk.LEFT, padx=5)
        self.btn_set_rev = ttk.Button(rev_row, text=tr("debug_set_btn"), width=5, command=lambda: self.send_quick_command(0x06, self.rev_var.get()))
        self.btn_set_rev.pack(side=tk.RIGHT, padx=2)
        self.btn_get_rev = ttk.Button(rev_row, text=tr("debug_get_btn"), width=5, command=lambda: self.send_query_command(0x06))
        self.btn_get_rev.pack(side=tk.RIGHT, padx=2)

        # Angle
        angle_row = ttk.Frame(travel_frame)
        angle_row.pack(fill=tk.X, pady=2)
        self.lbl_angle = ttk.Label(angle_row, text=tr("debug_angle_label"), background="#f8f9fa")
        self.lbl_angle.pack(side=tk.LEFT)
        self.angle_var = tk.IntVar(value=0)
        ttk.Entry(angle_row, textvariable=self.angle_var, width=6, background="white").pack(side=tk.LEFT, padx=5)
        self.btn_set_angle = ttk.Button(angle_row, text=tr("debug_set_btn"), width=5, command=self.set_angle)
        self.btn_set_angle.pack(side=tk.RIGHT, padx=2)
        self.btn_get_angle = ttk.Button(angle_row, text=tr("debug_get_btn"), width=5, command=lambda: self.send_query_command(0x07))
        self.btn_get_angle.pack(side=tk.RIGHT, padx=2)

        # Pulse
        pulse_row = ttk.Frame(travel_frame)
        pulse_row.pack(fill=tk.X, pady=2)
        self.lbl_pulse = ttk.Label(pulse_row, text=tr("debug_pulse_label"), background="#f8f9fa")
        self.lbl_pulse.pack(side=tk.LEFT)
        self.pulse_var = tk.IntVar(value=0)
        ttk.Entry(pulse_row, textvariable=self.pulse_var, width=6, background="white").pack(side=tk.LEFT, padx=5)
        self.btn_set_pulse = ttk.Button(pulse_row, text=tr("debug_set_btn"), width=5, command=lambda: self.send_quick_command(0x05, self.pulse_var.get()))
        self.btn_set_pulse.pack(side=tk.RIGHT, padx=2)
        self.btn_get_pulse = ttk.Button(pulse_row, text=tr("debug_get_btn"), width=5, command=lambda: self.send_query_command(0x05))
        self.btn_get_pulse.pack(side=tk.RIGHT, padx=2)

    def create_manual_command(self, parent):
        """创建手动指令输入区域"""
        self.manual_frame = ttk.LabelFrame(parent, text=tr("debug_manual_hex"), padding=15)
        self.manual_frame.pack(fill=tk.X, pady=5)

        self.cmd_var = tk.StringVar()
        ttk.Entry(self.manual_frame, textvariable=self.cmd_var).pack(fill=tk.X, pady=(0, 10))

        ex_frame = ttk.Frame(self.manual_frame)
        ex_frame.pack(fill=tk.X)
        self.btn_ex_run = ttk.Button(ex_frame, text=tr("debug_ex_run"), width=8, command=lambda: self.set_manual_cmd("01 06 00 02 00 01"))
        self.btn_ex_run.pack(side=tk.LEFT, padx=2)
        self.btn_ex_stop = ttk.Button(ex_frame, text=tr("debug_ex_stop"), width=8, command=lambda: self.set_manual_cmd("01 06 00 03 00 01"))
        self.btn_ex_stop.pack(side=tk.LEFT, padx=2)
        self.btn_ex_query = ttk.Button(ex_frame, text=tr("debug_ex_query"), width=8, command=lambda: self.set_manual_cmd("01 03 00 04 00 01"))
        self.btn_ex_query.pack(side=tk.LEFT, padx=2)

        # 发送按钮
        self.btn_send = ttk.Button(self.manual_frame, text=tr("debug_send"), style="Primary.TButton", command=self.send_manual_command)
        self.btn_send.pack(fill=tk.X, pady=(15, 0))

    def create_log_area(self, parent):
        """创建日志显示区域"""
        self.log_frame = ttk.LabelFrame(parent, text=tr("debug_comm_log"), padding=15)
        self.log_frame.pack(fill=tk.BOTH, expand=True)

        # 工具栏
        toolbar = ttk.Frame(self.log_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        # 显示选项
        self.show_hex_var = tk.BooleanVar(value=True)
        self.chk_hex = ttk.Checkbutton(toolbar, text=tr("debug_hex"), variable=self.show_hex_var)
        self.chk_hex.pack(side=tk.LEFT, padx=5)
        self.show_ascii_var = tk.BooleanVar(value=False)
        self.chk_ascii = ttk.Checkbutton(toolbar, text=tr("debug_ascii"), variable=self.show_ascii_var)
        self.chk_ascii.pack(side=tk.LEFT, padx=5)

        self.btn_clear = ttk.Button(toolbar, text=tr("debug_clear"), width=12, command=self.clear_log)
        self.btn_clear.pack(side=tk.RIGHT, padx=5)
        self.btn_copy = ttk.Button(toolbar, text=tr("debug_copy"), width=8, command=self.copy_selected)
        self.btn_copy.pack(side=tk.RIGHT, padx=5)

        # 日志文本框
        log_container = ttk.Frame(self.log_frame, style="Card.TFrame")
        log_container.pack(fill=tk.BOTH, expand=True)

        self.log_area = scrolledtext.ScrolledText(
            log_container, 
            state='disabled', 
            height=20,
            font=("Cambria", 10),
            bg="#2b2b2b",
            fg="#d1d1d1",
            highlightthickness=0,
            borderwidth=0
        )
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.log_area.tag_config("sent", foreground="#3498db")    # 蓝色
        self.log_area.tag_config("received", foreground="#2ecc71") # 绿色
        self.log_area.tag_config("error", foreground="#e74c3c", font=("Cambria", 10, "bold")) # 红色
        self.log_area.tag_config("info", foreground="#95a5a6")    # 灰色

    def refresh_ports(self, event=None, initial=False):
        """
        刷新可用串口列表

        :param event: tkinter 事件对象
        :param initial: 是否为初始化调用，初始时不自动选择第一个端口
        """
        ports = sorted([port.device for port in serial.tools.list_ports.comports()])
        self.port_combo['values'] = ports if ports else []

        if initial:
            # 初始化时清空选择，等待用户手动选择
            self.port_var.set('')
        elif not self.port_var.get() and ports:
            # 非初始化时，如果没有选中端口，则选择第一个
            self.port_combo.set(ports[0])

    def toggle_port(self):
        """打开或关闭串口"""
        if self.is_open:
            self.close_port()
        else:
            self.open_port()

    def open_port(self):
        """打开串口连接"""
        port = self.port_var.get()
        if not port:
            self.add_log("Error: No port selected", "error")
            return

        try:
            parity_map = {
                'None': serial.PARITY_NONE,
                'Even': serial.PARITY_EVEN,
                'Odd': serial.PARITY_ODD,
                'Mark': serial.PARITY_MARK,
                'Space': serial.PARITY_SPACE
            }

            self.serial_conn = serial.Serial(
                port=port,
                baudrate=self.baud_var.get(),
                bytesize=self.data_bits_var.get(),
                stopbits=self.stop_bits_var.get(),
                parity=parity_map.get(self.parity_var.get(), serial.PARITY_NONE),
                timeout=0.5
            )

            self.is_open = True
            self.btn_open.config(text=tr("debug_close_port"))
            self.add_log(f"Port {port} opened successfully", "info")
            self.log(f"Motor Debug: Port {port} opened", "SER")

        except Exception as e:
            self.add_log(f"Error opening port: {e}", "error")
            self.serial_conn = None

    def close_port(self):
        """关闭串口连接"""
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.close()
            except Exception as e:
                self.add_log(f"Error closing port: {e}", "error")

        self.serial_conn = None
        self.is_open = False
        self.btn_open.config(text=tr("debug_open_port"))
        self.add_log("Port closed", "info")
        self.log("Motor Debug: Port closed", "SER")

    def calculate_crc(self, data):
        """计算 Modbus CRC16 校验码"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc

    def send_quick_command(self, register, value):
        """发送快速设置指令 (功能码 06)"""
        if not self.is_open or not self.serial_conn:
            self.add_log("Error: Port not open", "error")
            return

        try:
            data = struct.pack('>BBHH', self.device_addr, 0x06, register, value)
            crc = self.calculate_crc(data)
            crc_low = crc & 0xFF
            crc_high = (crc >> 8) & 0xFF
            command = data + bytes([crc_low, crc_high])

            self.send_and_receive(command)

        except Exception as e:
            self.add_log(f"Error sending command: {e}", "error")

    def send_query_command(self, register):
        """
        发送查询指令 (功能码 03)

        :param register: 寄存器地址
        """
        if not self.is_open or not self.serial_conn:
            self.add_log("Error: Port not open", "error")
            return

        try:
            data = struct.pack('>BBHH', self.device_addr, 0x03, register, 1)
            crc = self.calculate_crc(data)
            crc_low = crc & 0xFF
            crc_high = (crc >> 8) & 0xFF
            command = data + bytes([crc_low, crc_high])

            # 保存当前查询的寄存器地址，用于响应处理
            self.pending_query_register = register
            self.send_and_receive(command)

        except Exception as e:
            self.add_log(f"Error sending query: {e}", "error")

    def get_all_parameters(self):
        """
        获取所有电机参数并更新到输入框
        依次查询：方向、速度、脉冲、圈数、角度、加减速系数、脱机使能
        """
        if not self.is_open or not self.serial_conn:
            self.add_log("Error: Port not open", "error")
            return

        self.add_log("Starting to get all parameters...", "info")

        # 定义要查询的寄存器列表
        registers = [
            (0x01, "Direction"),
            (0x04, "Speed"),
            (0x05, "Pulse"),
            (0x06, "Revolutions"),
            (0x07, "Angle"),
            (0x0E, "Acceleration"),
            (0x09, "Enable Status"),
            (0x02, "Run Status")
        ]

        # 使用索引来跟踪当前查询的寄存器
        self._get_all_registers = registers
        self._get_all_index = 0

        # 开始依次查询
        self._query_next_register()

    def _query_next_register(self):
        """查询下一个寄存器"""
        if not hasattr(self, '_get_all_registers') or not hasattr(self, '_get_all_index'):
            return

        if self._get_all_index >= len(self._get_all_registers):
            # 所有寄存器查询完成
            self.add_log("All parameters retrieved successfully!", "info")
            delattr(self, '_get_all_registers')
            delattr(self, '_get_all_index')
            return

        register, name = self._get_all_registers[self._get_all_index]

        # 发送查询命令
        try:
            data = struct.pack('>BBHH', self.device_addr, 0x03, register, 1)
            crc = self.calculate_crc(data)
            crc_low = crc & 0xFF
            crc_high = (crc >> 8) & 0xFF
            command = data + bytes([crc_low, crc_high])

            # 标记这是批量查询的一部分
            self._is_batch_query = True
            self.pending_query_register = register

            # 清空接收缓冲区
            self.serial_conn.reset_input_buffer()

            # 发送指令
            self.serial_conn.write(command)

            # 显示发送的数据
            hex_str = ' '.join(f'{b:02X}' for b in command)
            self.add_log(f"[TX] {hex_str} (Get {name})", "sent")

            # 等待响应
            self.after(150, lambda: self._read_batch_response())

        except Exception as e:
            self.add_log(f"Error querying {name}: {e}", "error")
            self._get_all_index += 1
            self.after(100, self._query_next_register)

    def _read_batch_response(self):
        """读取批量查询的响应"""
        if not self.serial_conn or not self.serial_conn.is_open:
            self._get_all_index += 1
            self.after(100, self._query_next_register)
            return

        try:
            if self.serial_conn.in_waiting > 0:
                response = self.serial_conn.read(self.serial_conn.in_waiting)

                # 显示接收的数据
                hex_str = ' '.join(f'{b:02X}' for b in response)
                display_str = f"[RX] {hex_str}"

                # 解析响应并更新输入框
                data_value = None
                if len(response) >= 5:
                    if response[1] & 0x80:
                        display_str += "  [ERROR RESPONSE]"
                    elif response[1] == 0x03 and len(response) >= 5:
                        byte_count = response[2]
                        if len(response) >= 3 + byte_count + 2:
                            data_value = int.from_bytes(response[3:3+byte_count], 'big')
                            display_str += f"  [Value: {data_value}]"
                            # 更新输入框
                            self.update_input_value(data_value)

                self.add_log(display_str, "received")
            else:
                self.add_log("[RX] No response (timeout)", "info")

        except Exception as e:
            self.add_log(f"Error reading response: {e}", "error")

        # 查询下一个寄存器
        self._get_all_index += 1
        self.after(100, self._query_next_register)

    def set_speed(self):
        """设置速度"""
        speed = self.speed_var.get()
        if 1 <= speed <= 800:
            self.send_quick_command(0x04, speed)
        else:
            self.add_log("Error: Speed must be 1-800", "error")

    def set_angle(self):
        """设置角度 (转换为脉冲: 1圈=360度=1600脉冲)"""
        angle = self.angle_var.get()
        if 0 <= angle <= 360:
            pulse = int(angle * 1600 / 360)
            self.send_quick_command(0x07, pulse)
        else:
            self.add_log("Error: Angle must be 0-360", "error")

    def set_manual_cmd(self, cmd_str):
        """设置手动指令示例"""
        self.cmd_var.set(cmd_str)

    def send_manual_command(self):
        """发送手动输入的指令"""
        if not self.is_open or not self.serial_conn:
            self.add_log("Error: Port not open", "error")
            return

        cmd_str = self.cmd_var.get().strip()
        if not cmd_str:
            self.add_log("Error: Empty command", "error")
            return

        try:
            # 解析十六进制字符串
            hex_bytes = cmd_str.replace(' ', '').replace('0x', '').replace(',', '')
            if len(hex_bytes) % 2 != 0:
                hex_bytes = '0' + hex_bytes

            command = bytes.fromhex(hex_bytes)

            # 如果指令长度不足6字节，添加CRC
            if len(command) == 6:
                crc = self.calculate_crc(command)
                crc_low = crc & 0xFF
                crc_high = (crc >> 8) & 0xFF
                command = command + bytes([crc_low, crc_high])
                self.add_log(f"Auto-added CRC: {crc_low:02X} {crc_high:02X}", "info")

            self.send_and_receive(command)

        except ValueError as e:
            self.add_log(f"Error: Invalid hex format - {e}", "error")
        except Exception as e:
            self.add_log(f"Error sending manual command: {e}", "error")

    def send_and_receive(self, command):
        """发送指令并接收响应"""
        try:
            # 清空接收缓冲区
            self.serial_conn.reset_input_buffer()

            # 发送指令
            self.serial_conn.write(command)

            # 显示发送的数据
            hex_str = ' '.join(f'{b:02X}' for b in command)
            display_str = f"[TX] {hex_str}"
            if self.show_ascii_var.get():
                ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in command)
                display_str += f"  |  {ascii_str}"
            self.add_log(display_str, "sent")

            # 等待并接收响应
            self.after(100, lambda: self.read_response())

        except Exception as e:
            self.add_log(f"Error in communication: {e}", "error")

    def read_response(self):
        """读取串口响应"""
        if not self.serial_conn or not self.serial_conn.is_open:
            return

        try:
            # 检查是否有数据可读
            if self.serial_conn.in_waiting > 0:
                response = self.serial_conn.read(self.serial_conn.in_waiting)

                # 显示接收的数据
                hex_str = ' '.join(f'{b:02X}' for b in response)
                display_str = f"[RX] {hex_str}"

                # 解析响应
                data_value = None
                if len(response) >= 5:
                    if response[1] & 0x80:
                        display_str += "  [ERROR RESPONSE]"
                    elif response[1] == 0x03 and len(response) >= 5:
                        byte_count = response[2]
                        if len(response) >= 3 + byte_count + 2:
                            data_value = int.from_bytes(response[3:3+byte_count], 'big')
                            display_str += f"  [Value: {data_value}]"

                            # 更新对应输入框的值
                            self.update_input_value(data_value)

                if self.show_ascii_var.get():
                    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in response)
                    display_str += f"  |  {ascii_str}"

                self.add_log(display_str, "received")

                # 清除待处理的查询寄存器
                if hasattr(self, 'pending_query_register'):
                    delattr(self, 'pending_query_register')
            else:
                # 再等待一下，有些设备响应较慢
                self.after(100, lambda: self.read_delayed())

        except Exception as e:
            self.add_log(f"Error reading response: {e}", "error")

    def read_delayed(self):
        """延迟读取响应"""
        if not self.serial_conn or not self.serial_conn.is_open:
            return

        try:
            if self.serial_conn.in_waiting > 0:
                response = self.serial_conn.read(self.serial_conn.in_waiting)
                hex_str = ' '.join(f'{b:02X}' for b in response)
                display_str = f"[RX] {hex_str}"

                if response[1] & 0x80:
                    display_str += "  [ERROR RESPONSE]"

                if self.show_ascii_var.get():
                    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in response)
                    display_str += f"  |  {ascii_str}"

                self.add_log(display_str, "received")
            else:
                self.add_log("[RX] No response (timeout)", "info")

        except Exception as e:
            self.add_log(f"Error reading delayed response: {e}", "error")

    def update_input_value(self, value):
        """
        根据查询的寄存器地址，更新对应的输入框值

        :param value: 从设备读取到的值
        """
        if not hasattr(self, 'pending_query_register'):
            return

        register = self.pending_query_register

        # 根据寄存器地址更新对应的变量
        if register == 0x01:  # 方向
            self.dir_var.set(value)
            self.add_log(f"  -> Direction updated to: {value} ({'CW' if value == 1 else 'CCW'})", "info")
        elif register == 0x04:  # 速度
            self.speed_var.set(value)
            self.add_log(f"  -> Speed updated to: {value}", "info")
        elif register == 0x05:  # 脉冲
            self.pulse_var.set(value)
            self.add_log(f"  -> Pulse updated to: {value}", "info")
        elif register == 0x06:  # 圈数
            self.rev_var.set(value)
            self.add_log(f"  -> Revolutions updated to: {value}", "info")
        elif register == 0x07:  # 角度
            # 将脉冲转换为角度显示 (1圈=360度=1600脉冲)
            angle = int(value * 360 / 1600)
            self.angle_var.set(angle)
            self.add_log(f"  -> Angle updated to: {angle}° (pulse: {value})", "info")
        elif register == 0x0E:  # 加减速系数
            self.accel_var.set(value)
            self.add_log(f"  -> Acceleration coefficient updated to: {value}", "info")
        elif register == 0x02:  # 运行状态
            status_str = "Running" if value == 1 else "Stopped"
            self.add_log(f"  -> Run status: {status_str} ({value})", "info")
        elif register == 0x09:  # 脱机使能
            self.enable_var.set(value)
            status_str = "Free (脱机)" if value == 1 else "Lock (锁定)"
            self.add_log(f"  -> Enable status updated to: {value} ({status_str})", "info")

    def add_log(self, message, tag="info"):
        """添加日志到显示区域"""
        timestamp = self.get_timestamp()
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def get_timestamp(self):
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]

    def clear_log(self):
        """清空日志"""
        self.log_area.config(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state='disabled')

    def copy_selected(self):
        """复制选中的内容到剪贴板"""
        try:
            selected = self.log_area.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.clipboard_clear()
            self.clipboard_append(selected)
        except tk.TclError:
            pass
    
    def refresh_texts(self):
        """刷新界面文本（语言切换时调用）"""
        # 更新 LabelFrame 标题
        if hasattr(self, 'serial_frame'):
            self.serial_frame.config(text=tr("debug_serial_connection"))
        if hasattr(self, 'quick_frame'):
            self.quick_frame.config(text=tr("debug_quick_commands"))
        if hasattr(self, 'manual_frame'):
            self.manual_frame.config(text=tr("debug_manual_hex"))
        if hasattr(self, 'log_frame'):
            self.log_frame.config(text=tr("debug_comm_log"))

        # 更新串口配置区域标签
        if hasattr(self, 'lbl_port'):
            self.lbl_port.config(text=tr("debug_port_label"))
        if hasattr(self, 'lbl_baud'):
            self.lbl_baud.config(text=tr("debug_baud_label"))

        # 更新按钮文本
        if hasattr(self, 'btn_open'):
            self.btn_open.config(text=tr("debug_close_port") if self.is_open else tr("debug_open_port"))
        if hasattr(self, 'btn_get_all'):
            self.btn_get_all.config(text=tr("debug_get_all_params"))

        # 更新快速指令区域按钮
        if hasattr(self, 'btn_run'):
            self.btn_run.config(text=tr("debug_run_btn"))
        if hasattr(self, 'btn_pause'):
            self.btn_pause.config(text=tr("debug_pause_btn"))
        if hasattr(self, 'btn_stop'):
            self.btn_stop.config(text=tr("debug_stop_btn"))
        if hasattr(self, 'btn_status'):
            self.btn_status.config(text=tr("debug_status_btn"))

        # 更新速度和方向区域
        if hasattr(self, 'lbl_speed'):
            self.lbl_speed.config(text=tr("debug_speed_label"))
        if hasattr(self, 'btn_set_speed'):
            self.btn_set_speed.config(text=tr("debug_set_btn"))
        if hasattr(self, 'lbl_dir'):
            self.lbl_dir.config(text=tr("debug_dir_label"))
        if hasattr(self, 'btn_set_dir'):
            self.btn_set_dir.config(text=tr("debug_set_btn"))

        # 更新行程设置区域
        if hasattr(self, 'lbl_rev'):
            self.lbl_rev.config(text=tr("debug_rev_label"))
        if hasattr(self, 'btn_set_rev'):
            self.btn_set_rev.config(text=tr("debug_set_btn"))
        if hasattr(self, 'btn_get_rev'):
            self.btn_get_rev.config(text=tr("debug_get_btn"))

        if hasattr(self, 'lbl_angle'):
            self.lbl_angle.config(text=tr("debug_angle_label"))
        if hasattr(self, 'btn_set_angle'):
            self.btn_set_angle.config(text=tr("debug_set_btn"))
        if hasattr(self, 'btn_get_angle'):
            self.btn_get_angle.config(text=tr("debug_get_btn"))

        if hasattr(self, 'lbl_pulse'):
            self.lbl_pulse.config(text=tr("debug_pulse_label"))
        if hasattr(self, 'btn_set_pulse'):
            self.btn_set_pulse.config(text=tr("debug_set_btn"))
        if hasattr(self, 'btn_get_pulse'):
            self.btn_get_pulse.config(text=tr("debug_get_btn"))

        # 更新手动指令区域
        if hasattr(self, 'btn_ex_run'):
            self.btn_ex_run.config(text=tr("debug_ex_run"))
        if hasattr(self, 'btn_ex_stop'):
            self.btn_ex_stop.config(text=tr("debug_ex_stop"))
        if hasattr(self, 'btn_ex_query'):
            self.btn_ex_query.config(text=tr("debug_ex_query"))
        if hasattr(self, 'btn_send'):
            self.btn_send.config(text=tr("debug_send"))

        # 更新日志区域
        if hasattr(self, 'chk_hex'):
            self.chk_hex.config(text=tr("debug_hex"))
        if hasattr(self, 'chk_ascii'):
            self.chk_ascii.config(text=tr("debug_ascii"))
        if hasattr(self, 'btn_clear'):
            self.btn_clear.config(text=tr("debug_clear"))
        if hasattr(self, 'btn_copy'):
            self.btn_copy.config(text=tr("debug_copy"))
