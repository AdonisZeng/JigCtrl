import tkinter as tk
from tkinter import ttk
from motion import MotionControlFrame
from settings import SettingsFrame
from test_control import TestControlFrame
from log import LogFrame
from motor_debug import MotorDebugFrame
from utils import StatusBar, Tooltip
from language import get_language_manager, tr

class JigCtrlApp(tk.Tk):
    """
    JigCtrlApp 类：应用程序的主窗口类，继承自 tk.Tk。
    负责初始化主界面、配置全局样式以及管理各个功能页签。
    """
    def __init__(self):
        super().__init__()
        # 初始化语言管理器
        self.lang_manager = get_language_manager()
        
        # 设置窗口标题
        self.title("JigCtrl - Remote Control Jig System")
        # 设置窗口初始大小
        self.geometry("1280x720")
        # 设置最小窗口大小
        self.minsize(1024, 600)
        
        # --- 1. 样式配置 ---
        self.configure_styles()

        # --- 2. 界面组件创建 ---
        self.create_widgets()
        
        # --- 3. 创建底部状态栏 ---
        self.status_bar = StatusBar(self, on_language_change=self.refresh_all_texts)
        
        # --- 4. 绑定窗口关闭事件 ---
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def configure_styles(self):
        """
        配置应用程序的全局 ttk 样式。
        设计一套现代化的 UI 配色方案。
        """
        style = ttk.Style(self)
        try:
            style.theme_use('clam') 
        except:
            pass
        
        # --- 颜色定义 ---
        COLORS = {
            'bg': "#f0f2f5",          # 浅灰蓝背景
            'card': "#ffffff",        # 白色卡片
            'primary': "#0078d4",     # 微软蓝
            'primary_hover': "#005a9e",
            'success': "#107c10",     # 办公绿
            'danger': "#d13438",      # 警告红
            'text': "#323130",        # 深灰文字
            'secondary_text': "#605e5c", # 次要文字
            'border': "#edebe9"       # 边框色
        }

        # 全局字体 - 使用更现代的字体
        default_font = ("Microsoft YaHei", 9)
        header_font = ("Microsoft YaHei", 10, "bold")
        
        # 1. 基础配置
        style.configure(".", font=default_font, background=COLORS['bg'], foreground=COLORS['text'])
        
        # 2. 框架样式
        style.configure("TFrame", background=COLORS['bg'])
        style.configure("Card.TFrame", background=COLORS['card'])
        
        # 3. 标签框架样式 (LabelFrame)
        style.configure("TLabelframe", background=COLORS['bg'], bordercolor=COLORS['border'], relief="flat")
        style.configure("TLabelframe.Label", background=COLORS['bg'], foreground=COLORS['primary'], font=header_font)
        
        # 4. 标签样式
        style.configure("TLabel", background=COLORS['bg'], foreground=COLORS['text'])
        style.configure("Header.TLabel", font=header_font, foreground=COLORS['primary'])
        style.configure("Secondary.TLabel", foreground=COLORS['secondary_text'], font=("Microsoft YaHei", 9))
        
        # 5. 按钮样式 (使用统一的 padding 而非 width)
        # 默认按钮
        style.configure("TButton", font=default_font, padding=(8, 4))
        
        # 强调按钮 (Primary)
        style.configure("Primary.TButton", font=default_font, foreground="white", background=COLORS['primary'])
        style.map("Primary.TButton", background=[('active', COLORS['primary_hover'])])
        
        # 成功按钮 (Success)
        style.configure("Success.TButton", font=default_font, foreground="white", background=COLORS['success'])
        style.map("Success.TButton", background=[('active', '#0f6b0f')])
        
        # 危险按钮 (Danger)
        style.configure("Danger.TButton", font=default_font, foreground="white", background=COLORS['danger'])
        style.map("Danger.TButton", background=[('active', '#c02b33')])
        
        # 方向控制按钮
        style.configure("Dir.TButton", font=("Microsoft YaHei", 11, "bold"), padding=12)
        
        # 6. 输入框和下拉框
        style.configure("TEntry", fieldbackground="white", bordercolor=COLORS['border'], lightcolor=COLORS['border'])
        style.configure("TCombobox", fieldbackground="white", background="white", arrowcolor=COLORS['primary'])
        
        # 7. 选项卡 (Notebook) 样式
        style.configure("TNotebook", background=COLORS['bg'], borderwidth=0)
        style.configure("TNotebook.Tab", font=default_font, padding=(15, 8), background=COLORS['border'])
        style.map("TNotebook.Tab", 
                  background=[("selected", COLORS['bg']), ("active", "#e1dfdd")],
                  foreground=[("selected", COLORS['primary'])])
        
        # 8. 进度条样式
        style.configure("TProgressbar", thickness=20, barcolor=COLORS['primary'], trackcolor=COLORS['border'])
        
        # 确保根窗口背景
        self.configure(background=COLORS['bg'])

    def create_widgets(self):
        """
        创建并组织主界面上的所有功能组件。
        使用 Notebook (页签) 控件来组织不同的功能模块。
        """
        # 创建主页签控件
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- 初始化功能页签 ---
        
        # 1. 日志页签 (最先初始化，以便其他页签可以调用其日志记录功能)
        self.tab_log = LogFrame(self.notebook)
        
        # 2. 参数设置页签 (先初始化，因为运动控制需要获取Y轴串口连接)
        self.tab_settings = SettingsFrame(self.notebook, log_callback=self.tab_log.add_log, on_motor_connect_callback=self.on_motor_connected)
        
        # 3. 运动控制页签 (传入设置页签引用，以便获取Y轴串口连接)
        self.tab_motion = MotionControlFrame(self.notebook, settings_source=self.tab_settings, log_callback=self.tab_log.add_log)
        
        # 4. 测试控制页签 (传入设置页签引用，以便读取配置信息)
        self.tab_test = TestControlFrame(self.notebook, settings_source=self.tab_settings, log_callback=self.tab_log.add_log)

        # 相互引用
        self.tab_settings.test_control = self.tab_test
        self.tab_test.motion_control = self.tab_motion

        # 5. 电机命令调试页签
        self.tab_motor_debug = MotorDebugFrame(self.notebook, log_callback=self.tab_log.add_log)

        # 将页签添加到 Notebook 中显示 (Motor Debug 在最右端)
        self.notebook.add(self.tab_motion, text=tr("tab_motion"))
        self.notebook.add(self.tab_settings, text=tr("tab_settings"))
        self.notebook.add(self.tab_test, text=tr("tab_test"))
        self.notebook.add(self.tab_log, text=tr("tab_log"))
        self.notebook.add(self.tab_motor_debug, text=tr("tab_debug"))

        # --- 5. 绑定快捷键 ---
        self.bind_shortcuts()
    
    def refresh_all_texts(self):
        """刷新所有界面文本"""
        # 更新页签标题
        self.notebook.tab(self.tab_motion, text=tr("tab_motion"))
        self.notebook.tab(self.tab_settings, text=tr("tab_settings"))
        self.notebook.tab(self.tab_test, text=tr("tab_test"))
        self.notebook.tab(self.tab_log, text=tr("tab_log"))
        self.notebook.tab(self.tab_motor_debug, text=tr("tab_debug"))
        
        # 刷新各页签的文本
        if hasattr(self.tab_motion, 'refresh_texts'):
            self.tab_motion.refresh_texts()
        if hasattr(self.tab_settings, 'refresh_texts'):
            self.tab_settings.refresh_texts()
        if hasattr(self.tab_test, 'refresh_texts'):
            self.tab_test.refresh_texts()
        if hasattr(self.tab_log, 'refresh_texts'):
            self.tab_log.refresh_texts()
        if hasattr(self.tab_motor_debug, 'refresh_texts'):
            self.tab_motor_debug.refresh_texts()

    def bind_shortcuts(self):
        """
        绑定全局快捷键。
        """
        # Ctrl+Z: 撤销 (仅在设置页签时有效)
        self.bind('<Control-z>', lambda e: self.tab_settings.undo_changes() if hasattr(self, 'tab_settings') else None)
        self.bind('<Control-Z>', lambda e: self.tab_settings.undo_changes() if hasattr(self, 'tab_settings') else None)
        
        # Ctrl+Y: 重做 (仅在设置页签时有效)
        self.bind('<Control-y>', lambda e: self.tab_settings.redo_changes() if hasattr(self, 'tab_settings') else None)
        self.bind('<Control-Y>', lambda e: self.tab_settings.redo_changes() if hasattr(self, 'tab_settings') else None)
        
        # Ctrl+S: 保存配置
        self.bind('<Control-s>', lambda e: self.on_save_config())
        self.bind('<Control-S>', lambda e: self.on_save_config())
        
        # F5: 刷新状态
        self.bind('<F5>', lambda e: self.on_refresh())
        
        # Esc: 关闭当前对话框或取消操作
        self.bind('<Escape>', lambda e: self.on_escape())

    def on_save_config(self):
        """保存配置快捷键"""
        if hasattr(self, 'tab_settings'):
            self.tab_settings.save_config_to_file()
            self.status_bar.set_status("Configuration saved", 2000)

    def on_motor_connected(self):
        """电机串口连接成功后的回调，刷新位置显示并获取回原点速度"""
        if hasattr(self, 'tab_motion'):
            # 延迟 200ms 后刷新位置，等待串口稳定
            self.after(200, self.tab_motion.refresh_positions)
            # 延迟 300ms 后获取回原点速度
            self.after(300, self.tab_motion.on_get_homing_speed)

    def on_refresh(self):
        """刷新状态快捷键"""
        self.status_bar.set_status("Status refreshed", 2000)
        # 可以在这里添加其他刷新逻辑

    def on_escape(self):
        """Esc 键处理"""
        # 可以在这里添加 Esc 键的处理逻辑
        pass

    def on_closing(self):
        """
        窗口关闭时的回调函数。
        在关闭前自动保存配置。
        """
        # 保存设置页签的配置
        self.tab_settings.save_config_to_file()
        # 关闭窗口
        self.destroy()

# --- 程序入口 ---
if __name__ == "__main__":
    app = JigCtrlApp()
    app.mainloop()
