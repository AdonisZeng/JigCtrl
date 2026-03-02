import json
import os


class LanguageManager:
    """
    LanguageManager 类：管理界面语言切换。
    支持中文和英文两种语言。
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config_path=None):
        """
        初始化语言管理器。
        
        :param config_path: 配置文件路径
        """
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._initialized = True
        self.current_language = "zh"  # 默认中文
        self.config_path = config_path or "config/language.json"
        self.callbacks = []  # 语言切换回调列表
        
        # 定义所有翻译文本
        self.translations = {
            # === 页签标题 ===
            "tab_motion": {"zh": "运动控制", "en": "Motion Control"},
            "tab_settings": {"zh": "参数设置", "en": "Settings"},
            "tab_test": {"zh": "测试控制", "en": "Test Control"},
            "tab_log": {"zh": "日志", "en": "Logs"},
            "tab_debug": {"zh": "电机调试", "en": "Motor Debug"},
            
            # === 运动控制页面 ===
            "motion_title": {"zh": "运动控制", "en": "Motion Control"},
            "motion_direction_control": {"zh": "方向控制", "en": "Direction Control"},
            "motion_origin": {"zh": "原点操作", "en": "Origin Operations"},
            "motion_key_binding": {"zh": "按键绑定", "en": "Key Binding"},
            "motion_x_position": {"zh": "X轴位置", "en": "X Position"},
            "motion_y_position": {"zh": "Y轴位置", "en": "Y Position"},
            "motion_set_origin": {"zh": "设置原点", "en": "Set Origin"},
            "motion_return_origin": {"zh": "回到原点", "en": "Return to Origin"},
            "motion_get_homing_speed": {"zh": "获取回原点速度", "en": "Get Homing Speed"},
            "motion_set_homing_speed": {"zh": "设置回原点速度", "en": "Set Homing Speed"},
            "motion_get_x_pulse": {"zh": "获取X轴脉冲", "en": "Get X Pulse"},
            "motion_get_y_pulse": {"zh": "获取Y轴脉冲", "en": "Get Y Pulse"},
            "motion_add_binding": {"zh": "添加绑定", "en": "Add Binding"},
            "motion_select_key": {"zh": "选择按键", "en": "Select Key"},
            "motion_cancel": {"zh": "取消", "en": "Cancel"},
            "motion_delete": {"zh": "删除", "en": "Delete"},
            "motion_key": {"zh": "按键", "en": "Key"},
            "motion_x_pulse": {"zh": "X脉冲", "en": "X Pulse"},
            "motion_y_pulse": {"zh": "Y脉冲", "en": "Y Pulse"},
            "motion_action": {"zh": "操作", "en": "Action"},
            "motion_manual_control": {"zh": "手动控制", "en": "Manual Control"},
            "motion_up": {"zh": "▲ 上", "en": "▲ Up"},
            "motion_left": {"zh": "◀ 左", "en": "◀ Left"},
            "motion_down": {"zh": "▼ 下", "en": "▼ Down"},
            "motion_right": {"zh": "▶ 右", "en": "▶ Right"},
            "motion_coordinate_system": {"zh": "坐标系", "en": "Coordinate System"},
            "motion_homing_speed": {"zh": "回原点速度 (RPM):", "en": "Homing Speed (RPM):"},
            "motion_get": {"zh": "获取", "en": "Get"},
            "motion_set": {"zh": "设置", "en": "Set"},
            "motion_refresh": {"zh": "刷新", "en": "Refresh"},
            "motion_binding_hint": {"zh": "管理自动化测试的按键位置", "en": "Manage key positions for automated testing"},
            "motion_key_label": {"zh": "按键:", "en": "Key:"},
            "motion_x_label": {"zh": "X:", "en": "X:"},
            "motion_y_label": {"zh": "Y:", "en": "Y:"},
            "motion_x_axis_position": {"zh": "X轴位置", "en": "X-Axis Position"},
            "motion_y_axis_position": {"zh": "Y轴位置", "en": "Y-Axis Position"},
            
            # === 参数设置页面 ===
            "settings_serial": {"zh": "串口配置", "en": "Serial Configuration"},
            "settings_press": {"zh": "按压参数", "en": "Press Settings"},
            "settings_test_flow": {"zh": "测试流程", "en": "Test Flow"},
            "settings_port": {"zh": "端口", "en": "Port"},
            "settings_baud": {"zh": "波特率", "en": "Baud Rate"},
            "settings_open_port": {"zh": "打开端口", "en": "Open Port"},
            "settings_close_port": {"zh": "关闭端口", "en": "Close Port"},
            "settings_press_duration": {"zh": "按压时长:", "en": "Press Duration (ms):"},
            "settings_interval": {"zh": "间隔:", "en": "Interval (ms):"},
            "settings_add_item": {"zh": "+ 添加测试项", "en": "+ Add Test Item"},
            "settings_clear_all": {"zh": "清空全部", "en": "Clear All"},
            "settings_next_item": {"zh": "下一项 >>", "en": "Next Item >>"},
            "settings_apply": {"zh": "应用更改", "en": "Apply Changes"},
            "settings_item_name": {"zh": "项目名称", "en": "Item Name"},
            "settings_key": {"zh": "按键", "en": "Key"},
            "settings_move_up": {"zh": "上移", "en": "Move Up"},
            "settings_move_down": {"zh": "下移", "en": "Move Down"},
            "settings_remove": {"zh": "移除", "en": "Remove"},
            "settings_test_type": {"zh": "测试类型:", "en": "Test Type:"},
            "settings_single_key": {"zh": "单键", "en": "Single Key"},
            "settings_multi_key": {"zh": "多键", "en": "Multi-Key"},
            "settings_select_key": {"zh": "选择按键:", "en": "Select Key:"},
            "settings_test_mode": {"zh": "测试模式:", "en": "Test Mode:"},
            "settings_count": {"zh": "次数", "en": "Count"},
            "settings_time": {"zh": "时间", "en": "Time"},
            "settings_target_value": {"zh": "目标值:", "en": "Target Value:"},
            "settings_unit": {"zh": "单位:", "en": "Unit:"},
            "settings_ok": {"zh": "确定", "en": "OK"},
            "settings_cancel": {"zh": "取消", "en": "Cancel"},
            "settings_x_motor": {"zh": "X轴电机", "en": "X-Axis Motor"},
            "settings_y_motor": {"zh": "Y轴电机", "en": "Y-Axis Motor"},
            "settings_relay": {"zh": "继电器 (电磁阀)", "en": "Relay (Solenoid)"},
            "settings_port_label": {"zh": "端口:", "en": "Port:"},
            "settings_baud_label": {"zh": "波特率:", "en": "Baud:"},
            "settings_step": {"zh": "步骤", "en": "Step"},
            "settings_x_motor_title": {"zh": "X轴电机", "en": "X-Axis Motor"},
            "settings_y_motor_title": {"zh": "Y轴电机", "en": "Y-Axis Motor"},
            "settings_relay_title": {"zh": "继电器 (电磁阀)", "en": "Relay (Solenoid)"},
            "settings_running": {"zh": "运行中...", "en": "Running..."},
            "settings_pending": {"zh": "待执行", "en": "Pending"},
            "settings_completed": {"zh": "已完成", "en": "Completed"},
            "settings_times": {"zh": "次", "en": "Times"},
            "settings_single_key_label": {"zh": "单键", "en": "Single Key"},
            "settings_multi_key_label": {"zh": "多键", "en": "Multi-Key"},
            "settings_delete_item": {"zh": "删除项目", "en": "Delete Item"},
            "settings_key1": {"zh": "按键1", "en": "Key 1"},
            "settings_key2": {"zh": "按键2", "en": "Key 2"},
            "error_multi_key_exists": {"zh": "测试流程中已有多键测试项，不能再添加其他测试项", "en": "Multi-key test item already exists, cannot add other items"},
            "error_cannot_add_multi_key": {"zh": "测试流程中已有其他测试项，不能再添加多键测试项", "en": "Other test items exist, cannot add multi-key item"},
            
            # === 测试控制页面 ===
            "test_title": {"zh": "测试控制", "en": "Test Control"},
            "test_mode": {"zh": "测试模式", "en": "Test Mode"},
            "test_count_mode": {"zh": "次数模式", "en": "Count Mode"},
            "test_time_mode": {"zh": "时间模式", "en": "Time Mode"},
            "test_count": {"zh": "测试次数", "en": "Test Count"},
            "test_duration": {"zh": "测试时长 (秒)", "en": "Duration (seconds)"},
            "test_remaining": {"zh": "剩余", "en": "Remaining"},
            "test_current_item": {"zh": "当前项目", "en": "Current Item"},
            "test_start": {"zh": "开始测试", "en": "Start"},
            "test_pause": {"zh": "暂停", "en": "Pause"},
            "test_resume": {"zh": "继续", "en": "Resume"},
            "test_stop": {"zh": "停止", "en": "Stop"},
            "test_skip": {"zh": "跳过", "en": "Skip"},
            "test_times": {"zh": "次", "en": "times"},
            "test_seconds": {"zh": "秒", "en": "seconds"},
            "test_status_monitor": {"zh": "状态监控", "en": "Status Monitor"},
            "test_current_state": {"zh": "当前状态: 待机", "en": "Current State: STANDBY"},
            "test_testing": {"zh": "● 测试中", "en": "● TESTING"},
            "test_paused": {"zh": "II 已暂停", "en": "II PAUSED"},
            "test_standby": {"zh": "待机", "en": "STANDBY"},
            "test_resume": {"zh": "继续", "en": "Resume"},
            "test_item": {"zh": "项目", "en": "Item"},
            "test_counts": {"zh": "次", "en": "Counts"},

            # === 日志页面 ===
            "log_title": {"zh": "日志", "en": "Logs"},
            "log_filter": {"zh": "筛选", "en": "Filter"},
            "log_export": {"zh": "导出", "en": "Export"},
            "log_clear": {"zh": "清空", "en": "Clear"},
            "log_all": {"zh": "全部", "en": "All"},
            "log_time_range": {"zh": "时间范围", "en": "Time Range"},
            "log_category": {"zh": "分类", "en": "Category"},
            "log_keyword": {"zh": "关键字", "en": "Keyword"},
            "log_apply_filter": {"zh": "应用筛选", "en": "Apply Filter"},
            "log_show_all": {"zh": "↺ 显示全部", "en": "↺ Show All"},
            "log_time_range": {"zh": "时间范围", "en": "Time Range"},
            "log_category_tag": {"zh": "分类标签", "en": "Category Tag"},
            "log_content_keyword": {"zh": "日志内容关键字", "en": "Log Content Keyword"},
            "log_init_time": {"zh": "初始化时间", "en": "Init Time"},
            "log_reset": {"zh": "重置", "en": "Reset"},
            "log_filter_btn": {"zh": "筛选", "en": "Filter"},
            
            # === 电机调试页面 ===
            "debug_title": {"zh": "电机调试", "en": "Motor Debug"},
            "debug_command": {"zh": "指令", "en": "Command"},
            "debug_send": {"zh": "发送", "en": "Send"},
            "debug_clear": {"zh": "清空", "en": "Clear"},
            "debug_quick_commands": {"zh": "快速指令", "en": "Quick Commands"},
            "debug_log": {"zh": "通信日志", "en": "Communication Log"},
            "debug_serial_config": {"zh": "串口配置", "en": "Serial Configuration"},
            "debug_port": {"zh": "端口:", "en": "Port:"},
            "debug_baud": {"zh": "波特率:", "en": "Baud:"},
            "debug_open": {"zh": "打开", "en": "Open"},
            "debug_close": {"zh": "关闭", "en": "Close"},
            "debug_refresh": {"zh": "刷新", "en": "Refresh"},
            "debug_run": {"zh": "运行", "en": "Run"},
            "debug_pause": {"zh": "暂停", "en": "Pause"},
            "debug_stop": {"zh": "停止", "en": "Stop"},
            "debug_status": {"zh": "状态", "en": "Status"},
            "debug_speed": {"zh": "速度:", "en": "Speed:"},
            "debug_direction": {"zh": "方向:", "en": "Direction:"},
            "debug_cw": {"zh": "正转", "en": "CW"},
            "debug_ccw": {"zh": "反转", "en": "CCW"},
            "debug_travel": {"zh": "行程 (脉冲/圈/角度):", "en": "Travel (Pulse/Rev/Angle):"},
            "debug_pulse": {"zh": "脉冲", "en": "Pulse"},
            "debug_rev": {"zh": "圈", "en": "Rev"},
            "debug_angle": {"zh": "角度", "en": "Angle"},
            "debug_get_all": {"zh": "获取所有参数", "en": "Get All Params"},
            "debug_manual": {"zh": "手动指令", "en": "Manual Command"},
            "debug_copy": {"zh": "复制", "en": "Copy"},
            "debug_ascii": {"zh": "ASCII", "en": "ASCII"},
            "debug_serial_connection": {"zh": "串口连接", "en": "Serial Connection"},
            "debug_port_label": {"zh": "端口:", "en": "Port:"},
            "debug_baud_label": {"zh": "波特率:", "en": "Baud:"},
            "debug_open_port": {"zh": "打开端口", "en": "Open Port"},
            "debug_close_port": {"zh": "关闭端口", "en": "Close Port"},
            "debug_get_all_params": {"zh": "获取所有参数", "en": "Get All Params"},
            "debug_run_btn": {"zh": "运行", "en": "Run"},
            "debug_pause_btn": {"zh": "暂停", "en": "Pause"},
            "debug_stop_btn": {"zh": "停止", "en": "Stop"},
            "debug_status_btn": {"zh": "状态", "en": "Status"},
            "debug_speed_label": {"zh": "速度:", "en": "Speed:"},
            "debug_dir_label": {"zh": "方向:", "en": "Dir:"},
            "debug_set_btn": {"zh": "设置", "en": "Set"},
            "debug_get_btn": {"zh": "获取", "en": "Get"},
            "debug_rev_label": {"zh": "圈数:", "en": "Rev:"},
            "debug_angle_label": {"zh": "角度:", "en": "Angle:"},
            "debug_pulse_label": {"zh": "脉冲:", "en": "Pulse:"},
            "debug_manual_hex": {"zh": "手动指令 (HEX)", "en": "Manual Command (HEX)"},
            "debug_ex_run": {"zh": "例: 运行", "en": "Ex: Run"},
            "debug_ex_stop": {"zh": "例: 停止", "en": "Ex: Stop"},
            "debug_ex_query": {"zh": "例: 查询", "en": "Ex: Query"},
            "debug_comm_log": {"zh": "通信日志", "en": "Communication Log"},
            "debug_hex": {"zh": "HEX", "en": "HEX"},
            "debug_copy": {"zh": "📋 复制", "en": "📋 Copy"},
            
            # === 状态栏 ===
            "status_ready": {"zh": "就绪", "en": "Ready"},
            "status_processing": {"zh": "处理中...", "en": "Processing..."},
            "status_saved": {"zh": "已保存", "en": "Saved"},
            
            # === 语言切换按钮 ===
            "lang_zh": {"zh": "中文", "en": "中文"},
            "lang_en": {"zh": "EN", "en": "EN"},
            
            # === 通用 ===
            "confirm": {"zh": "确认", "en": "Confirm"},
            "cancel": {"zh": "取消", "en": "Cancel"},
            "save": {"zh": "保存", "en": "Save"},
            "load": {"zh": "加载", "en": "Load"},
            "error": {"zh": "错误", "en": "Error"},
            "success": {"zh": "成功", "en": "Success"},
            "warning": {"zh": "警告", "en": "Warning"},
        }
        
        # 加载保存的语言设置
        self.load()
    
    def get_text(self, key):
        """
        获取翻译文本。
        
        :param key: 文本键名
        :return: 当前语言对应的文本
        """
        if key in self.translations:
            return self.translations[key].get(self.current_language, key)
        return key
    
    def toggle_language(self):
        """
        切换语言。
        """
        self.current_language = "en" if self.current_language == "zh" else "zh"
        self.save()
        self._notify_callbacks()
    
    def set_language(self, lang):
        """
        设置语言。
        
        :param lang: 语言代码 ("zh" 或 "en")
        """
        if lang in ["zh", "en"]:
            self.current_language = lang
            self.save()
            self._notify_callbacks()
    
    def get_language(self):
        """
        获取当前语言。
        
        :return: 当前语言代码
        """
        return self.current_language
    
    def get_language_button_text(self):
        """
        获取语言切换按钮的显示文本。
        
        :return: 按钮文本
        """
        return "EN" if self.current_language == "zh" else "中文"
    
    def add_callback(self, callback):
        """
        添加语言切换回调函数。
        
        :param callback: 回调函数
        """
        if callback not in self.callbacks:
            self.callbacks.append(callback)
    
    def remove_callback(self, callback):
        """
        移除语言切换回调函数。
        
        :param callback: 回调函数
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def _notify_callbacks(self):
        """通知所有回调函数语言已切换"""
        for callback in self.callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Language callback error: {e}")
    
    def save(self):
        """保存语言设置到配置文件"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump({"language": self.current_language}, f)
        except Exception as e:
            print(f"Failed to save language setting: {e}")
    
    def load(self):
        """从配置文件加载语言设置"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.current_language = data.get("language", "zh")
        except Exception as e:
            print(f"Failed to load language setting: {e}")
            self.current_language = "zh"


# 全局语言管理器实例
_language_manager = None


def get_language_manager():
    """
    获取全局语言管理器实例。
    
    :return: LanguageManager 实例
    """
    global _language_manager
    if _language_manager is None:
        _language_manager = LanguageManager()
    return _language_manager


def tr(key):
    """
    翻译函数的简写形式。
    
    :param key: 文本键名
    :return: 翻译后的文本
    """
    return get_language_manager().get_text(key)
