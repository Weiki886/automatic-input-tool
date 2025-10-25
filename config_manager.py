import json
import os
from pynput.keyboard import Key, KeyCode

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.default_config = {
            "hotkeys": [
                {"keys": ["alt_l", "g"], "description": "Alt + G"}
            ],
            "debounce_time": 0.5,
            "input_delay": 0.01
        }
    
    def load_config(self):
        """加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置失败: {e}，使用默认配置")
                return self.default_config.copy()
        else:
            return self.default_config.copy()
    
    def save_config(self, config):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def key_to_string(self, key):
        """将按键对象转换为字符串"""
        if isinstance(key, KeyCode):
            if key.char:
                return key.char.lower()
            else:
                return f"vk_{key.vk}"
        else:
            # Key枚举类型
            return str(key).replace('Key.', '').lower()
    
    def string_to_key(self, key_str):
        """将字符串转换为按键对象"""
        key_str = key_str.lower()
        
        # 尝试转换为Key枚举
        key_mapping = {
            'alt_l': Key.alt_l,
            'alt_r': Key.alt_r,
            'alt': Key.alt,
            'ctrl_l': Key.ctrl_l,
            'ctrl_r': Key.ctrl_r,
            'ctrl': Key.ctrl,
            'shift': Key.shift,
            'shift_l': Key.shift_l,
            'shift_r': Key.shift_r,
            'cmd': Key.cmd,
            'cmd_l': Key.cmd_l,
            'cmd_r': Key.cmd_r,
            'enter': Key.enter,
            'space': Key.space,
            'tab': Key.tab,
            'backspace': Key.backspace,
            'delete': Key.delete,
            'esc': Key.esc,
            'up': Key.up,
            'down': Key.down,
            'left': Key.left,
            'right': Key.right,
            'home': Key.home,
            'end': Key.end,
            'page_up': Key.page_up,
            'page_down': Key.page_down,
            'f1': Key.f1, 'f2': Key.f2, 'f3': Key.f3, 'f4': Key.f4,
            'f5': Key.f5, 'f6': Key.f6, 'f7': Key.f7, 'f8': Key.f8,
            'f9': Key.f9, 'f10': Key.f10, 'f11': Key.f11, 'f12': Key.f12,
        }
        
        if key_str in key_mapping:
            return key_mapping[key_str]
        else:
            # 单字符按键
            if len(key_str) == 1:
                return KeyCode(char=key_str)
            elif key_str.startswith('vk_'):
                # 虚拟键码
                vk = int(key_str[3:])
                return KeyCode(vk=vk)
            else:
                return KeyCode(char=key_str)
    
    def hotkeys_from_config(self, config):
        """从配置转换为热键集合列表"""
        hotkeys = []
        for hotkey_config in config.get('hotkeys', []):
            key_set = set()
            for key_str in hotkey_config['keys']:
                key_set.add(self.string_to_key(key_str))
            hotkeys.append(key_set)
        return hotkeys
    
    def format_key_display(self, key):
        """格式化按键显示名称"""
        if isinstance(key, KeyCode):
            if key.char:
                return key.char.upper()
            else:
                return f"VK_{key.vk}"
        else:
            key_str = str(key).replace('Key.', '')
            # 美化显示
            display_mapping = {
                'alt_l': 'Left Alt',
                'alt_r': 'Right Alt',
                'ctrl_l': 'Left Ctrl',
                'ctrl_r': 'Right Ctrl',
                'shift_l': 'Left Shift',
                'shift_r': 'Right Shift',
                'cmd_l': 'Left Cmd',
                'cmd_r': 'Right Cmd',
                'page_up': 'Page Up',
                'page_down': 'Page Down',
            }
            return display_mapping.get(key_str, key_str.title())

