import customtkinter as ctk
from tkinter import messagebox
from pynput import keyboard
from pynput.keyboard import Key, KeyCode
import pyperclip
import time
import threading
import logging
from config_manager import ConfigManager

# 设置外观模式和默认颜色主题
ctk.set_appearance_mode("light")  # 可选: "light", "dark", "system"
ctk.set_default_color_theme("dark-blue")  # 可选: "blue", "green", "dark-blue"

class AutoInputGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("自动输入工具")
        self.root.geometry("900x750")
        
        # 配置管理器
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        
        # 全局变量
        self.hotkey_pressed = threading.Event()
        self.current_keys = set()
        self.listener = None
        self.is_listening = False
        
        # 从配置加载热键
        self.hotkeys = self.config_manager.hotkeys_from_config(self.config)
        self.hotkey_descriptions = [hk['description'] for hk in self.config['hotkeys']]
        
        # 防抖时间
        self.debounce_time = self.config.get('debounce_time', 0.5)
        
        # 快捷键设置窗口引用
        self.hotkey_settings_window = None
        
        # 配置日志
        self.setup_logging()
        
        # 创建界面
        self.create_widgets()
        
        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_logging(self):
        """配置日志系统"""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear()
    
    def create_widgets(self):
        """创建界面组件"""
        
        # ===== 标题区域 =====
        title_frame = ctk.CTkFrame(self.root, corner_radius=0, fg_color=("gray85", "gray15"))
        title_frame.pack(fill="x", padx=0, pady=0)
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="自动输入工具",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=("#1f538d", "#3a7ebf")
        )
        title_label.pack(pady=20)
        
        # ===== 主内容区域 =====
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 左右分栏布局
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        right_frame = ctk.CTkFrame(main_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # ========== 左侧内容 ==========
        
        # ----- 控制面板 -----
        control_frame = ctk.CTkFrame(left_frame)
        control_frame.pack(fill="x", pady=(0, 15))
        
        control_title = ctk.CTkLabel(
            control_frame,
            text="控制面板",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        control_title.pack(pady=(15, 10), padx=15, anchor="w")
        
        # 状态指示
        status_container = ctk.CTkFrame(control_frame, fg_color="transparent")
        status_container.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkLabel(
            status_container,
            text="监听状态:",
            font=ctk.CTkFont(size=13)
        ).pack(side="left", padx=(0, 10))
        
        self.status_label = ctk.CTkLabel(
            status_container,
            text="● 未启动",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#e74c3c"
        )
        self.status_label.pack(side="left")
        
        # 按钮区域
        button_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        self.start_button = ctk.CTkButton(
            button_frame,
            text="启动监听",
            command=self.start_listening,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            corner_radius=8,
            fg_color="#27ae60",
            hover_color="#229954"
        )
        self.start_button.pack(fill="x", pady=(0, 10))
        
        self.stop_button = ctk.CTkButton(
            button_frame,
            text="停止监听",
            command=self.stop_listening,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            corner_radius=8,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            state="disabled"
        )
        self.stop_button.pack(fill="x", pady=(0, 10))
        
        self.test_button = ctk.CTkButton(
            button_frame,
            text="测试输入",
            command=self.test_input,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            corner_radius=8,
            fg_color="#3498db",
            hover_color="#2980b9"
        )
        self.test_button.pack(fill="x")
        
        # ----- 内容输入区域 -----
        input_frame = ctk.CTkFrame(left_frame)
        input_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        input_title = ctk.CTkLabel(
            input_frame,
            text="内容输入区",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        input_title.pack(pady=(15, 10), padx=15, anchor="w")
        
        # 输入框
        self.input_text = ctk.CTkTextbox(
            input_frame,
            height=180,
            font=ctk.CTkFont(size=13),
            corner_radius=8,
            wrap="word"
        )
        self.input_text.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        
        # 添加placeholder
        placeholder_text = "在此输入要自动输入的内容...\n支持多行文本、换行符和制表符"
        self.input_text.insert("1.0", placeholder_text)
        self.input_text.configure(text_color="gray50")
        
        # Placeholder效果
        def on_input_focus_in(event):
            if self.input_text.get("1.0", "end-1c") == placeholder_text:
                self.input_text.delete("1.0", "end")
                self.input_text.configure(text_color=("gray10", "gray90"))
        
        def on_input_focus_out(event):
            if not self.input_text.get("1.0", "end-1c").strip():
                self.input_text.insert("1.0", placeholder_text)
                self.input_text.configure(text_color="gray50")
        
        self.input_text.bind("<FocusIn>", on_input_focus_in)
        self.input_text.bind("<FocusOut>", on_input_focus_out)
        
        # 按钮容器
        input_button_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        input_button_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # 使用grid布局让按钮平均分布
        input_button_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        ctk.CTkButton(
            input_button_frame,
            text="复制到剪贴板",
            command=self.copy_input_to_clipboard,
            font=ctk.CTkFont(size=12),
            height=35,
            corner_radius=6,
            fg_color="#9b59b6",
            hover_color="#8e44ad"
        ).grid(row=0, column=0, padx=3, sticky="ew")
        
        ctk.CTkButton(
            input_button_frame,
            text="复制并输入",
            command=self.copy_and_auto_input,
            font=ctk.CTkFont(size=12),
            height=35,
            corner_radius=6,
            fg_color="#e67e22",
            hover_color="#d35400"
        ).grid(row=0, column=1, padx=3, sticky="ew")
        
        ctk.CTkButton(
            input_button_frame,
            text="清空",
            command=self.clear_input_text,
            font=ctk.CTkFont(size=12),
            height=35,
            corner_radius=6,
            fg_color="#7f8c8d",
            hover_color="#95a5a6"
        ).grid(row=0, column=2, padx=3, sticky="ew")
        
        # ----- 剪贴板预览 -----
        clipboard_frame = ctk.CTkFrame(left_frame)
        clipboard_frame.pack(fill="x")
        
        clipboard_title_container = ctk.CTkFrame(clipboard_frame, fg_color="transparent")
        clipboard_title_container.pack(fill="x", pady=(15, 10), padx=15)
        
        ctk.CTkLabel(
            clipboard_title_container,
            text="剪贴板预览",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        ctk.CTkButton(
            clipboard_title_container,
            text="刷新",
            command=self.update_clipboard_preview,
            font=ctk.CTkFont(size=11),
            width=70,
            height=25,
            corner_radius=5,
            fg_color="#95a5a6",
            hover_color="#7f8c8d"
        ).pack(side="right")
        
        self.clipboard_text = ctk.CTkTextbox(
            clipboard_frame,
            height=80,
            font=ctk.CTkFont(size=12),
            corner_radius=8,
            wrap="word"
        )
        self.clipboard_text.pack(fill="x", padx=15, pady=(0, 15))
        
        # ========== 右侧内容 ==========
        
        # ----- 快捷键配置 -----
        hotkey_frame = ctk.CTkFrame(right_frame)
        hotkey_frame.pack(fill="x", pady=(0, 15))
        
        hotkey_title_container = ctk.CTkFrame(hotkey_frame, fg_color="transparent")
        hotkey_title_container.pack(fill="x", pady=(15, 10), padx=15)
        
        ctk.CTkLabel(
            hotkey_title_container,
            text="快捷键配置",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        ctk.CTkButton(
            hotkey_title_container,
            text="设置",
            command=self.open_hotkey_settings,
            font=ctk.CTkFont(size=11),
            width=70,
            height=25,
            corner_radius=5,
            fg_color="#e67e22",
            hover_color="#d35400"
        ).pack(side="right")
        
        # 快捷键列表容器（用于动态更新）
        self.hotkey_list_frame = ctk.CTkFrame(hotkey_frame, fg_color="transparent")
        self.hotkey_list_frame.pack(fill="x", padx=15)
        
        # 刷新快捷键显示
        self.refresh_hotkey_display()
        
        # 添加底部说明
        ctk.CTkLabel(
            hotkey_frame,
            text="启动监听后，按下任意快捷键触发自动输入",
            font=ctk.CTkFont(size=11),
            text_color="gray60"
        ).pack(pady=(5, 15), padx=15)
        
        # ----- 运行日志 -----
        log_frame = ctk.CTkFrame(right_frame)
        log_frame.pack(fill="both", expand=True)
        
        log_title_container = ctk.CTkFrame(log_frame, fg_color="transparent")
        log_title_container.pack(fill="x", pady=(15, 10), padx=15)
        
        ctk.CTkLabel(
            log_title_container,
            text="运行日志",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        ctk.CTkButton(
            log_title_container,
            text="清空",
            command=self.clear_log,
            font=ctk.CTkFont(size=11),
            width=70,
            height=25,
            corner_radius=5,
            fg_color="#7f8c8d",
            hover_color="#95a5a6"
        ).pack(side="right")
        
        self.log_text = ctk.CTkTextbox(
            log_frame,
            font=ctk.CTkFont(size=12, family="Consolas"),
            corner_radius=8,
            wrap="word"
        )
        self.log_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # 配置日志handler
        handler = logging.Handler()
        handler.emit = lambda record: self.root.after(0, 
            lambda: self.append_log(handler.format(record)))
        
        formatter = logging.Formatter('%(asctime)s - %(message)s', 
                                     datefmt='%H:%M:%S')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # 初始化
        self.update_clipboard_preview()
        self.logger.info("欢迎使用自动输入工具！")
        self.logger.info("点击 '启动监听' 或直接在输入区输入内容开始使用")
    
    def append_log(self, msg):
        """添加日志"""
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete("1.0", "end")
        self.logger.info("日志已清空")
    
    def refresh_hotkey_display(self):
        """刷新快捷键显示"""
        # 清空现有显示
        for widget in self.hotkey_list_frame.winfo_children():
            widget.destroy()
        
        # 重新创建显示
        for i, desc in enumerate(self.hotkey_descriptions, 1):
            hotkey_item = ctk.CTkFrame(self.hotkey_list_frame, fg_color=("gray80", "gray25"))
            hotkey_item.pack(fill="x", pady=5)
            
            ctk.CTkLabel(
                hotkey_item,
                text=f"{i}.",
                font=ctk.CTkFont(size=13),
                width=30
            ).pack(side="left", padx=(10, 5), pady=10)
            
            ctk.CTkLabel(
                hotkey_item,
                text=desc,
                font=ctk.CTkFont(size=13, weight="bold", family="Courier New"),
                anchor="w"
            ).pack(side="left", fill="x", expand=True, padx=5, pady=10)
    
    def open_hotkey_settings(self):
        """打开快捷键设置窗口"""
        if self.hotkey_settings_window is not None and self.hotkey_settings_window.winfo_exists():
            self.hotkey_settings_window.focus()
            return
        
        self.hotkey_settings_window = HotkeySettingsWindow(self)
    
    def update_clipboard_preview(self):
        """更新剪贴板预览"""
        try:
            content = pyperclip.paste()
            self.clipboard_text.delete("1.0", "end")
            preview = content[:200] + ('...' if len(content) > 200 else '')
            self.clipboard_text.insert("1.0", preview)
        except Exception as e:
            self.clipboard_text.delete("1.0", "end")
            self.clipboard_text.insert("1.0", f"无法读取剪贴板: {e}")
    
    def copy_input_to_clipboard(self):
        """复制输入框内容到剪贴板"""
        try:
            # 获取原始内容，保留所有换行符
            content = self.input_text.get("1.0", "end-1c")
            placeholder_text = "在此输入要自动输入的内容...\n支持多行文本、换行符和制表符"
            
            # 只去除首尾空白来检查是否为空
            if content.strip() == placeholder_text or not content.strip():
                messagebox.showwarning("提示", "请先在输入框中输入内容！")
                return
            
            # 复制原始内容，保留所有换行和空格
            pyperclip.copy(content)
            self.logger.info(f"已复制到剪贴板（{len(content)} 个字符，包含所有换行）")
            self.update_clipboard_preview()
            
            # 统计换行数量
            line_count = content.count('\n') + 1
            messagebox.showinfo("成功", f"内容已复制到剪贴板！\n共 {len(content)} 个字符\n{line_count} 行")
            
        except Exception as e:
            self.logger.error(f"复制失败: {e}")
            messagebox.showerror("错误", f"复制失败: {e}")
    
    def copy_and_auto_input(self):
        """复制到剪贴板并触发自动输入"""
        try:
            # 获取原始内容，保留所有换行符
            content = self.input_text.get("1.0", "end-1c")
            placeholder_text = "在此输入要自动输入的内容...\n支持多行文本、换行符和制表符"
            
            # 只去除首尾空白来检查是否为空
            if content.strip() == placeholder_text or not content.strip():
                messagebox.showwarning("提示", "请先在输入框中输入内容！")
                return
            
            # 复制原始内容，保留所有换行和空格
            pyperclip.copy(content)
            line_count = content.count('\n') + 1
            self.logger.info(f"已复制到剪贴板（{len(content)} 个字符，{line_count} 行，包含所有换行）")
            self.update_clipboard_preview()
            
            self.logger.info("将在3秒后开始自动输入...")
            self.logger.info("请切换到目标窗口！")
            
            threading.Thread(target=self._delayed_auto_input, args=(content,), daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"操作失败: {e}")
            messagebox.showerror("错误", f"操作失败: {e}")
    
    def _delayed_auto_input(self, content):
        """延迟后自动输入"""
        try:
            for i in range(3, 0, -1):
                self.logger.info(f"倒计时: {i}秒")
                time.sleep(1)
            
            self.logger.info("===== 开始自动输入 =====")
            self.logger.info("正在输入...")
            self.logger.info("提示：如果有输入法，建议切换到英文模式以获得最佳效果")
            
            keyboard_controller = keyboard.Controller()
            char_count = len(content)
            
            for i, char in enumerate(content):
                if char == '\n':
                    keyboard_controller.press(Key.enter)
                    keyboard_controller.release(Key.enter)
                elif char == '\t':
                    keyboard_controller.press(Key.tab)
                    keyboard_controller.release(Key.tab)
                elif char == ' ':
                    # 空格使用 Key.space，确保正确输入
                    keyboard_controller.press(Key.space)
                    keyboard_controller.release(Key.space)
                else:
                    try:
                        keyboard_controller.press(char)
                        keyboard_controller.release(char)
                    except Exception:
                        self.logger.warning(f"无法输入字符: {repr(char)}")
                        continue
                
                # 中英文混合时，增加延迟避免输入法干扰
                base_delay = self.config.get('input_delay', 0.02)
                if char.isascii() and char.isalpha():
                    time.sleep(base_delay * 2.5)  # 英文字母使用基础延迟的2.5倍（默认50ms）
                elif char == ' ':
                    time.sleep(base_delay * 1.5)  # 空格使用基础延迟的1.5倍（默认30ms）
                else:
                    time.sleep(base_delay)  # 其他字符使用基础延迟（默认20ms）
                
                if (i + 1) % 100 == 0:
                    progress = (i + 1) / char_count * 100
                    self.logger.info(f"进度: {i + 1}/{char_count} ({progress:.1f}%)")
            
            self.logger.info(f"输入完成！共输入 {char_count} 个字符")
            self.logger.info("=========================")
            
        except Exception as e:
            self.logger.error(f"自动输入失败: {e}")
    
    def clear_input_text(self):
        """清空输入框"""
        self.input_text.delete("1.0", "end")
        self.input_text.configure(text_color=("gray10", "gray90"))
        self.logger.info("已清空输入框")
    
    def start_listening(self):
        """启动键盘监听"""
        if self.is_listening:
            return
        
        self.is_listening = True
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status_label.configure(text="● 监听中", text_color="#27ae60")
        
        self.listener_thread = threading.Thread(target=self._listener_loop, daemon=True)
        self.listener_thread.start()
        
        self.logger.info("键盘监听已启动")
        self.logger.info("请使用配置的快捷键触发自动输入")
    
    def stop_listening(self):
        """停止键盘监听"""
        if not self.is_listening:
            return
        
        self.is_listening = False
        
        if self.listener:
            self.listener.stop()
        
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.status_label.configure(text="● 已停止", text_color="#e74c3c")
        
        self.logger.info("键盘监听已停止")
    
    def _listener_loop(self):
        """监听循环"""
        try:
            with keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release
            ) as listener:
                self.listener = listener
                listener.join()
        except Exception as e:
            self.logger.error(f"监听线程错误: {e}")
            self.root.after(0, self.stop_listening)
    
    def on_press(self, key):
        """监听按键按下"""
        if not self.is_listening:
            return
        
        self.current_keys.add(key)
        
        if not self.hotkey_pressed.is_set():
            for combo in self.hotkeys:
                if combo.issubset(self.current_keys):
                    self.logger.info(f"触发热键: {self._format_keys(combo)}")
                    self.hotkey_pressed.set()
                    threading.Thread(target=self.handle_hotkey, daemon=True).start()
                    break
    
    def on_release(self, key):
        """监听按键释放"""
        if key in self.current_keys:
            self.current_keys.discard(key)
    
    def _format_keys(self, keys):
        """格式化按键显示"""
        key_names = []
        for key in keys:
            if isinstance(key, KeyCode):
                key_names.append(key.char.upper() if key.char else str(key))
            else:
                key_names.append(str(key).replace('Key.', '').title())
        return ' + '.join(sorted(key_names))
    
    def handle_hotkey(self):
        """处理热键触发"""
        try:
            self.logger.info("===== 开始自动输入 =====")
            
            content = pyperclip.paste()
            char_count = len(content)
            self.logger.info(f"剪贴板内容长度: {char_count} 字符")
            
            if not content:
                self.logger.warning("剪贴板为空，无法输入")
                return
            
            time.sleep(0.2)
            
            self.logger.info("正在输入...")
            self.logger.info("提示：如果有输入法，建议切换到英文模式以获得最佳效果")
            keyboard_controller = keyboard.Controller()
            
            for i, char in enumerate(content):
                if char == '\n':
                    keyboard_controller.press(Key.enter)
                    keyboard_controller.release(Key.enter)
                elif char == '\t':
                    keyboard_controller.press(Key.tab)
                    keyboard_controller.release(Key.tab)
                elif char == ' ':
                    # 空格使用 Key.space，确保正确输入
                    keyboard_controller.press(Key.space)
                    keyboard_controller.release(Key.space)
                else:
                    try:
                        keyboard_controller.press(char)
                        keyboard_controller.release(char)
                    except Exception:
                        self.logger.warning(f"无法输入字符: {repr(char)}")
                        continue
                
                # 中英文混合时，增加延迟避免输入法干扰
                base_delay = self.config.get('input_delay', 0.02)
                if char.isascii() and char.isalpha():
                    time.sleep(base_delay * 2.5)  # 英文字母使用基础延迟的2.5倍（默认50ms）
                elif char == ' ':
                    time.sleep(base_delay * 1.5)  # 空格使用基础延迟的1.5倍（默认30ms）
                else:
                    time.sleep(base_delay)  # 其他字符使用基础延迟（默认20ms）
                
                if (i + 1) % 100 == 0:
                    progress = (i + 1) / char_count * 100
                    self.logger.info(f"进度: {i + 1}/{char_count} ({progress:.1f}%)")
            
            self.logger.info(f"输入完成！共输入 {char_count} 个字符")
            
        except Exception as e:
            self.logger.error(f"输入过程中发生错误: {e}")
        
        finally:
            time.sleep(self.debounce_time)
            self.hotkey_pressed.clear()
            self.logger.info("=========================")
    
    def test_input(self):
        """测试输入功能"""
        try:
            content = pyperclip.paste()
            if not content:
                messagebox.showwarning("警告", "剪贴板为空，请先复制一些文本")
                return
            
            self.logger.info("开始测试输入...")
            self.logger.info("将在3秒后输入前50个字符")
            
            for i in range(3, 0, -1):
                self.logger.info(f"倒计时: {i}秒")
                time.sleep(1)
            
            test_content = content[:50]
            keyboard_controller = keyboard.Controller()
            self.logger.info("提示：如果有输入法，建议切换到英文模式以获得最佳效果")
            
            for char in test_content:
                if char == '\n':
                    keyboard_controller.press(Key.enter)
                    keyboard_controller.release(Key.enter)
                elif char == '\t':
                    keyboard_controller.press(Key.tab)
                    keyboard_controller.release(Key.tab)
                elif char == ' ':
                    # 空格使用 Key.space
                    keyboard_controller.press(Key.space)
                    keyboard_controller.release(Key.space)
                else:
                    try:
                        keyboard_controller.press(char)
                        keyboard_controller.release(char)
                    except Exception:
                        continue
                
                # 中英文混合时，增加延迟避免输入法干扰
                base_delay = self.config.get('input_delay', 0.02)
                if char.isascii() and char.isalpha():
                    time.sleep(base_delay * 2.5)  # 英文字母使用基础延迟的2.5倍（默认50ms）
                elif char == ' ':
                    time.sleep(base_delay * 1.5)  # 空格使用基础延迟的1.5倍（默认30ms）
                else:
                    time.sleep(base_delay)  # 其他字符使用基础延迟（默认20ms）
            
            self.logger.info("测试完成！")
            
        except Exception as e:
            self.logger.error(f"测试失败: {e}")
            messagebox.showerror("错误", f"测试失败: {e}")
    
    def on_closing(self):
        """关闭窗口"""
        if self.is_listening:
            self.stop_listening()
        
        self.logger.info("程序已退出")
        self.root.destroy()
    
    def run(self):
        """运行程序"""
        self.root.mainloop()


class HotkeySettingsWindow(ctk.CTkToplevel):
    """快捷键设置窗口"""
    
    def __init__(self, parent_app):
        super().__init__(parent_app.root)
        
        self.parent_app = parent_app
        self.title("快捷键设置")
        self.geometry("600x500")
        
        # 录制状态
        self.is_recording = False
        self.recorded_keys = set()
        self.recording_listener = None
        self.current_editing_index = None
        
        self.create_widgets()
        
        # 绑定窗口关闭事件
        self.protocol("WM_DELETE_WINDOW", self.on_window_close)
        
        # 设置为模态窗口
        self.transient(parent_app.root)  # 设置为主窗口的子窗口
        
        # 窗口居中显示
        self.update_idletasks()  # 确保窗口尺寸已计算
        window_width = 600
        window_height = 650
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 设置窗口属性
        self.attributes('-topmost', True)  # 始终置顶
        
        # 延迟执行，确保窗口完全创建后再置顶
        self.after(10, self._ensure_on_top)
    
    def _ensure_on_top(self):
        """确保窗口在最上层"""
        try:
            self.lift()  # 提升窗口层级
            self.focus_force()  # 强制获取焦点
            self.grab_set()  # 设置为模态窗口，阻止与主窗口交互
        except Exception:
            pass
    
    def create_widgets(self):
        """创建窗口组件"""
        
        # 标题
        title_label = ctk.CTkLabel(
            self,
            text="快捷键设置",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=20)
        
        # 说明
        info_label = ctk.CTkLabel(
            self,
            text="点击 '录制' 按钮，然后按下你想设置的快捷键组合",
            font=ctk.CTkFont(size=12),
            text_color="gray60"
        )
        info_label.pack(pady=(0, 20))
        
        # 快捷键列表
        list_frame = ctk.CTkScrollableFrame(self, height=250)
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.hotkey_widgets = []
        
        for i, hotkey_config in enumerate(self.parent_app.config['hotkeys']):
            item_frame = ctk.CTkFrame(list_frame)
            item_frame.pack(fill="x", pady=5)
            
            # 序号
            ctk.CTkLabel(
                item_frame,
                text=f"{i + 1}.",
                font=ctk.CTkFont(size=13),
                width=30
            ).pack(side="left", padx=(10, 5))
            
            # 快捷键显示
            hotkey_label = ctk.CTkLabel(
                item_frame,
                text=hotkey_config['description'],
                font=ctk.CTkFont(size=13, family="Courier New"),
                anchor="w"
            )
            hotkey_label.pack(side="left", fill="x", expand=True, padx=10)
            
            # 录制按钮
            record_btn = ctk.CTkButton(
                item_frame,
                text="录制",
                command=lambda idx=i: self.start_recording(idx),
                width=80,
                height=35,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#3498db",
                hover_color="#2980b9",
                corner_radius=6
            )
            record_btn.pack(side="right", padx=5)
            
            # 删除按钮
            delete_btn = ctk.CTkButton(
                item_frame,
                text="删除",
                command=lambda idx=i: self.delete_hotkey(idx),
                width=80,
                height=35,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#e74c3c",
                hover_color="#c0392b",
                corner_radius=6
            )
            delete_btn.pack(side="right", padx=5)
            
            self.hotkey_widgets.append({
                'frame': item_frame,
                'label': hotkey_label,
                'record_btn': record_btn
            })
        
        # 添加新快捷键按钮
        add_frame = ctk.CTkFrame(list_frame)
        add_frame.pack(fill="x", pady=5)
        
        ctk.CTkButton(
            add_frame,
            text="添加新快捷键",
            command=self.add_new_hotkey,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#27ae60",
            hover_color="#229954",
            corner_radius=8
        ).pack(fill="x", padx=10, pady=5)
        
        # 高级配置区域
        advanced_frame = ctk.CTkFrame(self)
        advanced_frame.pack(fill="x", padx=20, pady=(10, 10))
        
        # 标题
        ctk.CTkLabel(
            advanced_frame,
            text="高级配置",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(15, 10), padx=15, anchor="w")
        
        # 防抖时间配置
        debounce_frame = ctk.CTkFrame(advanced_frame, fg_color="transparent")
        debounce_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(
            debounce_frame,
            text="防抖时间 (秒):",
            font=ctk.CTkFont(size=13),
            width=120,
            anchor="w"
        ).pack(side="left", padx=(0, 10))
        
        self.debounce_entry = ctk.CTkEntry(
            debounce_frame,
            width=100,
            font=ctk.CTkFont(size=13)
        )
        self.debounce_entry.pack(side="left", padx=(0, 10))
        self.debounce_entry.insert(0, str(self.parent_app.config.get('debounce_time', 0.5)))
        
        ctk.CTkLabel(
            debounce_frame,
            text="防止快捷键重复触发的间隔时间 (推荐: 0.3-1.0)",
            font=ctk.CTkFont(size=11),
            text_color="gray60"
        ).pack(side="left")
        
        # 输入速度配置
        delay_frame = ctk.CTkFrame(advanced_frame, fg_color="transparent")
        delay_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(
            delay_frame,
            text="输入延迟 (毫秒):",
            font=ctk.CTkFont(size=13),
            width=120,
            anchor="w"
        ).pack(side="left", padx=(0, 10))
        
        self.delay_entry = ctk.CTkEntry(
            delay_frame,
            width=100,
            font=ctk.CTkFont(size=13)
        )
        self.delay_entry.pack(side="left", padx=(0, 10))
        # 将秒转换为毫秒显示
        current_delay_ms = int(self.parent_app.config.get('input_delay', 0.01) * 1000)
        self.delay_entry.insert(0, str(current_delay_ms))
        
        ctk.CTkLabel(
            delay_frame,
            text="每个字符之间的延迟时间 (推荐: 10-50)",
            font=ctk.CTkFont(size=11),
            text_color="gray60"
        ).pack(side="left")
        
        # 底部说明
        ctk.CTkLabel(
            advanced_frame,
            text="注意: 延迟太小可能导致输入失败，太大则输入速度慢",
            font=ctk.CTkFont(size=11),
            text_color="#e67e22"
        ).pack(pady=(5, 15), padx=15, anchor="w")
        
        # 录制状态提示
        self.recording_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#e67e22"
        )
        self.recording_label.pack(pady=10)
        
        # 底部按钮
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        ctk.CTkButton(
            button_frame,
            text="保存",
            command=self.save_settings,
            height=50,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#27ae60",
            hover_color="#229954",
            corner_radius=8
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkButton(
            button_frame,
            text="取消",
            command=self.on_window_close,
            height=50,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#7f8c8d",
            hover_color="#95a5a6",
            corner_radius=8
        ).pack(side="right", fill="x", expand=True, padx=(10, 0))
    
    def start_recording(self, index):
        """开始录制快捷键"""
        if self.is_recording:
            messagebox.showwarning("提示", "请先完成当前录制")
            return
        
        self.is_recording = True
        self.current_editing_index = index
        self.recorded_keys.clear()
        
        # 更新UI
        self.hotkey_widgets[index]['record_btn'].configure(text="按键中...")
        self.recording_label.configure(text="请按下快捷键组合... (按 ESC 取消)")
        
        # 启动录制监听
        self.recording_listener = keyboard.Listener(
            on_press=self.on_record_press,
            on_release=self.on_record_release
        )
        self.recording_listener.start()
    
    def on_record_press(self, key):
        """录制按键按下"""
        if key == Key.esc:
            self.stop_recording(cancelled=True)
            return
        
        self.recorded_keys.add(key)
        
        # 显示当前按下的键
        keys_display = ' + '.join([
            self.parent_app.config_manager.format_key_display(k) 
            for k in self.recorded_keys
        ])
        self.recording_label.configure(text=f"当前按键: {keys_display}")
    
    def on_record_release(self, key):
        """录制按键释放"""
        # 当所有按键都释放时，完成录制
        if len(self.recorded_keys) > 0:
            # 延迟一点检查是否还有按键按下
            self.after(100, self.check_recording_complete)
    
    def check_recording_complete(self):
        """检查录制是否完成"""
        if self.is_recording and len(self.recorded_keys) > 0:
            self.stop_recording(cancelled=False)
    
    def stop_recording(self, cancelled=False):
        """停止录制"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        # 停止并清理监听器
        if self.recording_listener:
            try:
                self.recording_listener.stop()
            except Exception:
                pass
            self.recording_listener = None
        
        if not cancelled and len(self.recorded_keys) > 0:
            # 保存录制的快捷键
            keys_list = [
                self.parent_app.config_manager.key_to_string(k)
                for k in self.recorded_keys
            ]
            keys_display = ' + '.join([
                self.parent_app.config_manager.format_key_display(k)
                for k in self.recorded_keys
            ])
            
            self.parent_app.config['hotkeys'][self.current_editing_index] = {
                'keys': keys_list,
                'description': keys_display
            }
            
            # 更新显示
            self.hotkey_widgets[self.current_editing_index]['label'].configure(text=keys_display)
            self.recording_label.configure(text=f"已设置: {keys_display}")
        else:
            self.recording_label.configure(text="已取消录制")
        
        # 恢复按钮
        if self.current_editing_index is not None and self.current_editing_index < len(self.hotkey_widgets):
            self.hotkey_widgets[self.current_editing_index]['record_btn'].configure(text="录制")
        self.recorded_keys.clear()
        
        # 清空提示（添加异常处理，避免窗口已销毁时出错）
        def clear_label():
            try:
                if self.winfo_exists():
                    self.recording_label.configure(text="")
            except Exception:
                pass
        
        self.after(2000, clear_label)
    
    def add_new_hotkey(self):
        """添加新快捷键"""
        new_hotkey = {
            'keys': ['ctrl_l', 'shift', 'n'],
            'description': 'Ctrl + Shift + N (新增)'
        }
        self.parent_app.config['hotkeys'].append(new_hotkey)
        
        # 先关闭当前窗口，然后在主线程中重新打开
        self.cleanup_and_close()
        self.parent_app.root.after(100, self.parent_app.open_hotkey_settings)
    
    def delete_hotkey(self, index):
        """删除快捷键"""
        if len(self.parent_app.config['hotkeys']) <= 1:
            messagebox.showwarning("提示", "至少需要保留一个快捷键")
            return
        
        # 直接删除，不显示确认框
        del self.parent_app.config['hotkeys'][index]
        self.parent_app.logger.info(f"已删除快捷键 {index + 1}")
        
        # 先关闭当前窗口，然后在主线程中重新打开
        self.cleanup_and_close()
        self.parent_app.root.after(100, self.parent_app.open_hotkey_settings)
    
    def save_settings(self):
        """保存设置"""
        # 停止正在进行的录制
        if self.is_recording:
            self.stop_recording(cancelled=True)
        
        # 验证并保存防抖时间
        try:
            debounce_value = float(self.debounce_entry.get())
            if debounce_value < 0.1 or debounce_value > 5.0:
                self.recording_label.configure(text="错误: 防抖时间必须在 0.1-5.0 秒之间")
                return
            self.parent_app.config['debounce_time'] = debounce_value
        except ValueError:
            self.recording_label.configure(text="错误: 防抖时间必须是有效的数字")
            return
        
        # 验证并保存输入延迟
        try:
            delay_ms = float(self.delay_entry.get())
            if delay_ms < 1 or delay_ms > 1000:
                self.recording_label.configure(text="错误: 输入延迟必须在 1-1000 毫秒之间")
                return
            # 将毫秒转换为秒保存
            self.parent_app.config['input_delay'] = delay_ms / 1000
        except ValueError:
            self.recording_label.configure(text="错误: 输入延迟必须是有效的数字")
            return
        
        # 保存配置
        if self.parent_app.config_manager.save_config(self.parent_app.config):
            # 重新加载热键
            self.parent_app.hotkeys = self.parent_app.config_manager.hotkeys_from_config(
                self.parent_app.config
            )
            self.parent_app.hotkey_descriptions = [
                hk['description'] for hk in self.parent_app.config['hotkeys']
            ]
            
            # 更新防抖时间和输入延迟
            self.parent_app.debounce_time = self.parent_app.config.get('debounce_time', 0.5)
            
            # 刷新主窗口显示
            self.parent_app.refresh_hotkey_display()
            
            # 如果正在监听，重启监听
            if self.parent_app.is_listening:
                self.parent_app.logger.info("快捷键已更新，请重新启动监听使其生效")
                messagebox.showinfo("提示", "快捷键已更新！\n请重新启动监听使其生效。")
            else:
                messagebox.showinfo("成功", "快捷键设置已保存！")
            
            # 清理监听器后关闭窗口
            self.cleanup_and_close()
        else:
            messagebox.showerror("错误", "保存配置失败！")
    
    def on_window_close(self):
        """窗口关闭事件处理"""
        # 停止录制（如果正在录制）
        if self.is_recording:
            self.stop_recording(cancelled=True)
        
        # 清理并关闭
        self.cleanup_and_close()
    
    def cleanup_and_close(self):
        """清理资源并关闭窗口"""
        try:
            # 确保停止录制监听器
            if self.recording_listener is not None:
                try:
                    self.recording_listener.stop()
                    self.parent_app.logger.info("已停止快捷键录制监听器")
                except Exception as e:
                    self.parent_app.logger.warning(f"停止监听器时出错: {e}")
                finally:
                    self.recording_listener = None
            
            # 清理录制状态
            self.is_recording = False
            self.recorded_keys.clear()
            self.current_editing_index = None
            
        except Exception as e:
            self.parent_app.logger.error(f"清理资源时出错: {e}")
            print(f"清理资源时出错: {e}")
        finally:
            # 释放模态状态
            try:
                self.grab_release()
            except Exception:
                pass
            
            # 取消置顶
            try:
                self.attributes('-topmost', False)
            except Exception:
                pass
            
            # 确保窗口被销毁
            try:
                if self.winfo_exists():
                    self.destroy()
            except Exception:
                pass


def main():
    """主函数"""
    app = AutoInputGUI()
    app.run()


if __name__ == "__main__":
    main()