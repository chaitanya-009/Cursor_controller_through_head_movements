import time
import platform
from abc import ABC, abstractmethod

class CursorController(ABC):
    @abstractmethod
    def move(self, x, y): pass
    
    @abstractmethod
    def click(self, x, y): pass
    
    @abstractmethod
    def double_click(self, x, y): pass
    
    @abstractmethod
    def take_screenshot(self): pass

class MacCursorController(CursorController):
    def __init__(self):
        from Quartz.CoreGraphics import (
            CGEventCreateMouseEvent, kCGEventMouseMoved,
            kCGEventLeftMouseDown, kCGEventLeftMouseUp,
            kCGHIDEventTap, CGEventPost,
            CGEventSetIntegerValueField, kCGMouseEventClickState,
            kCGMouseButtonLeft
        )
        import AppKit
        
        # Get screen dimensions first
        self.screen_width = int(AppKit.NSScreen.mainScreen().frame().size.width)
        self.screen_height = int(AppKit.NSScreen.mainScreen().frame().size.height)
        self.last_pos = (self.screen_width // 2, self.screen_height // 2)
        
        self.Quartz = {
            'create_event': CGEventCreateMouseEvent,
            'mouse_move': kCGEventMouseMoved,
            'left_down': kCGEventLeftMouseDown,
            'left_up': kCGEventLeftMouseUp,
            'post': CGEventPost,
            'set_click_count': CGEventSetIntegerValueField,
            'click_state': kCGMouseEventClickState,
            'tap': kCGHIDEventTap,
            'mouse_button': kCGMouseButtonLeft
        }

    def _get_initial_position(self):
        return (int(AppKit.NSScreen.mainScreen().frame().size.width // 2), 
                int(AppKit.NSScreen.mainScreen().frame().size.height // 2))

    def move(self, x, y):
        if (x, y) != self.last_pos:
            event = self.Quartz['create_event'](
                None, 
                self.Quartz['mouse_move'], 
                (x, y), 
                self.Quartz['mouse_button']  # Use stored constant
            )
            self.Quartz['post'](self.Quartz['tap'], event)
            self.last_pos = (x, y)

    def click(self, x, y):
        down = self.Quartz['create_event'](
            None, 
            self.Quartz['left_down'], 
            (x, y), 
            self.Quartz['mouse_button']
        )
        up = self.Quartz['create_event'](
            None, 
            self.Quartz['left_up'], 
            (x, y), 
            self.Quartz['mouse_button']
        )
        self.Quartz['post'](self.Quartz['tap'], down)
        self.Quartz['post'](self.Quartz['tap'], up)

    def double_click(self, x, y):
        # Use self.Quartz instead of self.CG
        down = self.Quartz['create_event'](
            None, 
            self.Quartz['left_down'], 
            (x, y), 
            self.Quartz['mouse_button']
        )
        up = self.Quartz['create_event'](
            None, 
            self.Quartz['left_up'], 
            (x, y), 
            self.Quartz['mouse_button']
        )
        self.Quartz['set_click_count'](down, self.Quartz['click_state'], 2)
        self.Quartz['set_click_count'](up, self.Quartz['click_state'], 2)
        self.Quartz['post'](self.Quartz['tap'], down)
        time.sleep(0.01)
        self.Quartz['post'](self.Quartz['tap'], up)

    def take_screenshot(self):
        import subprocess
        subprocess.run(["screencapture", "-x", "screenshot.png"])

class WindowsCursorController(CursorController):
    def __init__(self):
        import win32api
        import win32con
        self.win32api = win32api
        self.win32con = win32con
        self.screen_width = win32api.GetSystemMetrics(0)
        self.screen_height = win32api.GetSystemMetrics(1)
        self.last_pos = (self.screen_width // 2, self.screen_height // 2)

    def move(self, x, y):
        x = max(0, min(x, self.screen_width))
        y = max(0, min(y, self.screen_height))
        if (x, y) != self.last_pos:
            self.win32api.SetCursorPos((x, y))
            self.last_pos = (x, y)

    def click(self, x, y):
        self.win32api.mouse_event(self.win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
        self.win32api.mouse_event(self.win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)

    def double_click(self, x, y):
        self.click(x, y)
        time.sleep(0.05)
        self.click(x, y)

    def take_screenshot(self):
        import win32api
        import win32con
        # Simulate PrintScreen key press
        win32api.keybd_event(win32con.VK_SNAPSHOT, 0, 0, 0)
        win32api.keybd_event(win32con.VK_SNAPSHOT, 0, win32con.KEYEVENTF_KEYUP, 0)