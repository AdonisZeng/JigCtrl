import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import datetime
from language import tr

class LogFrame(ttk.Frame):
    """
    LogFrame 类：日志管理界面类，继承自 ttk.Frame。
    提供日志的实时显示、内存存储、多条件筛选、恢复显示、导出及清空功能。
    """
    def __init__(self, master=None):
        super().__init__(master)
        # --- 成员变量初始化 ---
        # 存储所有日志的列表，每条日志为一个元组: (datetime对象, 分类字符串, 消息内容, 完整日志行)
        self.all_logs = [] 
        # 预定义的日志分类标签
        self.categories = ['SYS', 'MOT', 'SET', 'SER', 'TEST', 'REL', 'ERR']
        # 标记当前是否处于筛选状态
        self.is_filtered = False
        
        # 填充父容器并设置内边距
        self.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建界面组件
        self.create_widgets()
        # 添加初始模拟日志
        self.add_mock_logs()

    # =========================================================================
    # 界面构建分区 (UI Construction)
    # =========================================================================
    def create_widgets(self):
        """
        创建日志界面的所有子组件，包括工具栏和日志显示区域。
        """
        # --- 工具栏 (Toolbar) ---
        self.toolbar = ttk.Frame(self)
        self.toolbar.pack(fill=tk.X, pady=(0, 10))

        # 1. 筛选按钮
        self.btn_filter = ttk.Button(self.toolbar, text=tr("log_filter"), command=self.open_filter_window)
        self.btn_filter.pack(side=tk.LEFT, padx=5)

        # 2. 恢复按钮
        self.btn_recover = ttk.Button(self.toolbar, text=tr("log_show_all"), command=self.recover_logs)

        # 3. 导出日志按钮
        self.btn_export = ttk.Button(self.toolbar, text=tr("log_export"), command=self.export_log)
        self.btn_export.pack(side=tk.RIGHT, padx=5)

        # 4. 清空日志按钮
        self.btn_clear = ttk.Button(self.toolbar, text=tr("log_clear"), style="Danger.TButton", command=self.clear_log_with_confirm)
        self.btn_clear.pack(side=tk.RIGHT, padx=5)

        # --- 日志显示区域 (Log Area) ---
        log_container = ttk.Frame(self, style="Card.TFrame")
        log_container.pack(fill=tk.BOTH, expand=True)

        self.log_area = scrolledtext.ScrolledText(
            log_container, 
            state='disabled', 
            height=20, 
            font=("Microsoft YaHei", 9),
            bg="#1e1e1e", # 更深色的背景，提高对比度
            fg="#e0e0e0", # 更亮的文字，提高对比度
            highlightthickness=0,
            borderwidth=0
        )
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # 配置日志颜色标签 - 优化颜色对比度
        self.log_area.tag_configure("SYS", foreground="#61dafb")    # 更亮的蓝色
        self.log_area.tag_configure("MOT", foreground="#b388ff")    # 更亮的紫色
        self.log_area.tag_configure("SET", foreground="#fff59d")    # 更亮的黄色
        self.log_area.tag_configure("SER", foreground="#80cbc4")    # 更亮的青色
        self.log_area.tag_configure("TEST", foreground="#a5d6a7")   # 更亮的绿色
        self.log_area.tag_configure("REL", foreground="#ffcc80")    # 更亮的橙色
        self.log_area.tag_configure("ERR", foreground="#ef9a9a", font=("Microsoft YaHei", 9, "bold")) # 更亮的红色
        self.log_area.tag_configure("COM", foreground="#b0bec5")    # 更亮的灰色
        self.log_area.tag_configure("TIMESTAMP", foreground="#546e7a") # 时间戳颜色

    def add_log(self, message, category="SYS"):
        """
        向系统添加一条新日志。
        """
        now = datetime.datetime.now()
        timestamp_str = now.strftime("%H:%M:%S") + f".{now.microsecond // 1000:03d}"
        
        entry_time = f"[{timestamp_str}] "
        entry_cat = f"[{category}] "
        entry_msg = f"{message}\n"
        
        # 将日志数据存储在内存列表中
        self.all_logs.append((now, category, message, f"{entry_time}{entry_cat}{entry_msg}"))
        
        if not self.is_filtered:
            self.log_area.config(state='normal')
            
            # 分段插入以应用不同颜色
            start_idx = self.log_area.index(tk.END + "-1c")
            self.log_area.insert(tk.END, entry_time, "TIMESTAMP")
            self.log_area.insert(tk.END, entry_cat, category)
            self.log_area.insert(tk.END, entry_msg)
            
            self.log_area.see(tk.END)
            self.log_area.config(state='disabled')

    def add_mock_logs(self):
        """
        初始化时添加一些模拟日志数据，用于界面演示。
        """
        self.add_log("System initialized.", "SYS")
        self.add_log("Loading configuration...", "SYS")
        self.add_log("Connecting to Motion Controller...", "MOT")
        self.add_log("Motion Controller connected.", "MOT")
        self.add_log("Checking settings...", "SET")
        self.add_log("Ready for operation.", "SYS")
        self.add_log("Starting test sequence...", "TEST")
        self.add_log("Error: Sensor timeout.", "ERR")

    def recover_logs(self):
        """
        恢复日志显示：取消筛选状态，显示所有历史日志。
        """
        self.is_filtered = False
        # 隐藏恢复按钮
        self.btn_recover.pack_forget()
        # 重新应用无条件的筛选逻辑（即显示全部）
        self.apply_filter(None, None, "", "")

    def clear_log_with_confirm(self):
        """
        清空日志前的确认逻辑：询问用户是否需要先保存。
        """
        if not self.all_logs:
            return

        # 弹出确认对话框：是(导出并清空), 否(直接清空), 取消(不做操作)
        answer = messagebox.askyesnocancel("Clear Log", "Do you want to save the logs before clearing?")
        
        if answer is True: # 用户选择“是”
            # 导出当前显示的日志内容
            if self.export_log():
                self.perform_clear()
        elif answer is False: # 用户选择“否”
            self.perform_clear()

    def perform_clear(self):
        """
        执行具体的日志清空操作。
        """
        # 清空内存存储
        self.all_logs = []
        self.is_filtered = False
        # 隐藏恢复按钮
        self.btn_recover.pack_forget()
        # 清空 UI 显示
        self.log_area.config(state='normal')
        self.log_area.delete("1.0", tk.END)
        self.log_area.config(state='disabled')
        # 记录一条清空操作的日志
        self.add_log("Log cleared.", "SYS")

    def export_log(self):
        """
        将当前显示的日志内容导出到文本文件。
        返回: 布尔值，表示导出是否成功。
        """
        # 生成默认文件名：test_年月日_时分秒
        default_filename = "test_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # 弹出文件保存对话框
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=default_filename,
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                # 仅获取当前 log_area 中可见的内容（可能是筛选后的结果）
                content = self.log_area.get("1.0", tk.END)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.add_log(f"Log exported to {file_path}", "SYS")
                return True
            except Exception as e:
                self.add_log(f"Error exporting log: {e}", "ERR")
                return False
        return False

    # =========================================================================
    # 筛选逻辑分区 (Filter Logic)
    # =========================================================================
    def open_filter_window(self):
        """
        弹出高级筛选配置窗口。
        """
        filter_win = tk.Toplevel(self)
        filter_win.title("Filter Logs")
        filter_win.geometry("550x500")
        filter_win.resizable(False, False)
        filter_win.configure(bg="white")
        # 设置为模态窗口
        filter_win.transient(self.winfo_toplevel())
        filter_win.grab_set()

        # --- 内部辅助方法：创建时间选择器组件 ---
        def create_time_picker(parent, title):
            frame = ttk.LabelFrame(parent, text=title, padding=5)
            frame.pack(fill=tk.X, padx=10, pady=2)
            
            now = datetime.datetime.now()
            
            # 准备下拉框数值
            years = [str(y) for y in range(now.year - 5, now.year + 6)]
            months = [f"{m:02d}" for m in range(1, 13)]
            days = [f"{d:02d}" for d in range(1, 32)]
            hours = [f"{h:02d}" for h in range(0, 24)]
            min_sec = [f"{i:02d}" for i in range(0, 60)]

            # 存储用户选择的变量
            vars = {
                'Y': tk.StringVar(), 'M': tk.StringVar(), 'D': tk.StringVar(),
                'h': tk.StringVar(), 'm': tk.StringVar(), 's': tk.StringVar()
            }

            # 布局：年-月-日 时:分:秒
            ttk.Combobox(frame, textvariable=vars['Y'], values=years, width=5, state="readonly").pack(side=tk.LEFT, padx=2)
            ttk.Label(frame, text="-").pack(side=tk.LEFT)
            ttk.Combobox(frame, textvariable=vars['M'], values=months, width=3, state="readonly").pack(side=tk.LEFT, padx=2)
            ttk.Label(frame, text="-").pack(side=tk.LEFT)
            ttk.Combobox(frame, textvariable=vars['D'], values=days, width=3, state="readonly").pack(side=tk.LEFT, padx=2)
            
            ttk.Label(frame, text=" ").pack(side=tk.LEFT, padx=5)
            
            ttk.Combobox(frame, textvariable=vars['h'], values=hours, width=3, state="readonly").pack(side=tk.LEFT, padx=2)
            ttk.Label(frame, text=":").pack(side=tk.LEFT)
            # 分和秒设置为可编辑下拉框
            ttk.Combobox(frame, textvariable=vars['m'], values=min_sec, width=3).pack(side=tk.LEFT, padx=2)
            ttk.Label(frame, text=":").pack(side=tk.LEFT)
            ttk.Combobox(frame, textvariable=vars['s'], values=min_sec, width=3).pack(side=tk.LEFT, padx=2)
            
            return vars

        # 创建起始时间和结束时间选择器
        start_vars = create_time_picker(filter_win, "Start Time (From)")
        end_vars = create_time_picker(filter_win, "End Time (To)")

        # --- 内部辅助方法：时间变量操作 ---
        def set_vars_from_dt(vars_dict, dt):
            """将 datetime 对象的值填入变量字典"""
            vars_dict['Y'].set(str(dt.year))
            vars_dict['M'].set(f"{dt.month:02d}")
            vars_dict['D'].set(f"{dt.day:02d}")
            vars_dict['h'].set(f"{dt.hour:02d}")
            vars_dict['m'].set(f"{dt.minute:02d}")
            vars_dict['s'].set(f"{dt.second:02d}")

        def get_dt_from_vars(vars_dict):
            """从变量字典中解析出 datetime 对象"""
            try:
                y, m, d = vars_dict['Y'].get(), vars_dict['M'].get(), vars_dict['D'].get()
                h, mi, s = vars_dict['h'].get(), vars_dict['m'].get(), vars_dict['s'].get()
                if not all([y, m, d, h, mi, s]): return None
                return datetime.datetime(int(y), int(m), int(d), int(h), int(mi), int(s))
            except: return None

        def init_time():
            """初始化时间范围：当前时间的前一小时到当前时间"""
            now = datetime.datetime.now()
            hour_ago = now - datetime.timedelta(hours=1)
            set_vars_from_dt(start_vars, hour_ago)
            set_vars_from_dt(end_vars, now)

        # 初始化时间按钮
        btn_init_time = ttk.Button(filter_win, text=tr("log_init_time"), command=init_time)
        btn_init_time.pack(pady=5)

        # --- 筛选分类 (Category) ---
        cat_frame = ttk.LabelFrame(filter_win, text=tr("log_category_tag"), padding=10)
        cat_frame.pack(fill=tk.X, padx=10, pady=5)
        cat_var = tk.StringVar()
        cat_combo = ttk.Combobox(cat_frame, textvariable=cat_var, values=self.categories)
        cat_combo.pack(fill=tk.X)

        # --- 筛选内容关键字 (Content Keyword) ---
        content_frame = ttk.LabelFrame(filter_win, text=tr("log_content_keyword"), padding=10)
        content_frame.pack(fill=tk.X, padx=10, pady=5)
        content_var = tk.StringVar()
        ent_content = ttk.Entry(content_frame, textvariable=content_var)
        ent_content.pack(fill=tk.X)

        # --- 操作按钮区域 (底部) ---
        btn_action_frame = ttk.Frame(filter_win, padding=10)
        btn_action_frame.pack(fill=tk.X, side=tk.BOTTOM)

        def reset_filters_ui():
            """重置筛选窗口的所有输入项，不影响主界面显示"""
            for v in list(start_vars.values()) + list(end_vars.values()): v.set("")
            cat_var.set("")
            content_var.set("")

        def apply_filter_action():
            """执行筛选动作：验证输入并调用主界面的筛选逻辑"""
            s_time = get_dt_from_vars(start_vars)
            e_time = get_dt_from_vars(end_vars)
            
            # 基础验证
            if (start_vars['Y'].get() and not s_time) or (end_vars['Y'].get() and not e_time):
                messagebox.showerror("Error", "Invalid time format.")
                return
                
            if s_time and e_time and s_time > e_time:
                messagebox.showerror("Error", "Start time must be earlier than end time.")
                return

            # 设置筛选状态并显示恢复按钮
            self.is_filtered = True
            self.btn_recover.pack(side=tk.LEFT, padx=5, after=self.btn_filter)
            # 应用筛选逻辑
            self.apply_filter(s_time, e_time, cat_var.get().strip(), content_var.get().strip())
            # 关闭筛选窗口
            filter_win.destroy()

        # 底部按钮布局
        btn_reset = ttk.Button(btn_action_frame, text=tr("log_reset"), command=reset_filters_ui)
        btn_reset.pack(side=tk.LEFT, padx=10)

        btn_apply = ttk.Button(btn_action_frame, text=tr("log_filter_btn"), command=apply_filter_action)
        btn_apply.pack(side=tk.RIGHT, padx=10)

    def apply_filter(self, start_time, end_time, category, keyword):
        """
        根据给定条件，对内存中的所有日志进行过滤并刷新显示。
        参数:
            start_time: 起始时间 (datetime对象)
            end_time: 结束时间 (datetime对象)
            category: 分类关键字 (字符串)
            keyword: 消息关键字 (字符串)
        """
        self.log_area.config(state='normal')
        # 先清空显示区域
        self.log_area.delete("1.0", tk.END)
        
        # 遍历所有存储的日志并检查条件
        for log_time, log_cat, log_msg, full_entry in self.all_logs:
            if start_time and log_time < start_time: continue
            if end_time and log_time > end_time: continue
            if category and category.upper() not in log_cat.upper(): continue
            if keyword and keyword.lower() not in log_msg.lower(): continue
            
            # 满足所有条件的日志行将被插入
            self.log_area.insert(tk.END, full_entry)
            
        # 滚动到最新位置并重新禁用编辑
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')
    
    def refresh_texts(self):
        """刷新界面文本（语言切换时调用）"""
        self.btn_filter.config(text=tr("log_filter"))
        self.btn_export.config(text=tr("log_export"))
        self.btn_clear.config(text=tr("log_clear"))
        self.btn_recover.config(text=tr("log_show_all"))
