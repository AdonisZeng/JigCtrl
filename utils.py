import tkinter as tk
from tkinter import ttk
import threading
import time
from language import get_language_manager, tr


class Tooltip:
    """
    Tooltip 类：为控件添加悬停提示信息。
    """
    def __init__(self, widget, text):
        """
        初始化 Tooltip。
        
        :param widget: 需要添加提示的控件
        :param text: 提示文本内容
        """
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind('<Enter>', self.show_tooltip)
        self.widget.bind('<Leave>', self.hide_tooltip)
        self.widget.bind('<Motion>', self.move_tooltip)
    
    def show_tooltip(self, event):
        """显示提示窗口"""
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            background="#ffffe0",
            foreground="#333333",
            relief="solid",
            borderwidth=1,
            font=("Microsoft YaHei", 9)
        )
        label.pack()
    
    def hide_tooltip(self, event):
        """隐藏提示窗口"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
    
    def move_tooltip(self, event):
        """移动提示窗口跟随鼠标"""
        if self.tooltip_window:
            x = event.x_root + 15
            y = event.y_root + 15
            self.tooltip_window.wm_geometry(f"+{x}+{y}")


class ProgressBar:
    """
    ProgressBar 类：创建一个可复用的进度条组件。
    """
    def __init__(self, parent, text="Processing...", mode="determinate"):
        """
        初始化进度条。
        
        :param parent: 父容器
        :param text: 进度条上方显示的文本
        :param mode: 进度条模式 ('determinate' 或 'indeterminate')
        """
        self.frame = ttk.LabelFrame(parent, text=text, padding=10)
        self.progress_var = tk.DoubleVar()
        
        self.progress = ttk.Progressbar(
            self.frame,
            variable=self.progress_var,
            mode=mode,
            length=300
        )
        self.progress.pack(fill=tk.X, pady=(5, 0))
        
        self.label = ttk.Label(self.frame, text="0%", font=("Microsoft YaHei", 9))
        self.label.pack(pady=(5, 0))
    
    def set_value(self, value):
        """设置进度值 (0-100)"""
        self.progress_var.set(value)
        self.label.config(text=f"{int(value)}%")
    
    def start(self):
        """开始进度条动画"""
        self.progress.start()
    
    def stop(self):
        """停止进度条动画"""
        self.progress.stop()
    
    def pack(self, **kwargs):
        """打包进度条组件"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """网格布局进度条组件"""
        self.frame.grid(**kwargs)
    
    def destroy(self):
        """销毁进度条组件"""
        self.frame.destroy()


class StatusBar:
    """
    StatusBar 类：底部状态栏，显示状态信息和操作提示。
    """
    def __init__(self, parent, on_language_change=None):
        """
        初始化状态栏。
        
        :param parent: 父容器（通常是主窗口）
        :param on_language_change: 语言切换回调函数
        """
        self.parent = parent
        self.on_language_change = on_language_change
        self.lang_manager = get_language_manager()
        
        self.frame = tk.Frame(parent, bg="#f0f2f5", height=25, relief=tk.SUNKEN, borderwidth=1)
        self.frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.frame.pack_propagate(False)
        
        # 左侧状态标签
        self.status_var = tk.StringVar(value=tr("status_ready"))
        self.status_label = tk.Label(
            self.frame,
            textvariable=self.status_var,
            anchor=tk.W,
            padx=10,
            pady=5,
            bg="#f0f2f5",
            fg="#323130",
            font=("Microsoft YaHei", 9)
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X)
        
        # 右侧时间标签
        self.time_var = tk.StringVar()
        self.time_label = tk.Label(
            self.frame,
            textvariable=self.time_var,
            anchor=tk.E,
            padx=10,
            pady=5,
            bg="#f0f2f5",
            fg="#605e5c",
            font=("Microsoft YaHei", 9)
        )
        self.time_label.pack(side=tk.RIGHT)
        
        # 语言切换按钮（在时间标签左边）
        self.lang_btn = tk.Button(
            self.frame,
            text=self.lang_manager.get_language_button_text(),
            command=self.toggle_language,
            bg="#f0f2f5",
            fg="#0078d4",
            font=("Microsoft YaHei", 9, "bold"),
            bd=0,
            padx=10,
            cursor="hand2"
        )
        self.lang_btn.pack(side=tk.RIGHT)
        
        # 注册语言切换回调
        self.lang_manager.add_callback(self.refresh_texts)
        
        # 更新时间显示
        self.update_time()
    
    def toggle_language(self):
        """切换语言"""
        self.lang_manager.toggle_language()
    
    def refresh_texts(self):
        """刷新界面文本"""
        self.lang_btn.config(text=self.lang_manager.get_language_button_text())
        self.status_var.set(tr("status_ready"))
        
        # 调用外部回调
        if self.on_language_change:
            self.on_language_change()
    
    def update_time(self):
        """更新时间显示"""
        current_time = time.strftime("%H:%M:%S")
        self.time_var.set(current_time)
        self.frame.after(1000, self.update_time)
    
    def set_status(self, message, duration=None):
        """
        设置状态消息。
        
        :param message: 状态消息
        :param duration: 消息显示持续时间（毫秒），None 表示永久显示
        """
        self.status_var.set(message)
        if duration:
            self.frame.after(duration, lambda: self.set_status(tr("status_ready")))
    
    def set_busy(self, message=None):
        """设置为忙碌状态"""
        if message is None:
            message = tr("status_processing")
        self.status_var.set(message)
    
    def set_ready(self):
        """设置为就绪状态"""
        self.status_var.set(tr("status_ready"))


class HistoryManager:
    """
    HistoryManager 类：管理配置修改历史，支持撤销/重做功能。
    """
    def __init__(self, max_history=50):
        """
        初始化历史管理器。
        
        :param max_history: 最大历史记录数量
        """
        self.history = []
        self.current = -1
        self.max_history = max_history
    
    def add_state(self, state):
        """添加状态到历史记录"""
        # 如果当前不在历史记录末尾，删除之后的记录
        if self.current < len(self.history) - 1:
            self.history = self.history[:self.current + 1]
        
        self.history.append(state)
        self.current += 1
        
        # 限制历史记录数量
        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.current -= 1
    
    def undo(self):
        """撤销到上一个状态"""
        if self.current > 0:
            self.current -= 1
            return self.history[self.current]
        return None
    
    def redo(self):
        """重做到下一个状态"""
        if self.current < len(self.history) - 1:
            self.current += 1
            return self.history[self.current]
        return None
    
    def can_undo(self):
        """是否可以撤销"""
        return self.current > 0
    
    def can_redo(self):
        """是否可以重做"""
        return self.current < len(self.history) - 1


class AsyncOperation:
    """
    AsyncOperation 类：管理异步操作，防止 UI 冻结。
    """
    def __init__(self, parent, callback, on_complete=None):
        """
        初始化异步操作管理器。
        
        :param parent: 父容器
        :param callback: 异步回调函数
        :param on_complete: 完成时的回调函数
        """
        self.parent = parent
        self.callback = callback
        self.on_complete = on_complete
        self.thread = None
        self.is_running = False
    
    def start(self, *args, **kwargs):
        """启动异步操作"""
        if self.is_running:
            return
        
        self.is_running = True
        self.thread = threading.Thread(
            target=self._run,
            args=args,
            kwargs=kwargs,
            daemon=True
        )
        self.thread.start()
    
    def _run(self, *args, **kwargs):
        """运行回调函数"""
        try:
            result = self.callback(*args, **kwargs)
            if self.on_complete:
                self.parent.after(0, lambda: self.on_complete(result))
        except Exception as e:
            if self.on_complete:
                self.parent.after(0, lambda: self.on_complete(None, e))
        finally:
            self.is_running = False
    
    def stop(self):
        """停止异步操作"""
        self.is_running = False


def create_button(parent, text, command=None, style=None, width=None, tooltip=None, **kwargs):
    """
    创建带 tooltip 的按钮。
    
    :param parent: 父容器
    :param text: 按钮文本
    :param command: 按钮命令
    :param style: 按钮样式
    :param width: 按钮宽度
    :param tooltip: 悬停提示文本
    :param kwargs: 其他参数
    :return: 创建的按钮控件
    """
    if style:
        btn = ttk.Button(parent, text=text, command=command, style=style, width=width, **kwargs)
    else:
        btn = ttk.Button(parent, text=text, command=command, width=width, **kwargs)
    
    if tooltip:
        Tooltip(btn, tooltip)
    
    return btn


def create_labeled_entry(parent, label_text, variable, width=15, tooltip=None, **kwargs):
    """
    创建带标签的输入框。
    
    :param parent: 父容器
    :param label_text: 标签文本
    :param variable: 关联的变量
    :param width: 输入框宽度
    :param tooltip: 悬停提示文本
    :param kwargs: 其他参数
    :return: (标签, 输入框) 元组
    """
    label = ttk.Label(parent, text=label_text, font=("Microsoft YaHei", 9))
    entry = ttk.Entry(parent, textvariable=variable, width=width, **kwargs)
    
    if tooltip:
        Tooltip(entry, tooltip)
    
    return label, entry


def create_labeled_combobox(parent, label_text, variable, values, width=15, tooltip=None, **kwargs):
    """
    创建带标签的下拉框。
    
    :param parent: 父容器
    :param label_text: 标签文本
    :param variable: 关联的变量
    :param values: 下拉选项
    :param width: 下拉框宽度
    :param tooltip: 悬停提示文本
    :param kwargs: 其他参数
    :return: (标签, 下拉框) 元组
    """
    label = ttk.Label(parent, text=label_text, font=("Microsoft YaHei", 9))
    combobox = ttk.Combobox(parent, textvariable=variable, values=values, width=width, **kwargs)
    
    if tooltip:
        Tooltip(combobox, tooltip)
    
    return label, combobox
