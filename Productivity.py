
# -*- coding: utf-8 -*-
# Required for Kivy with non-ASCII paths/characters if needed

import os
import json
import time
import shutil
import calendar
from datetime import datetime, timedelta, timezone
import pytz
from uuid import uuid4
from dotenv import load_dotenv, set_key

# --- Kivy Imports --- #
from kivy.base import EventLoop
from kivy.core.window import Window
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
# Use FileChooserListView for a potentially simpler view, or keep FileChooserIconView
from kivy.uix.filechooser import FileChooserListView, FileChooserIconView
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.config import Config
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, DictProperty
from kivy.graphics import Color, Rectangle, Line
from kivy.utils import platform
from kivy.metrics import dp
from kivy.logger import Logger # Import Kivy logger
from kivy.uix.colorpicker import ColorPicker

# --- Groq API Imports (Modern Client) ---
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Groq library not available: {e}")
    GROQ_AVAILABLE = False

# --- Legacy Langchain Imports (Optional, for backward compatibility) ---
try:
    from langchain.chains import LLMChain
    from langchain_core.prompts import (
        ChatPromptTemplate,
        HumanMessagePromptTemplate,
        MessagesPlaceholder,
    )
    from langchain_core.messages import SystemMessage
    from langchain.chains.conversation.memory import ConversationBufferWindowMemory
    from langchain_groq import ChatGroq
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    LANGCHAIN_AVAILABLE = False

# --- Other Imports ---
import pygame
import logging

# --- Configuration & Constants ---
# Use Kivy's logger alongside Python's logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
Config.set('input', 'mouse', 'mouse,disable_multitouch')

ENV_FILE = '.env'
TASKS_FILE = os.path.join('broadcasts', 'tasks.json')
ALARM_FOLDER = 'alarm'
BACKGROUND_FOLDER = 'graphics/background'
ICON_FOLDER = 'graphics/icon'
APP_ICON_SUBFOLDER = 'app_icon'
TASK_ICON_SUBFOLDER = 'task_icons'

# Timezones
PH_TZ = pytz.timezone('Asia/Manila')
HOUSTON_TZ = pytz.timezone('America/Chicago')

# --- Initialization ---
load_dotenv(dotenv_path=ENV_FILE)
try:
    pygame.mixer.init()
except pygame.error as e:
     logging.error(f"Pygame mixer initialization failed: {e}. Sound features disabled.")

# --- Utility Functions ---
def show_error_popup(message):
    """Displays a standardized error popup."""
    try:
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        error_label = Label(text=str(message), halign='center', valign='middle', markup=True)
        error_label.bind(size=lambda *x: setattr(error_label, 'text_size', (content.width*0.95, None)))
        content.add_widget(error_label)

        ok_button = Button(text='OK', size_hint_y=None, height=dp(40))
        content.add_widget(ok_button)
        popup = Popup(title='Error', content=content, size_hint=(0.7, None), height=dp(200), auto_dismiss=False)
        ok_button.bind(on_press=popup.dismiss)
        popup.open()
    except Exception as e:
        Logger.error(f"Failed to show error popup: {e}", exc_info=True)
        logging.error(f"Failed to show error popup: {e}")

def show_confirmation_popup(message, on_confirm=None, title='Confirmation', size_hint=(0.6, 0.3)):
    """Displays a confirmation popup with an OK button."""
    try:
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        confirm_label = Label(text=str(message), halign='center', valign='middle', markup=True)
        confirm_label.bind(size=lambda *x: setattr(confirm_label, 'text_size', (content.width*0.95, None)))
        content.add_widget(confirm_label)
        confirm_button = Button(text='OK', size_hint_y=None, height=dp(40))
        content.add_widget(confirm_button)
        content.bind(minimum_height=content.setter('height'))
        popup_height = max(dp(150), content.minimum_height + dp(70))

        popup = Popup(title=title, content=content, size_hint=size_hint, height=popup_height, auto_dismiss=False)
        def confirm_action(instance):
            popup.dismiss()
            if on_confirm: on_confirm()
        confirm_button.bind(on_press=confirm_action)
        popup.open()
        return popup
    except Exception as e:
        Logger.error(f"Failed to show confirmation popup: {e}", exc_info=True)
        logging.error(f"Failed to show confirmation popup: {e}")
        return None

def format_timedelta(seconds):
    """Formats total seconds into HH:MM:SS."""
    if seconds < 0: seconds = 0
    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{secs:02}"

# --- Custom Widgets ---
class ResizableSplitter(BoxLayout):
    """A custom widget that creates resizable panels with drag handles"""
    
    def __init__(self, **kwargs):
        super().__init__(orientation='horizontal', **kwargs)
        self.left_panel = None
        self.middle_panel = None
        self.right_panel = None
        self.left_splitter = None
        self.right_splitter = None
        
        # Default proportions (can be adjusted)
        self.left_width = 0.3
        self.middle_width = 0.4
        self.right_width = 0.3
        
    def add_panels(self, left_widget, middle_widget, right_widget):
        """Add the three main panels with splitters between them"""
        self.clear_widgets()
        
        # Create left panel
        self.left_panel = left_widget
        self.left_panel.size_hint_x = self.left_width
        self.add_widget(self.left_panel)
        
        # Create left splitter handle
        self.left_splitter = self._create_splitter_handle('left')
        self.add_widget(self.left_splitter)
        
        # Create middle panel
        self.middle_panel = middle_widget
        self.middle_panel.size_hint_x = self.middle_width
        self.add_widget(self.middle_panel)
        
        # Create right splitter handle
        self.right_splitter = self._create_splitter_handle('right')
        self.add_widget(self.right_splitter)
        
        # Create right panel
        self.right_panel = right_widget
        self.right_panel.size_hint_x = self.right_width
        self.add_widget(self.right_panel)
        
    def _create_splitter_handle(self, side):
        """Create a draggable splitter handle"""
        splitter = BoxLayout(
            size_hint_x=None,
            width=dp(8),
            orientation='vertical'
        )
        
        # Visual handle
        with splitter.canvas.before:
            Color(0.7, 0.7, 0.7, 1)  # Gray color
            splitter.bg_rect = Rectangle(pos=splitter.pos, size=splitter.size)
            
        # Add visual grip lines
        with splitter.canvas:
            Color(0.5, 0.5, 0.5, 1)  # Darker gray for grip lines
            for i in range(3):
                y_offset = splitter.height * (0.3 + i * 0.15)
                splitter.grip_lines = []
                for j in range(2):
                    x_pos = splitter.x + dp(2) + j * dp(2)
                    splitter.grip_lines.append(Rectangle(pos=(x_pos, y_offset), size=(dp(1), dp(10))))
        
        # Bind position updates
        splitter.bind(pos=self._update_splitter_graphics, size=self._update_splitter_graphics)
        
        # Add drag behavior and hover effects
        splitter.bind(on_touch_down=lambda instance, touch: self._on_splitter_touch_down(instance, touch, side))
        splitter.bind(on_touch_move=lambda instance, touch: self._on_splitter_touch_move(instance, touch, side))
        splitter.bind(on_touch_up=lambda instance, touch: self._on_splitter_touch_up(instance, touch, side))
        
        # Add hover effect for better UX
        def on_mouse_pos(window, pos):
            if splitter.collide_point(*pos):
                Window.set_system_cursor('size_we')
            elif not hasattr(splitter, 'is_dragging') or not splitter.is_dragging:
                Window.set_system_cursor('arrow')
        
        Window.bind(mouse_pos=on_mouse_pos)
        
        return splitter
        
    def _update_splitter_graphics(self, instance, value):
        """Update splitter visual elements when position/size changes"""
        if hasattr(instance, 'bg_rect'):
            instance.bg_rect.pos = instance.pos
            instance.bg_rect.size = instance.size
            
    def _on_splitter_touch_down(self, instance, touch, side):
        """Handle splitter touch down event"""
        if instance.collide_point(*touch.pos):
            touch.grab_current = instance
            instance.drag_start_x = touch.x
            instance.drag_side = side
            Window.set_system_cursor('size_we')  # Resize cursor
            return True
        return False
        
    def _on_splitter_touch_move(self, instance, touch, side):
        """Handle splitter drag movement"""
        if touch.grab_current == instance:
            delta_x = touch.x - instance.drag_start_x
            self._resize_panels(side, delta_x)
            instance.drag_start_x = touch.x
            return True
        return False
        
    def _resize_panels(self, side, delta_x):
        """Resize panels based on splitter movement"""
        if not self.parent:
            return
            
        # Calculate delta as percentage of total width
        total_width = self.width - dp(16)  # Account for splitter widths
        if total_width <= 0:
            return
            
        delta_percent = delta_x / total_width
        
        # Minimum panel widths (as percentages)
        min_width = 0.15
        
        if side == 'left':
            # Moving left splitter affects left and middle panels
            new_left = max(min_width, min(0.7, self.left_width + delta_percent))
            new_middle = max(min_width, self.middle_width - delta_percent)
            
            # Ensure we don't exceed bounds
            if new_left + new_middle + self.right_width <= 1.0:
                self.left_width = new_left
                self.middle_width = new_middle
                
        elif side == 'right':
            # Moving right splitter affects middle and right panels
            new_middle = max(min_width, min(0.7, self.middle_width + delta_percent))
            new_right = max(min_width, self.right_width - delta_percent)
            
            # Ensure we don't exceed bounds
            if self.left_width + new_middle + new_right <= 1.0:
                self.middle_width = new_middle
                self.right_width = new_right
        
        # Apply new sizes
        self._apply_panel_sizes()
        
    def _on_splitter_touch_up(self, instance, touch, side):
        """Handle splitter touch up event"""
        if touch.grab_current == instance:
            touch.ungrab(instance)
            Window.set_system_cursor('arrow')  # Reset cursor to default
            return True
        return False
        
    def _apply_panel_sizes(self):
        """Apply the current size ratios to the panels"""
        if self.left_panel:
            self.left_panel.size_hint_x = self.left_width
        if self.middle_panel:
            self.middle_panel.size_hint_x = self.middle_width
        if self.right_panel:
            self.right_panel.size_hint_x = self.right_width

class ColorCyclingLabel(Label):
    colors = [
        (1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1), # RGB
        (0, 0, 0, 1), (1, 1, 1, 1)             # Black, White
    ]
    def __init__(self, date_str=None, app_ref=None, **kwargs):
        super().__init__(**kwargs)
        self.color_index = 3 # Start black
        self.override = False
        self.color = self.colors[self.color_index]
        self.halign = 'center'
        self.valign = 'middle'
        self.bind(size=self._update_text_size)
        self.date_str = date_str
        self.app_ref = app_ref
    def _update_text_size(self, *args):
        self.text_size = (self.width, None)
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.color_index = (self.color_index + 1) % len(self.colors)
            self.color = self.colors[self.color_index]
            self.override = True
            # Save the color to app_ref.date_colors if available
            if self.app_ref and self.date_str:
                self.app_ref.date_colors[self.date_str] = list(self.color)
                self.app_ref.save_tasks(force=True)
            return True
        return super().on_touch_down(touch)

class ColorCyclingIcon(Image):
    colors = [
        (1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1), # RGB
        (0, 0, 0, 1), (1, 1, 1, 1)             # Black, White
    ]
    def __init__(self, task_ref=None, app_ref=None, icon_key='calendar_icon_color', **kwargs):
        kwargs.setdefault('allow_stretch', True)
        kwargs.setdefault('keep_ratio', True)
        super().__init__(**kwargs)
        self.task_ref = task_ref
        self.app_ref = app_ref
        self.icon_key = icon_key
        # Determine initial color index
        initial_color = (task_ref.get(icon_key) if task_ref and icon_key in task_ref else None)
        if initial_color and isinstance(initial_color, (list, tuple)) and len(initial_color) == 4:
            try:
                self.color_index = self.colors.index(tuple(initial_color))
            except ValueError:
                self.color_index = 3 # default black
        else:
            self.color_index = 3 # default black
        self.color = self.colors[self.color_index]
        with self.canvas.before:
            self.overlay_color = Color(rgba=(self.color[0], self.color[1], self.color[2], 0.5))  # Set overlay to current color
            self.overlay_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.color_index = (self.color_index + 1) % len(self.colors)
            self.overlay_color.rgba = (self.colors[self.color_index][0], self.colors[self.color_index][1], self.colors[self.color_index][2], 0.5)
            # Save to task dict and persist
            if self.task_ref is not None:
                self.task_ref[self.icon_key] = list(self.colors[self.color_index])
                if self.app_ref:
                    if hasattr(self.app_ref, 'mark_tasks_changed'):
                        self.app_ref.mark_tasks_changed()
                    self.app_ref.save_tasks(force=True)
                    # Instantly update both views (task list and calendar)
                    if hasattr(self.app_ref, 'update_task_view'):
                        self.app_ref.update_task_view()
            return True
        return super().on_touch_down(touch)
    def update_rect(self, instance, value):
        self.overlay_rect.pos = self.pos
        self.overlay_rect.size = self.size

class CalendarWidget(GridLayout):
    def __init__(self, year, month, tasks_provider, gratitude_provider=None, **kwargs):
        # Set default size_hint to fill available space
        kwargs.setdefault('size_hint', (1, 1))
        super().__init__(cols=7, spacing=dp(2), padding=dp(2), **kwargs)
        self.year = year
        self.month = month
        self.tasks_provider = tasks_provider
        self.gratitude_provider = gratitude_provider
        self.global_text_color = (0, 0, 0, 1)  # Default to black
        self.global_date_number_color = (0, 0, 0, 1)  # Default to black
        # Bind to size changes to ensure proper scaling
        self.bind(size=self._update_layout)
        self.populate_calendar()

    def set_global_text_color(self, header_color, date_number_color=None):
        self.global_text_color = header_color
        if date_number_color is not None:
            self.global_date_number_color = date_number_color
        self.populate_calendar()

    def _update_layout(self, *args):
        # Force recalculation of cell sizes when widget size changes
        Clock.schedule_once(lambda dt: self.populate_calendar(), 0)
        
    def populate_calendar(self):
        self.clear_widgets()
        tasks = self.tasks_provider()
        
        # Calculate cell size based on available space
        cell_width = self.width / 7  # 7 columns
        num_weeks = 6  # Maximum possible weeks in a month view
        cell_height = self.height / (num_weeks + 1)  # +1 for header row
        
        # Add day headers with proper sizing (Sunday first)
        day_headers = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for day in day_headers:
            header = Label(text=day, color=self.global_text_color, size_hint=(1/7, None), height=cell_height/2)
            self.add_widget(header)
            
        try:
            # Set firstweekday to Sunday (6)
            cal = calendar.Calendar(firstweekday=6)
            month_calendar = cal.monthdayscalendar(self.year, self.month)
            today = datetime.now().date()
        except ValueError:
            logging.error(f"Invalid year/month for calendar: {self.year}/{self.month}")
            self.add_widget(Label(text="Invalid Date"))
            return
        
        # Pre-process tasks to create a date-to-tasks mapping for faster lookups
        date_to_tasks = {}
        for task in tasks:
            if task.get('due_date') and task.get('icon'):  # Check for both due date AND icon
                try:
                    # Parse date once per task
                    due_date_str = task['due_date'].strip()
                    due_dt = datetime.strptime(due_date_str, '%d-%B-%Y').date()
                    date_key = due_dt.strftime('%Y-%m-%d')
                    
                    # Only add tasks with valid icons
                    if os.path.exists(task['icon']):
                        if date_key not in date_to_tasks:
                            date_to_tasks[date_key] = []
                        date_to_tasks[date_key].append(task)
                    else:
                        logging.debug(f"Icon path '{task['icon']}' for task '{task.get('task')}' not found.")
                except ValueError:
                    # Skip invalid dates silently in release mode
                    pass
                except Exception as e:
                    logging.debug(f"Error processing due date {task.get('due_date')}: {e}")
        
        # Pre-fetch gratitude entries once
        gratitude_entries = self.gratitude_provider() if self.gratitude_provider else {}
        app_ref = App.get_running_app()
        
        # Add day cells
        for week in month_calendar:
            for day in week:
                if day == 0:
                    self.add_widget(BoxLayout(size_hint=(1/7, None), height=cell_height))
                    continue
                    
                # Create day cell with proper sizing
                day_cell = FloatLayout(size_hint=(1/7, None), height=cell_height)
                
                try:
                    day_date = datetime(self.year, self.month, day).date()
                except ValueError:
                    self.add_widget(Label(text="X"))
                    continue
                    
                # Day number label with relative sizing
                date_str = day_date.strftime('%Y-%m-%d')
                # Pass date_str and app_ref to ColorCyclingLabel
                day_number_label = ColorCyclingLabel(
                    text=str(day),
                    size_hint=(0.8, 0.3),
                    pos_hint={'top': 0.95, 'center_x': 0.5},
                    font_size=max(10, min(16, cell_width/5)),  # Responsive font size
                    date_str=date_str,
                    app_ref=app_ref
                )
                # --- Left click cycles color, right click creates new task ---
                def on_day_click(instance, touch, the_date=date_str):
                    if not instance.collide_point(*touch.pos):
                        return False
                    if touch.button == 'left':
                        # Call the label's on_touch_down to cycle color
                        return ColorCyclingLabel.on_touch_down(instance, touch)
                    elif touch.button == 'right':
                        app = App.get_running_app()
                        if hasattr(app, 'prompt_new_task_for_date'):
                            app.prompt_new_task_for_date(the_date)
                        return True
                    return False
                day_number_label.bind(on_touch_down=on_day_click)

                # Set label color to per-date override if present
                if app_ref and hasattr(app_ref, 'date_colors') and date_str in app_ref.date_colors:
                    day_number_label.color = app_ref.date_colors[date_str]
                    day_number_label.override = True
                elif not hasattr(day_number_label, 'color_index') or day_number_label.color_index is None or not getattr(day_number_label, 'override', False):
                    day_number_label.color = self.global_date_number_color
                day_cell.add_widget(day_number_label)
                
                # Highlight today's date
                if day_date == today:
                    with day_cell.canvas.before:
                        Color(1, 0, 0, 0.25)
                        day_cell.highlight_rect = Rectangle(pos=day_cell.pos, size=day_cell.size)
                    def update_rect(instance, value):
                        if hasattr(instance, 'highlight_rect'):
                            instance.highlight_rect.pos = instance.pos
                            instance.highlight_rect.size = instance.size
                    day_cell.bind(pos=update_rect, size=update_rect)
                
                # Get matching tasks from our pre-processed dictionary
                matching_tasks = date_to_tasks.get(date_str, [])
                
                # Check for gratitude entries on this day
                has_gratitude = date_str in gratitude_entries
                
                # Only create layout if we have icons or gratitude to show
                if matching_tasks or has_gratitude:
                    # Add task icons and gratitude indicator
                    icons_layout = BoxLayout(
                        orientation='horizontal',
                        spacing=dp(1),
                        size_hint=(0.9, 0.4),
                        pos_hint={'center_y': 0.3, 'center_x': 0.5}  # Adjusted position to be more centered in the cell
                    )
                    
                    # Calculate icon size based on cell dimensions
                    icon_size_dp = max(10, min(20, cell_width/5))
                    icon_size = (icon_size_dp, icon_size_dp)
                    
                    # Add gratitude indicator if present
                    if has_gratitude:
                        gratitude_label = Label(
                            text="♥",  # Heart symbol for gratitude
                            color=(1, 0.4, 0.4, 1),  # Pinkish-red color
                            font_size=icon_size_dp * 1.2,
                            size_hint=(None, None),
                            size=icon_size
                        )
                        icons_layout.add_widget(gratitude_label)
                    
                    # Add task icons if any
                    if matching_tasks:
                        # Determine how many icons can fit
                        max_icons = min(3, len(matching_tasks))  # Limit to 3 icons max for readability
                        for i, t in enumerate(matching_tasks):
                            if i >= max_icons:
                                break
                            icon_path = t['icon']
                            try:
                                icon = ColorCyclingIcon(
                                    source=icon_path,
                                    size_hint=(None, None),
                                    size=icon_size,
                                    task_ref=t,
                                    app_ref=app_ref
                                )
                                # Set color from task dict if present
                                icon_color = t.get('calendar_icon_color')
                                if icon_color and isinstance(icon_color, (list, tuple)) and len(icon_color) == 4:
                                    icon.color = icon_color
                                icons_layout.add_widget(icon)
                            except Exception as img_err:
                                logging.debug(f"Failed to load icon image {icon_path} for calendar: {img_err}")
                    
                    day_cell.add_widget(icons_layout)
                
                self.add_widget(day_cell)

# --- Main Application Class ---
class ProductivityApp(App):
    calendar_text_color = ObjectProperty((0, 0, 0, 1))  # Default to black
    calendar_date_number_color = ObjectProperty((0, 0, 0, 1))  # Default to black for date numbers
    timer_label_color = ObjectProperty((0, 0, 0, 1))  # Default to black for timer labels
    timer_colors = DictProperty({})  # { task_index: [r, g, b, a] }
    stop_timer_colors = DictProperty({})  # { task_index: [r, g, b, a] }
    date_colors = DictProperty({})  # { 'YYYY-MM-DD': [r, g, b, a] }

    tasks = ObjectProperty([])
    selected_index = ObjectProperty(None, allownone=True)
    last_click_time = ObjectProperty(None, allownone=True)
    last_click_index = ObjectProperty(None, allownone=True)
    minimized = BooleanProperty(False)
    is_dark_mode = BooleanProperty(False)
    background_image_path = StringProperty(None, allownone=True)
    tasks_changed = BooleanProperty(False)
    task_widgets = DictProperty({})
    timer_labels = DictProperty({})
    scheduled_alarms = DictProperty({})
    gratitude_entries = ObjectProperty({})

    _manual_time_mode = BooleanProperty(False)
    _manual_time_offset = ObjectProperty(timedelta(0))

    _setup_popup = ObjectProperty(None, allownone=True)
    _background_spinner = ObjectProperty(None, allownone=True)
    _annotation_popup = ObjectProperty(None, allownone=True)
    _gratitude_popup = ObjectProperty(None, allownone=True)
    # Removed _icon_selector_popup


    def build(self):
        Window.bind(on_request_close=self.on_request_close)
        self.setup_directories()
        self.load_app_icon()
        self.tasks = self.load_tasks()
        self.gratitude_entries = self.load_gratitude_entries()
        # Load minimize mode color preference
        self._load_minimize_color_preference()
        # Removed: self._load_and_apply_background() # Moved down
        self.check_and_resume_timers()
        self._reschedule_pending_alarms()
        self.root = self.create_main_layout() # Create root layout first
        self._load_and_apply_background() # Load and apply background AFTER
        self.apply_theme()
        self.update_task_view()
        # Optimize timer updates - only update when needed
        self._last_timer_update = 0
        self._timer_update_interval = 0.5  # Update every 500ms instead of 1000ms for smoother display
        Clock.schedule_interval(self.update_timers_and_display, self._timer_update_interval)
        Clock.schedule_interval(self.update_live_time_displays, 2)  # Update time displays less frequently
        Clock.schedule_interval(self.save_tasks_periodically, 300)
        logging.info("Application built successfully.")
        # Force a window resize event to trigger layout updates (fixes distortion)
        Window.size = Window.size
        return self.root

    def _load_and_apply_background(self):
        saved_path = os.getenv('BACKGROUND_IMAGE_PATH')
        if saved_path and os.path.exists(saved_path): self._apply_background_image(saved_path)
        else: self._apply_background_image(self.find_background_image())

    def _apply_background_image(self, image_path):
        self.background_image_path = None
        root = self.root_layout if hasattr(self, 'root_layout') else self.root
        if hasattr(self, 'background_widget') and self.background_widget and self.background_widget.parent: self.background_widget.parent.remove_widget(self.background_widget); self.background_widget = None
        if hasattr(self, 'bg_rect') and self.bg_rect:
             if root and hasattr(root.canvas, 'before'):
                 if self.bg_rect in root.canvas.before.children: root.canvas.before.remove(self.bg_rect)
                 if hasattr(self, 'bg_color') and self.bg_color in root.canvas.before.children: root.canvas.before.remove(self.bg_color)
             self.bg_rect = None; self.bg_color = None
        if image_path and os.path.exists(image_path):
            try:
                if not root: self.background_image_path = image_path; return
                self.background_widget = Image(source=image_path, allow_stretch=True, keep_ratio=False, size=root.size)
                root.add_widget(self.background_widget, index=len(root.children))
                self.background_image_path = image_path; logging.info(f"Applied background image: {image_path}")
                if hasattr(self, 'content_layout') and self.content_layout.parent: root.remove_widget(self.content_layout); root.add_widget(self.content_layout)
            except Exception as e: logging.error(f"Failed to apply background image {image_path}: {e}"); show_error_popup(f"Error loading background:\n{os.path.basename(image_path)}"); self._apply_default_background_color()
        else: logging.info("Applying default background color (no valid image path)."); self._apply_default_background_color()

    def _apply_default_background_color(self):
         self.background_image_path = None
         root = self.root_layout if hasattr(self, 'root_layout') else self.root
         if root:
             if hasattr(self, 'background_widget') and self.background_widget and self.background_widget.parent: self.background_widget.parent.remove_widget(self.background_widget); self.background_widget = None
             if not hasattr(self, 'bg_rect') or not self.bg_rect:
                 with root.canvas.before:
                     bg_rgba = (0.15, 0.15, 0.15, 1) if self.is_dark_mode else (0.95, 0.95, 0.95, 1)
                     self.bg_color = Color(*bg_rgba)
                     self.bg_rect = Rectangle(size=root.size, pos=root.pos)
                 root.bind(size=lambda *args: setattr(self.bg_rect, 'size', root.size) if hasattr(self, 'bg_rect') and self.bg_rect else None,
                           pos=lambda *args: setattr(self.bg_rect, 'pos', root.pos) if hasattr(self, 'bg_rect') and self.bg_rect else None)
             self.apply_theme()

    def on_stop(self):
        logging.info("Application stopping.")
        self.save_tasks(force=True)
        self.save_gratitude_entries()
        try:
            if pygame.mixer.get_init(): pygame.mixer.music.stop()
        except pygame.error as e: logging.warning(f"Pygame error stopping music on exit: {e}")
        pygame.mixer.quit(); logging.info("Tasks saved and Pygame mixer quit.")

    def on_request_close(self, *args, **kwargs):
        self.save_tasks(force=True); 
        self.save_gratitude_entries();
        logging.info("Window close requested, tasks and gratitude entries saved."); 
        return False

    def setup_directories(self):
        folders = [ALARM_FOLDER, BACKGROUND_FOLDER, ICON_FOLDER, os.path.join(ICON_FOLDER, APP_ICON_SUBFOLDER), os.path.join(ICON_FOLDER, TASK_ICON_SUBFOLDER)]
        for folder in folders:
            if not os.path.exists(folder):
                try: os.makedirs(folder); logging.info(f"Created directory: {folder}")
                except OSError as e: logging.error(f"Failed to create directory {folder}: {e}"); show_error_popup(f"Could not create directory:\n{folder}\nApp may not function correctly.")

    def load_app_icon(self):
        app_icon_dir = os.path.join(ICON_FOLDER, APP_ICON_SUBFOLDER)
        try:
            preferred_icon = None
            if platform == 'win': preferred_icon = next((f for f in os.listdir(app_icon_dir) if f.lower().endswith('.ico')), None)
            elif platform == 'macosx': preferred_icon = next((f for f in os.listdir(app_icon_dir) if f.lower().endswith('.icns')), None)
            if preferred_icon: icon_path = os.path.join(app_icon_dir, preferred_icon)
            else: icons = [f for f in os.listdir(app_icon_dir) if f.lower().endswith(('.png', '.ico', '.icns'))]; icon_path = os.path.join(app_icon_dir, sorted(icons)[0]) if icons else None
            if icon_path and os.path.exists(icon_path): self.icon = icon_path; logging.info(f"App icon set to: {self.icon}")
            else: logging.warning(f"No suitable application icon found in {app_icon_dir}")
        except FileNotFoundError: logging.warning(f"App icon directory not found: {app_icon_dir}")
        except Exception as e: logging.error(f"Error setting app icon: {e}", exc_info=True)

    def load_tasks(self):
        try:
            with open(TASKS_FILE, 'r') as file:
                data = json.load(file)
                # Support old format (list of tasks)
                if isinstance(data, list):
                    tasks_data = data
                    meta = {}
                else:
                    tasks_data = data.get('tasks', [])
                    meta = data
                # Load user display name if present
                self.user_display_name = meta.get('user_display_name', '')
                # Load global colors
                self.calendar_text_color = tuple(meta.get('calendar_text_color', (0, 0, 0, 1)))
                self.calendar_date_number_color = tuple(meta.get('calendar_date_number_color', (0, 0, 0, 1)))
                self.timer_label_color = tuple(meta.get('timer_label_color', (0, 0, 0, 1)))
                self.timer_colors = meta.get('timer_colors', {})
                self.stop_timer_colors = meta.get('stop_timer_colors', {})
                self.date_colors = meta.get('date_colors', {})
                # After loading, update calendar widget if it exists
                if hasattr(self, 'calendar_widget') and self.calendar_widget:
                    self.calendar_widget.set_global_text_color(self.calendar_text_color, self.calendar_date_number_color)
                loaded_tasks = []; now_iso = datetime.now().isoformat()
                for i, task in enumerate(tasks_data):
                    try:
                        if 'task' not in task or not str(task['task']).strip():
                            if 'titleHistory' in task and task['titleHistory'] and isinstance(task['titleHistory'], list) and task['titleHistory'][-1].get('title'): task['task'] = task['titleHistory'][-1]['title']
                            else: task['task'] = f'Untitled Task {i+1}'; logging.warning(f"Task {i} had missing/empty title, assigned fallback.")
                        task.setdefault('timer_running', False); task.setdefault('completed', False); task.setdefault('annotations', []); task.setdefault('alarms', []); task.setdefault('timer', 0); task.setdefault('start_time_unix', None); task.setdefault('due_date', None); task.setdefault('icon', None); task.setdefault('localTime', datetime.now(PH_TZ).strftime('%Y-%m-%d %H:%M:%S %Z')); task.setdefault('createdAt', now_iso); task.setdefault('titleHistory', []); task.setdefault('subtasks', []); task.setdefault('subtasks_visible', True)
                        # Initialize subtasks recursively
                        self._initialize_subtasks(task)
                        if not isinstance(task.get('timer'), (int, float)): task['timer'] = 0
                        if not isinstance(task.get('start_time_unix'), (int, float, type(None))): task['start_time_unix'] = None
                        if not isinstance(task.get('annotations'), list): task['annotations'] = []
                        if not isinstance(task.get('alarms'), list): task['alarms'] = []
                        if not isinstance(task.get('due_date'), (str, type(None))): task['due_date'] = None
                        if not isinstance(task.get('icon'), (str, type(None))): task['icon'] = None
                        if not isinstance(task.get('completed'), bool): task['completed'] = False
                        if not isinstance(task.get('titleHistory'), list): task['titleHistory'] = []
                        valid_alarms = []
                        if isinstance(task.get('alarms'), list):
                            for alarm_index, alarm_entry in enumerate(task['alarms']):
                                if isinstance(alarm_entry, dict):
                                    alarm_entry.setdefault('target_timestamp_unix', None); alarm_entry.setdefault('sound_file', None); alarm_entry.setdefault('enabled', False); alarm_entry.setdefault('id', f"{i}_{alarm_index}_{time.time()}_{uuid4().hex[:6]}")
                                    if alarm_entry.get('target_timestamp_unix') and alarm_entry.get('sound_file'): valid_alarms.append(alarm_entry)
                                    else: logging.warning(f"Skipping invalid alarm entry in task {i}: {alarm_entry}")
                        task['alarms'] = valid_alarms
                        if not task['titleHistory'] or task['titleHistory'][-1].get('title') != task['task']: task['titleHistory'].append({'title': task['task'], 'timestamp': task.get('createdAt', now_iso)})
                        for entry in task['titleHistory']: entry.setdefault('timestamp', now_iso)
                        if 'start_time' in task and isinstance(task.get('start_time'), (int, float)):
                            if task['start_time_unix'] is None: task['start_time_unix'] = task['start_time']
                            task.pop('start_time', None)
                        loaded_tasks.append(task)
                    except Exception as task_err: logging.error(f"Error processing task at index {i}: {task_err}. Skipping task: {task}", exc_info=True)
                logging.info(f"Loaded {len(loaded_tasks)} tasks from {TASKS_FILE}. user_display_name: {getattr(self, 'user_display_name', None)}"); return loaded_tasks
        except FileNotFoundError: logging.warning(f"{TASKS_FILE} not found. Starting with an empty task list."); return []
        except json.JSONDecodeError as e: logging.error(f"Error decoding {TASKS_FILE}: {e}. Starting empty.", exc_info=True); show_error_popup(f"Error reading tasks file:\n{TASKS_FILE}\nStarting with empty list."); return []
        except Exception as e: logging.error(f"Unexpected error loading tasks: {e}", exc_info=True); show_error_popup(f"Failed to load tasks.\nSee console for details.\nStarting empty list."); return []

    def _initialize_subtasks(self, task):
        """Recursively initialize subtasks with default values"""
        if 'subtasks' not in task:
            task['subtasks'] = []
        
        now_iso = datetime.now().isoformat()
        for subtask in task['subtasks']:
            subtask.setdefault('timer_running', False)
            subtask.setdefault('completed', False)
            subtask.setdefault('annotations', [])
            subtask.setdefault('alarms', [])
            subtask.setdefault('timer', 0)
            subtask.setdefault('start_time_unix', None)
            subtask.setdefault('due_date', None)
            subtask.setdefault('icon', None)
            subtask.setdefault('localTime', datetime.now(PH_TZ).strftime('%Y-%m-%d %H:%M:%S %Z'))
            subtask.setdefault('createdAt', now_iso)
            subtask.setdefault('titleHistory', [])
            subtask.setdefault('subtasks', [])
            
            # Recursively initialize nested subtasks
            self._initialize_subtasks(subtask)

    def add_subtask(self, parent_task, subtask_name):
        """Add a subtask to a parent task"""
        if not subtask_name or not subtask_name.strip():
            show_error_popup("Subtask name cannot be empty.")
            return
        
        try:
            now_iso = datetime.now().isoformat()
            new_subtask = {
                'task': subtask_name.strip(),
                'timer': 0,
                'localTime': datetime.now(PH_TZ).strftime('%Y-%m-%d %H:%M:%S %Z'),
                'createdAt': now_iso,
                'timer_running': False,
                'start_time_unix': None,
                'completed': False,
                'due_date': None,
                'icon': None,
                'alarms': [],
                'annotations': [],
                'titleHistory': [{'title': subtask_name.strip(), 'timestamp': now_iso}],
                'subtasks': []
            }
            
            if 'subtasks' not in parent_task:
                parent_task['subtasks'] = []
            
            parent_task['subtasks'].append(new_subtask)
            self.mark_tasks_changed()
            self.update_task_view()
            logging.info(f"Added subtask: {subtask_name} to parent task: {parent_task.get('task', 'Unknown')}")
            
        except Exception as e:
            logging.error(f"Error adding subtask '{subtask_name}': {e}", exc_info=True)
            show_error_popup("Failed to add the subtask.")

    def delete_subtask(self, parent_task, subtask_index):
        """Delete a subtask from a parent task"""
        try:
            if 'subtasks' not in parent_task or not (0 <= subtask_index < len(parent_task['subtasks'])):
                show_error_popup("Invalid subtask index.")
                return
            
            subtask_to_delete = parent_task['subtasks'][subtask_index]
            subtask_name = subtask_to_delete.get('task', 'Unknown')
            
            # Cancel any alarms for this subtask
            for alarm in subtask_to_delete.get('alarms', []):
                alarm_id = alarm.get('id')
                if alarm_id:
                    event = self.scheduled_alarms.pop(alarm_id, None)
                    if event:
                        event.cancel()
                        logging.info(f"Cancelled alarm {alarm_id} for subtask being deleted.")
            
            del parent_task['subtasks'][subtask_index]
            self.mark_tasks_changed()
            self.update_task_view()
            logging.info(f"Deleted subtask: {subtask_name}")
            
        except Exception as e:
            logging.error(f"Error deleting subtask at index {subtask_index}: {e}", exc_info=True)
            show_error_popup("Failed to delete the subtask.")

    def toggle_subtask_completion(self, subtask):
        """Toggle completion status of a subtask"""
        try:
            subtask['completed'] = not subtask.get('completed', False)
            self.mark_tasks_changed()
            self.update_task_view()
            logging.info(f"Toggled subtask completion: {subtask.get('task', 'Unknown')} -> {subtask['completed']}")
        except Exception as e:
            logging.error(f"Error toggling subtask completion: {e}", exc_info=True)
            show_error_popup("Failed to toggle subtask completion.")

    def get_subtask_completion_stats(self, task):
        """Get completion statistics for a task's subtasks"""
        if 'subtasks' not in task or not task['subtasks']:
            return 0, 0  # completed, total
        
        total = len(task['subtasks'])
        completed = sum(1 for subtask in task['subtasks'] if subtask.get('completed', False))
        return completed, total

    def _create_subtasks_container(self, parent_index, parent_task):
        """Create UI container for displaying and managing subtasks"""
        container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(1))
        container.bind(minimum_height=container.setter('height'))
        
        # Add existing subtasks
        for subtask_index, subtask in enumerate(parent_task.get('subtasks', [])):
            subtask_row = self._create_subtask_row(parent_index, subtask_index, subtask, parent_task)
            container.add_widget(subtask_row)
        
        return container

    def _create_subtask_row(self, parent_index, subtask_index, subtask, parent_task):
        """Create a single subtask row"""
        row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(35), spacing=dp(5))
        row.padding = (dp(30), dp(2), dp(5), dp(2))  # Indent subtasks
        
        # Completion checkbox
        checkbox = Button(
            text='✓' if subtask.get('completed', False) else '',
            size_hint=(None, None),
            size=(dp(25), dp(25)),
            background_normal='',
            background_color=(0.8, 1, 0.8, 1) if subtask.get('completed', False) else (1, 1, 1, 1)
        )
        def toggle_completion(instance):
            self.toggle_subtask_completion(subtask)
        checkbox.bind(on_press=toggle_completion)
        row.add_widget(checkbox)
        
        # Subtask title
        title = subtask.get('task', 'Untitled Subtask')
        title_display = f"[s]{title}[/s]" if subtask.get('completed', False) else title
        
        subtask_label = Label(
            text=title_display,
            markup=True,
            halign='left',
            valign='middle',
            font_size=dp(12),
            color=(0, 0, 0, 1)  # Black text
        )
        subtask_label.bind(size=lambda *args: setattr(subtask_label, 'text_size', (subtask_label.width, None)))
        row.add_widget(subtask_label)
        
        # Delete subtask button
        delete_btn = Button(
            text='×',
            size_hint=(None, None),
            size=(dp(25), dp(25)),
            background_color=(1, 0.7, 0.7, 1)
        )
        def delete_subtask_action(instance):
            self.delete_subtask(parent_task, subtask_index)
        delete_btn.bind(on_press=delete_subtask_action)
        row.add_widget(delete_btn)
        
        # Add subtask button (for nested subtasks)
        add_nested_btn = Button(
            text='+',
            size_hint=(None, None),
            size=(dp(25), dp(25)),
            background_color=(0.8, 0.8, 1, 1)
        )
        def add_nested_subtask_action(instance):
            self._show_add_subtask_popup(subtask)
        add_nested_btn.bind(on_press=add_nested_subtask_action)
        row.add_widget(add_nested_btn)
        
        return row

    def _show_add_subtask_popup(self, parent_task):
        """Show popup to add a new subtask"""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        subtask_input = TextInput(
            hint_text='Enter subtask name',
            multiline=False,
            size_hint_y=None,
            height=dp(40)
        )
        content.add_widget(subtask_input)
        
        button_layout = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        
        save_button = Button(text='Add')
        cancel_button = Button(text='Cancel')
        
        button_layout.add_widget(save_button)
        button_layout.add_widget(cancel_button)
        content.add_widget(button_layout)
        
        popup = Popup(
            title='Add Subtask',
            content=content,
            size_hint=(0.7, None),
            height=dp(180),
            auto_dismiss=False
        )
        
        def save_action(instance):
            subtask_name = subtask_input.text.strip()
            if subtask_name:
                self.add_subtask(parent_task, subtask_name)
                popup.dismiss()
            else:
                show_error_popup("Subtask name cannot be empty.")
        
        def cancel_action(instance):
            popup.dismiss()
        
        save_button.bind(on_press=save_action)
        cancel_button.bind(on_press=cancel_action)
        
        # Allow Enter key to save
        def on_text_validate(instance):
            save_action(instance)
        subtask_input.bind(on_text_validate=on_text_validate)
        
        popup.open()

    def save_tasks(self, force=False):
        # Always save meta (colors, date_colors) and tasks
        if not self.tasks_changed and not force: return
        tasks_to_save = []
        for idx, task in enumerate(self.tasks):
            task_copy = task.copy()
            # Debug logging for growth-prone fields
            logging.debug(f"Task {idx}: titleHistory={len(task_copy.get('titleHistory', []))}, annotations={len(task_copy.get('annotations', []))}, alarms={len(task_copy.get('alarms', []))}")
            if not isinstance(task_copy.get('timer'), (int, float)): task_copy['timer'] = 0
            if not isinstance(task_copy.get('start_time_unix'), (int, float, type(None))): task_copy['start_time_unix'] = None
            if not isinstance(task_copy.get('annotations'), list): task_copy['annotations'] = []
            if not isinstance(task_copy.get('alarms'), list): task_copy['alarms'] = []
            if not isinstance(task_copy.get('due_date'), (str, type(None))): task_copy['due_date'] = None
            if not isinstance(task_copy.get('icon'), (str, type(None))): task_copy['icon'] = None
            if not isinstance(task_copy.get('completed'), bool): task_copy['completed'] = False
            if not isinstance(task_copy.get('titleHistory'), list): task_copy['titleHistory'] = []
            tasks_to_save.append(task_copy)
        temp_file = TASKS_FILE + '.tmp'
        try:
            # Load all meta fields from existing file, if present
            meta = {}
            if os.path.exists(TASKS_FILE):
                with open(TASKS_FILE, 'r', encoding='utf-8') as f:
                    try:
                        meta = json.load(f)
                        if isinstance(meta, list): meta = {}
                    except Exception: meta = {}
            # Always preserve all meta fields except tasks
            meta_keys_before = list(meta.keys())
            meta['tasks'] = tasks_to_save
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
            if platform == 'win' and os.path.exists(TASKS_FILE):
                try: os.remove(TASKS_FILE)
                except OSError as e: logging.error(f"Error removing old tasks file: {e}")
            os.replace(temp_file, TASKS_FILE)
            logging.info(f"Saved {len(tasks_to_save)} tasks to {TASKS_FILE}. Meta fields preserved: {meta_keys_before}"); self.tasks_changed = False
        except Exception as e: logging.error(f"Error saving tasks: {e}", exc_info=True); show_error_popup(f"Error saving tasks:\n{e}");
        if os.path.exists(temp_file):
            try: os.remove(temp_file)
            except OSError: pass

    def save_tasks_periodically(self, dt): 
        # Performance optimization: only save if data has actually changed
        if self.tasks_changed:
            self.save_tasks(force=False)
        # Save gratitude entries less frequently to reduce I/O
        if hasattr(self, '_last_gratitude_save'):
            if time.time() - self._last_gratitude_save > 600:  # Save every 10 minutes
                self.save_gratitude_entries()
                self._last_gratitude_save = time.time()
        else:
            self.save_gratitude_entries()
            self._last_gratitude_save = time.time()
        
    # --- Gratitude Journal Methods ---
    def load_gratitude_entries(self):
        """Load gratitude entries from file"""
        gratitude_file = os.path.join('broadcasts', 'gratitude.json')
        try:
            if os.path.exists(gratitude_file):
                with open(gratitude_file, 'r') as file:
                    entries = json.load(file)
                    logging.info(f"Loaded {len(entries)} gratitude entries from {gratitude_file}")
                    return entries
            else:
                logging.info(f"{gratitude_file} not found. Starting with empty gratitude journal.")
                return {}
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding {gratitude_file}: {e}. Starting empty.", exc_info=True)
            show_error_popup(f"Error reading gratitude file:\n{gratitude_file}\nStarting with empty journal.")
            return {}
        except Exception as e:
            logging.error(f"Unexpected error loading gratitude entries: {e}", exc_info=True)
            show_error_popup(f"Failed to load gratitude entries.\nSee console for details.\nStarting empty journal.")
            return {}
    
    def save_gratitude_entries(self):
        """Save gratitude entries to file"""
        gratitude_file = os.path.join('broadcasts', 'gratitude.json')
        try:
            temp_file = gratitude_file + '.tmp'
            with open(temp_file, 'w') as file:
                json.dump(self.gratitude_entries, file, indent=4)
            if platform == 'win' and os.path.exists(gratitude_file):
                try:
                    os.remove(gratitude_file)
                except OSError as e:
                    logging.error(f"Error removing old gratitude file: {e}")
            os.replace(temp_file, gratitude_file)
            logging.info(f"Saved {len(self.gratitude_entries)} gratitude entries to {gratitude_file}.")
        except Exception as e:
            logging.error(f"Error saving gratitude entries: {e}", exc_info=True)
            show_error_popup(f"Error saving gratitude entries:\n{e}")
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass
    
    def add_gratitude_entry(self, text):
        """Add a new gratitude entry for the current day"""
        if not text or not text.strip():
            show_error_popup("Gratitude entry cannot be empty.")
            return False
        
        try:
            # Use YYYY-MM-DD format as the key for each day's entries
            today = datetime.now().strftime('%Y-%m-%d')
            timestamp = datetime.now().isoformat()
            
            # Initialize the day's entries if it doesn't exist
            if today not in self.gratitude_entries:
                self.gratitude_entries[today] = []
            
            # Add the new entry
            entry = {
                'text': text.strip(),
                'timestamp': timestamp
            }
            
            self.gratitude_entries[today].append(entry)
            logging.info(f"Added gratitude entry for {today}")
            
            # Update the calendar to show the new entry
            if hasattr(self, 'calendar_widget'):
                self.calendar_widget.populate_calendar()
                
            return True
        except Exception as e:
            logging.error(f"Error adding gratitude entry: {e}", exc_info=True)
            show_error_popup(f"Failed to add gratitude entry:\n{e}")
            return False
    def mark_tasks_changed(self):
        if not self.tasks_changed: self.tasks_changed = True
    def check_and_resume_timers(self):
        now_unix = time.time(); resumed_count = 0; needs_save = False
        for task in self.tasks:
            if task.get('timer_running') and isinstance(task.get('start_time_unix'), (int, float)):
                elapsed_since_save = now_unix - task['start_time_unix']
                if elapsed_since_save > 0: task['timer'] = task.get('timer', 0) + elapsed_since_save; task['start_time_unix'] = now_unix; resumed_count += 1
                else: task['start_time_unix'] = now_unix; logging.warning(f"Corrected start time for '{task.get('task', 'N/A')}' due to potential clock skew.")
                needs_save = True
            elif task.get('timer_running'): task['timer_running'] = False; task['start_time_unix'] = None; logging.warning(f"Stopped timer for '{task.get('task', 'N/A')}' due to missing start time on load."); needs_save = True
        if resumed_count > 0: logging.info(f"Resumed {resumed_count} timers.")
        if needs_save: self.mark_tasks_changed()
    def find_background_image(self):
        if not os.path.exists(BACKGROUND_FOLDER): logging.warning(f"Background folder not found: {BACKGROUND_FOLDER}"); return None
        try:
            for f in sorted(os.listdir(BACKGROUND_FOLDER)):
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')): path = os.path.join(BACKGROUND_FOLDER, f); logging.info(f"Found suitable background image: {path}"); return path
        except Exception as e: logging.error(f"Error finding background image: {e}")
        logging.warning(f"No suitable background image found in {BACKGROUND_FOLDER}."); return None

    # --- Layout Creation ---
    def create_main_layout(self):
        root_float = FloatLayout(size=Window.size); self.root_layout = root_float
        
        # Create resizable splitter layout
        self.content_layout = self._create_resizable_layout()
        
        root_float.add_widget(self.content_layout)
        Window.bind(on_resize=self._update_layout_size)
        Clock.schedule_once(lambda dt: self._update_layout_size(Window, Window.width, Window.height), 0)
        # Additional delayed update to fix initial distortion
        Clock.schedule_once(lambda dt: self._update_layout_size(Window, Window.width, Window.height), 0.15)
        return root_float
    
    def _create_resizable_layout(self):
        """Create the main resizable layout with splitter handles"""
        # Create the resizable splitter container
        splitter = ResizableSplitter(padding=dp(10), spacing=dp(0))
        
        # Create the three main panels
        left_panel = self._create_left_layout()
        middle_panel = self._create_middle_layout()
        right_panel = self._create_right_layout()
        
        # Add panels to the splitter
        splitter.add_panels(left_panel, middle_panel, right_panel)
        
        return splitter
        
    def _update_layout_size(self, window, width, height):
         size_tuple = (width, height)
         if hasattr(self, 'root_layout') and self.root_layout: self.root_layout.size = size_tuple
         if hasattr(self, 'background_widget') and self.background_widget: self.background_widget.size = size_tuple
         if hasattr(self, 'bg_rect') and self.bg_rect:
              if hasattr(self, 'root_layout'): self.bg_rect.size = self.root_layout.size; self.bg_rect.pos = self.root_layout.pos
         if hasattr(self, 'content_layout'): self.content_layout.size = size_tuple
         # Force calendar widget to update when window size changes
         if hasattr(self, 'calendar_widget') and self.calendar_widget:
             Clock.schedule_once(lambda dt: self.calendar_widget._update_layout(), 0.1)
    def _create_left_layout(self):
        layout = BoxLayout(orientation='vertical', size_hint=(0.3, 1), spacing=dp(5))
        self.groq_input = TextInput(hint_text="Ask Groq...", multiline=False, size_hint=(1, None), height=dp(40))
        self.groq_input.bind(on_text_validate=self.send_to_groq_api)
        layout.add_widget(self.groq_input)
        groq_scroll = ScrollView(size_hint=(1, 1)); self.groq_output = TextInput(hint_text="Groq response...", readonly=True, size_hint=(1, None), halign='left'); self.groq_output.bind(minimum_height=self.groq_output.setter('height')); groq_scroll.add_widget(self.groq_output); layout.add_widget(groq_scroll)
        send_button = Button(text="Send to Groq", size_hint=(1, None), height=dp(40), on_press=self.send_to_groq_api); layout.add_widget(send_button); return layout
    def _create_middle_layout(self):
        layout = BoxLayout(orientation='vertical', size_hint=(0.4, 1), spacing=dp(10))
        task_container = BoxLayout(orientation='vertical', size_hint=(1, 0.65)); scroll_view = ScrollView(size_hint=(1, 1), do_scroll_x=False, bar_width=dp(10)); self.task_list_layout = BoxLayout(orientation='vertical', spacing=dp(5), size_hint_y=None); self.task_list_layout.bind(minimum_height=self.task_list_layout.setter('height')); scroll_view.add_widget(self.task_list_layout); task_container.add_widget(scroll_view); layout.add_widget(task_container)
        # Improved calendar container with better fullscreen support
        calendar_container = BoxLayout(orientation='vertical', size_hint=(1, 0.35)); now = datetime.now()
        try: 
            # Create calendar widget with full size hint to fill container
            self.calendar_widget = CalendarWidget(
                now.year, 
                now.month, 
                tasks_provider=lambda: self.tasks,
                gratitude_provider=lambda: self.gratitude_entries
            )
            calendar_container.add_widget(self.calendar_widget)
            # Set the calendar's colors to the app's current settings
            self.calendar_widget.set_global_text_color(self.calendar_text_color, self.calendar_date_number_color)
        except Exception as cal_err: 
            logging.error(f"Failed to create calendar widget: {cal_err}", exc_info=True)
            calendar_container.add_widget(Label(text="Error loading calendar."))
        layout.add_widget(calendar_container); return layout
    def _create_right_layout(self):
        layout = BoxLayout(orientation='vertical', size_hint=(0.3, 1), spacing=dp(10)); layout.add_widget(self._create_time_display_widgets())
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, bar_width=dp(10)); button_grid = GridLayout(cols=1, spacing=dp(5), size_hint_y=None); button_grid.bind(minimum_height=button_grid.setter('height'))
        buttons_config = [("Add Task", self.add_task_gui, False, True), ("Move Up", self.move_task_up_gui, False, False), ("Move Down", self.move_task_down_gui, False, False), ("Change Title", self.change_task_title_gui, False, False), ("Mark Completed", self.mark_as_completed_gui, False, False), (None, None, True, False), ("Add Subtask", self.add_subtask_gui, False, False), ("Toggle Subtasks", self.toggle_subtasks_gui, False, False), (None, None, True, False), ("Delete Task", self.delete_task_gui, False, False), ("Set Due Date", self.set_due_date_gui, False, False), ("Set Alarm", self.set_alarm_gui, False, False), ("Annotate Task", self.annotate_task_gui_proxy, False, False), (None, None, True, False), ("Add Gratitude", self.add_gratitude_gui, False, True), (None, None, True, False), ("Start Timer", self.start_timer_gui, False, False), ("Stop Timer", self.stop_timer_gui, False, False), ("Reset Timer", self.reset_timer_gui, False, False), (None, None, True, False), ("Export Tasks", self.export_tasks_gui, False, True), ("Import Tasks", self.import_tasks_gui, False, True), ("Sync to Todoist", self.sync_to_todoist_gui, False, True), (None, None, True, False), ("Customize", self.customize_gui, False, True), ("Setup", self.setup_gui, False, True), (None, None, True, False), ("Minimize", self.minimize_app, False, True)]
        self.action_buttons = {}
        for text, callback, is_spacer, enabled in buttons_config:
            if is_spacer: button_grid.add_widget(BoxLayout(size_hint_y=None, height=dp(10)))
            else: button = Button(text=text, on_press=callback, size_hint_y=None, height=dp(35), disabled=not enabled); button_grid.add_widget(button); self.action_buttons[text] = button
        scroll.add_widget(button_grid); layout.add_widget(scroll); return layout
    def _create_time_display_widgets(self):
        time_layout = BoxLayout(orientation='vertical', spacing=dp(5), size_hint_y=None, height=dp(130)); time_layout.add_widget(Label(text='Philippines Time (PHT)', size_hint_y=None, height=dp(20))); self.ph_time_display = TextInput(readonly=True, size_hint_y=None, height=dp(35), halign='center'); self.ph_time_display.bind(on_touch_down=self.on_time_field_right_click); time_layout.add_widget(self.ph_time_display); time_layout.add_widget(Label(text='Houston Time (CST/CDT)', size_hint_y=None, height=dp(20))); self.houston_time_display = TextInput(readonly=True, size_hint_y=None, height=dp(35), halign='center'); self.houston_time_display.bind(on_touch_down=self.on_time_field_right_click); time_layout.add_widget(self.houston_time_display); reset_button = Button(text='Reset Time to System', size_hint_y=None, height=dp(30), on_press=self.reset_time_to_system); time_layout.add_widget(reset_button); return time_layout

    # --- Task Data Handling ---
    def add_task(self, task_name, parent_task=None, parent_index=None):
        if not task_name or not task_name.strip(): show_error_popup("Task name cannot be empty."); return
        try:
            now_iso = datetime.now().isoformat(); new_task = {'task': task_name.strip(), 'timer': 0, 'localTime': datetime.now(PH_TZ).strftime('%Y-%m-%d %H:%M:%S %Z'), 'createdAt': now_iso, 'timer_running': False, 'start_time_unix': None, 'completed': False, 'due_date': None, 'icon': None, 'alarms': [], 'annotations': [], 'titleHistory': [{'title': task_name.strip(), 'timestamp': now_iso}], 'subtasks': []}
            
            if parent_task is not None:
                # Adding as subtask
                if 'subtasks' not in parent_task:
                    parent_task['subtasks'] = []
                parent_task['subtasks'].insert(0, new_task)
                logging.info(f"Added subtask: {task_name} to parent task")
            else:
                # Adding as main task
                self.tasks.insert(0, new_task); new_index = 0; self.select_task(new_index)
                if hasattr(self, 'task_list_layout') and new_index in self.task_widgets:
                    scroll_view = self.task_list_layout.parent
                    if scroll_view: widget_to_scroll = self.task_widgets.get(new_index);
                    if widget_to_scroll: scroll_view.scroll_to(widget_to_scroll, padding=dp(10), animate=True)
                logging.info(f"Added main task: {task_name}")
            
            self.mark_tasks_changed(); self.update_task_view()
        except Exception as e: logging.error(f"Error adding task '{task_name}': {e}", exc_info=True); show_error_popup("Failed to add the task.")
    def delete_task(self, index):
        if not (0 <= index < len(self.tasks)): logging.warning(f"Invalid index {index} for delete_task."); show_error_popup(f"Cannot delete task at invalid index {index}."); return
        task_to_delete = self.tasks[index]
        for alarm in task_to_delete.get('alarms', []):
            alarm_id = alarm.get('id');
            if alarm_id: event = self.scheduled_alarms.pop(alarm_id, None);
            if event: event.cancel(); logging.info(f"Cancelled alarm {alarm_id} for task being deleted.")
        try:
            deleted_task_name = self.tasks[index]['task']; del self.tasks[index]; self.mark_tasks_changed()
            if self.selected_index == index: self.selected_index = None
            elif self.selected_index is not None and self.selected_index > index: self.selected_index -= 1
            self.task_widgets.clear(); self.timer_labels.clear(); self.update_task_view(); self.update_action_buttons_state(); logging.info(f"Deleted task: {deleted_task_name} at index {index}")
        except Exception as e: logging.error(f"Error deleting task at index {index}: {e}", exc_info=True); show_error_popup("Failed to delete the task.")
    def move_task(self, index, direction):
        if not (0 <= index < len(self.tasks)): return None
        new_index = index + direction;
        if not (0 <= new_index < len(self.tasks)): return index
        try:
            task_to_move = self.tasks.pop(index); self.tasks.insert(new_index, task_to_move); self.mark_tasks_changed(); logging.info(f"Moved task '{self.tasks[new_index]['task']}' from {index} to {new_index}.")
            self.selected_index = new_index; self.update_task_view()
            if new_index in self.task_widgets: scroll_view = self.task_list_layout.parent;
            if scroll_view: widget_to_scroll = self.task_widgets.get(new_index);
            if widget_to_scroll: scroll_view.scroll_to(widget_to_scroll, padding=dp(10), animate=True)
            return new_index
        except Exception as e: logging.error(f"Error moving task from {index} to {new_index}: {e}", exc_info=True); show_error_popup("Failed to move the task."); self.update_task_view(); return index

    # --- UI Update Functions ---
    def update_task_view(self):
        Logger.debug("UI: Updating task view...")
        if not hasattr(self, 'task_list_layout'): return
        
        # Performance optimization: batch widget operations
        task_list_layout = self.task_list_layout
        task_list_layout.clear_widgets()
        self.task_widgets.clear()
        self.timer_labels.clear()
        
        currently_selected_index = self.selected_index
        
        # Create all task rows in a batch to reduce layout recalculations
        new_widgets = []
        for index, task in enumerate(self.tasks):
            try:
                task_row = self._create_task_row(index, task)
                task_row.idx = index  # For drag-and-drop
                new_widgets.append((index, task_row))
                self.task_widgets[index] = task_row
                
                # Find the timer label in the created row and add it to the dictionary
                info_layout = next((w for w in task_row.children if isinstance(w, BoxLayout) and hasattr(w, 'is_info_layout')), None)
                if info_layout:
                    timer_label = next((w for w in info_layout.children if isinstance(w, Label) and hasattr(w, 'is_timer_label')), None)
                    if timer_label:
                        self.timer_labels[index] = timer_label
                        
            except Exception as e:
                logging.error(f"Error creating/processing row for task index {index}: {e}\nTask data: {task}", exc_info=True)
                error_label = Label(text=f"Error loading task {index}", color=(1,0,0,1), size_hint_y=None, height=dp(60))
                new_widgets.append((index, error_label))

        # Add all widgets at once to reduce layout recalculations
        for index, widget in new_widgets:
            task_list_layout.add_widget(widget)

        # Restyle the selected row if it exists
        if currently_selected_index is not None and currently_selected_index in self.task_widgets:
            row = self.task_widgets[currently_selected_index]
            button = next((w for w in row.children if isinstance(w, Button)), None)
            if button: 
                self.update_task_row_style(currently_selected_index, row, button)

        # Update calendar and buttons (defer calendar update to reduce blocking)
        Clock.schedule_once(self._deferred_calendar_update, 0.1)
        self.update_action_buttons_state()
        
    def _deferred_calendar_update(self, dt):
        """Update calendar in a deferred manner to improve UI responsiveness"""
        if hasattr(self, 'calendar_widget'):
            try: 
                Logger.debug("UI: Populating calendar...")
                self.calendar_widget.populate_calendar()
            except Exception as cal_err: 
                logging.error(f"Error updating calendar widget: {cal_err}", exc_info=True)

    def _create_task_row(self, index, task):
        # --- Drag-and-drop support ---
        from kivy.uix.behaviors import DragBehavior
        class DraggableBox(DragBehavior, BoxLayout):
            def __init__(self, outer_self, idx, **kwargs):
                super().__init__(**kwargs)
                self.outer_self = outer_self
                self.idx = idx
                self.dragged = False
                self.drag_timeout = 10000
                self.drag_distance = 10
                self.orientation = 'horizontal'
                self.size_hint_y = None
                self.height = dp(70)
                self.spacing = dp(5)
                self.padding = (0, dp(2))
                # Update drag rectangle when size changes
                self.bind(size=self.update_drag_rectangle, pos=self.update_drag_rectangle)
                self.update_drag_rectangle()
                
            def update_drag_rectangle(self, *args):
                self.drag_rectangle = [self.x, self.y, self.width, self.height]
                
            def on_touch_down(self, touch):
                if self.collide_point(*touch.pos):
                    self.dragged = False
                    return super().on_touch_down(touch)
                return False
                
            def on_touch_move(self, touch):
                if self.collide_point(*touch.pos):
                    self.dragged = True
                    # Add visual feedback during drag
                    self._show_drop_indicator(touch.pos)
                    return super().on_touch_move(touch)
                return False
                
            def _show_drop_indicator(self, touch_pos):
                """Show visual indicator of where the task will be dropped"""
                if not self.parent:
                    return
                    
                # Clear any existing drop indicators
                self._clear_drop_indicators()
                
                # Find the drop position
                drop_position = self._find_drop_position(touch_pos)
                if drop_position is not None:
                    # Add visual indicator (could be a colored line or highlight)
                    # For now, we'll just change the opacity of the dragged item
                    self.opacity = 0.7
                    
            def _clear_drop_indicators(self):
                """Clear all drop indicators"""
                self.opacity = 1.0
                
            def on_touch_up(self, touch):
                if self.dragged and hasattr(self, 'parent') and self.parent:
                    # Find the correct insertion position based on drop location
                    drop_position = self._find_drop_position(touch.pos)
                    if drop_position is not None and drop_position != self.idx:
                        self.outer_self._insert_task_at_position(self.idx, drop_position)
                        logging.info(f"Moved task from index {self.idx} to position {drop_position}")
                
                self.dragged = False
                return super().on_touch_up(touch)
                
            def _find_drop_position(self, touch_pos):
                """Find the correct insertion position based on touch position"""
                if not self.parent:
                    return None
                    
                # Get all task rows sorted by their y position (top to bottom)
                task_rows = []
                for child in self.parent.children:
                    if hasattr(child, 'idx') and child != self:
                        task_rows.append((child.idx, child.y, child.height))
                
                # Sort by y position (higher y = higher on screen in Kivy)
                task_rows.sort(key=lambda x: x[1], reverse=True)
                
                touch_y = touch_pos[1]
                
                # Find where to insert based on touch position
                for i, (idx, y, height) in enumerate(task_rows):
                    row_center_y = y + height / 2
                    
                    # If touch is above the center of this row, insert before it
                    if touch_y > row_center_y:
                        return idx
                
                # If we didn't find a position above any row, insert at the end
                if task_rows:
                    return len(self.outer_self.tasks)
                
                return None
        task_row = DraggableBox(self, index)

        # --- Move Up/Down Buttons (left side of row) ---
        arrow_box = BoxLayout(orientation='vertical', size_hint_x=None, width=dp(14), spacing=dp(0), padding=(dp(2), dp(2), dp(2), dp(2)))
        from kivy.uix.image import Image
        btn_height = dp(11)
        btn_width = dp(11)
        up_btn = Button(size_hint_y=0.45, size_hint_x=1, height=btn_height, width=btn_width, background_normal='', background_color=(1,1,1,0.01), padding=(0,-dp(7),0,0))
        down_btn = Button(size_hint_y=0.45, size_hint_x=1, height=btn_height, width=btn_width, background_normal='', background_color=(1,1,1,0.01), padding=(0,-dp(3),0,0))
        # Always show the arrows, but only disable if at top or bottom
        up_btn.disabled = (index == 0)
        down_btn.disabled = (index == len(self.tasks)-1)
        up_img_path = os.path.join('graphics', 'assetts', 'red-arrow-up.png')
        down_img_path = os.path.join('graphics', 'assetts', 'green-arrow-down.png')
        up_img = Image(source=up_img_path, allow_stretch=True, keep_ratio=True, size_hint=(1,1), size=(btn_width, btn_height))
        down_img = Image(source=down_img_path, allow_stretch=True, keep_ratio=True, size_hint=(1,1), size=(btn_width, btn_height))
        up_btn.clear_widgets()
        down_btn.clear_widgets()
        up_btn.add_widget(up_img)
        down_btn.add_widget(down_img)
        def move_up(inst):
            self.move_task(index, -1)
        def move_down(inst):
            self.move_task(index, 1)
        up_btn.bind(on_press=move_up)
        down_btn.bind(on_press=move_down)
        arrow_box.add_widget(up_btn)
        arrow_box.add_widget(down_btn)
        task_row.add_widget(arrow_box)

        timer_str = format_timedelta(task.get('timer', 0)); local_time_str = task.get('localTime', 'N/A')
        try: created_dt = datetime.strptime(local_time_str.split(' ')[0] + ' ' + local_time_str.split(' ')[1], '%Y-%m-%d %H:%M:%S'); formatted_created_time = created_dt.strftime('%Y-%m-%d %H:%M')
        except: formatted_created_time = local_time_str

        # ... (rest of your code for creating task row)

        # Timer label (single, fully clickable, visually unified)
        timer_label = Label(text=f"Timer: {timer_str}", size_hint_x=1, halign='left', valign='middle', font_size=dp(12), color=(0, 0, 0, 1))
        timer_label.is_timer_label = True
        timer_label.index = index
        def timer_label_touch(instance, touch, idx=index):
            if instance.collide_point(*touch.pos):
                return self._on_timer_label_touch(instance, touch, idx)
            return False
        timer_label.bind(on_touch_down=timer_label_touch)
        timer_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
        if not hasattr(self, 'timer_labels'):
            self.timer_labels = {}
        self.timer_labels[index] = timer_label

        # Stop timer label (make it clickable)
        stop_timer_str = format_timedelta(task.get('timer', 0))
        stop_timer_label = Label(text=f"Stopped: {stop_timer_str}", size_hint_x=0.32, halign='left', valign='middle')
        stop_timer_label.is_stop_timer_label = True
        stop_timer_label.index = index
        stop_timer_label.bind(on_touch_down=lambda instance, touch, idx=index: self._on_stop_timer_label_touch(instance, touch, idx))
        if not hasattr(self, 'stop_timer_labels'):
            self.stop_timer_labels = {}
        self.stop_timer_labels[index] = stop_timer_label

        # ... (add timer_label and stop_timer_label to info_layout as before)

        # Continue with the rest of your row creation logic
        title = task.get('task', 'Untitled Task'); is_completed = task.get('completed', False); title_display = f"[s]{title}[/s]" if is_completed else title
        
        # Add subtask completion stats to display
        completed_subtasks, total_subtasks = self.get_subtask_completion_stats(task)
        
        # Show subtask info differently based on visibility
        subtasks_visible = task.get('subtasks_visible', True)
        if total_subtasks > 0:
            if subtasks_visible:
                # When subtasks are visible, show completion stats
                subtask_info = f" ({completed_subtasks}/{total_subtasks})"
            else:
                # When subtasks are hidden, show count with indicator
                subtask_info = f" [+{total_subtasks} subtasks]"
                logging.info(f"Task '{title}' has hidden subtasks, showing: {subtask_info}")
        else:
            subtask_info = ""
        
        # Create main task container to hold both task button and subtasks
        task_container = BoxLayout(orientation='vertical', size_hint_x=0.75, spacing=dp(2))
        
        display_text = f"[size={int(dp(16))}]{title_display}{subtask_info}[/size]\n[size={int(dp(11))}]Created: {formatted_created_time}[/size]"
        task_button = Button(size_hint_y=None, height=dp(60), markup=True, halign='left', valign='top', text=display_text, padding=(dp(10), dp(8)))
        task_button.bind(size=lambda *args: setattr(task_button, 'text_size', (task_button.width - task_button.padding[0]*2, None)))
        # Add right-click functionality to toggle subtask visibility
        def on_task_button_touch(instance, touch, task_index=index):
            if instance.collide_point(*touch.pos):
                if touch.button == 'left':
                    self.select_task(task_index)
                    return True
                elif touch.button == 'right' and len(self.tasks[task_index].get('subtasks', [])) > 0:
                    self.toggle_subtask_visibility(task_index)
                    return True
            return False
        task_button.bind(on_touch_down=on_task_button_touch)
        task_container.add_widget(task_button)
        
        # Show subtasks container if there are subtasks and they're visible
        if total_subtasks > 0 and task.get('subtasks_visible', True):
            subtasks_container = self._create_subtasks_container(index, task)
            task_container.add_widget(subtasks_container)
        
        task_row.add_widget(task_container)
        info_layout = BoxLayout(orientation='vertical', size_hint_x=0.25, spacing=dp(2), padding=(0, dp(5), dp(5), dp(5)))
        info_layout.is_info_layout = True
        # Only add the unified timer_label (already created above) to info_layout
        info_layout.add_widget(timer_label)
        due_label_height = dp(18)
        if task.get('due_date'): due_label = Label(text=f"Due: {task['due_date']}", size_hint_y=None, height=due_label_height, halign='left', valign='top', font_size=dp(10), color=(0.8, 0, 0, 1)); due_label.bind(size=lambda *args: setattr(due_label, 'text_size', (due_label.width, None))); info_layout.add_widget(due_label)
        else: info_layout.add_widget(BoxLayout(size_hint_y=None, height=due_label_height))
        icon_height = dp(20)
        if task.get('icon') and os.path.exists(task['icon']):
            try:
                # Use ColorCyclingIcon for task list, syncing color with calendar
                icon_widget = ColorCyclingIcon(
                    task_ref=task,
                    app_ref=self,
                    icon_key='calendar_icon_color',
                    source=task['icon'],
                    size_hint=(None, None),
                    size=(icon_height, icon_height),
                    pos_hint={'x': 0},
                    allow_stretch=True
                )
                info_layout.add_widget(icon_widget)
            except Exception as img_err:
                logging.warning(f"Failed to load icon image {task['icon']} for task row: {img_err}")
                info_layout.add_widget(BoxLayout(size_hint_y=None, height=icon_height))
        else:
            info_layout.add_widget(BoxLayout(size_hint_y=None, height=icon_height))
        # Add Todoist checkbox (small red outlined checkbox at top-right)
        checkbox_size = dp(16)
        is_todone = task.get('todone', False)
        
        # Create checkbox container positioned at top-right
        checkbox_container = FloatLayout(
            size_hint=(None, None), 
            size=(checkbox_size + dp(4), checkbox_size + dp(4)),
            pos_hint={'top': 1, 'right': 1}
        )
        
        todone_checkbox = Button(
            size_hint=(None, None),
            size=(checkbox_size, checkbox_size),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            background_normal='',
            background_color=(1, 1, 1, 0.9),  # White background
        )
        
        # Draw red border
        with todone_checkbox.canvas.before:
            Color(1, 0, 0, 1)  # Red color for border
            todone_checkbox.border_line = Line(width=1.5)
        
        # Add checkmark if task is flagged for todoist
        if is_todone:
            with todone_checkbox.canvas:
                Color(1, 0, 0, 1)  # Red checkmark
                todone_checkbox.checkmark = Line(width=2)
        
        # Update graphics when position/size changes
        def update_checkbox_graphics(instance, value):
            if hasattr(instance, 'border_line'):
                x, y, w, h = instance.x, instance.y, instance.width, instance.height
                instance.border_line.rectangle = (x, y, w, h)
            if hasattr(instance, 'checkmark'):
                x, y, w, h = instance.x, instance.y, instance.width, instance.height
                # Draw checkmark
                instance.checkmark.points = [
                    x + w * 0.2, y + h * 0.5,
                    x + w * 0.4, y + h * 0.3,
                    x + w * 0.8, y + h * 0.7
                ]
        
        todone_checkbox.bind(pos=update_checkbox_graphics, size=update_checkbox_graphics)
        
        # Handle checkbox click
        def toggle_todone(instance, task_index=index):
            current_state = self.tasks[task_index].get('todone', False)
            self.tasks[task_index]['todone'] = not current_state
            self.mark_tasks_changed()
            self.save_tasks(force=True)
            self.update_task_view()  # Refresh to show/hide checkmark
            
        todone_checkbox.bind(on_press=toggle_todone)
        checkbox_container.add_widget(todone_checkbox)
        
        # Position the checkbox container at the top-right of the task row
        task_row.add_widget(checkbox_container)
        
        task_row.add_widget(info_layout);
        # Apply initial style (might not color the timer label correctly yet)
        self.update_task_row_style(index, task_row, task_button);
        return task_row # Return the row so update_task_view can add it and populate self.timer_labels

    def update_task_row_style(self, index, task_row, task_button):
         if not (0 <= index < len(self.tasks)): return
         task = self.tasks[index]; is_selected = (self.selected_index == index); is_completed = task.get('completed', False)
         # Determine theme colors (dark/light mode)
         if self.is_dark_mode:
             base_color = (0.25, 0.25, 0.25, 1); selected_color = (0.2, 0.35, 0.55, 1); completed_color = (0.1, 0.45, 0.1, 1);
             text_color = (0.9, 0.9, 0.9, 1); completed_text_color = (0.6, 0.9, 0.6, 1)
         else:
             base_color = (1, 1, 1, 1); selected_color = (0.7, 0.85, 1, 1); completed_color = (0.8, 1, 0.8, 1);
             text_color = (0.1, 0.1, 0.1, 1); completed_text_color = (0.3, 0.5, 0.3, 1)

         # Style the main task button background and text
         task_button.background_normal = ''; title = task.get('task', 'Untitled Task'); local_time_str = task.get('localTime', 'N/A')
         try: created_dt = datetime.strptime(local_time_str.split(' ')[0] + ' ' + local_time_str.split(' ')[1], '%Y-%m-%d %H:%M:%S'); formatted_created_time = created_dt.strftime('%Y-%m-%d %H:%M')
         except: formatted_created_time = local_time_str

         if is_completed:
             task_button.background_color = completed_color; task_button.color = completed_text_color;
             display_text = f"[size={int(dp(16))}][s]{title}[/s][/size]\n[size={int(dp(11))}]Created: {formatted_created_time}[/size]"
         elif is_selected:
             task_button.background_color = selected_color; task_button.color = text_color;
             display_text = f"[size={int(dp(16))}]{title}[/size]\n[size={int(dp(11))}]Created: {formatted_created_time}[/size]"
         else:
             task_button.background_color = base_color; task_button.color = text_color;
             display_text = f"[size={int(dp(16))}]{title}[/size]\n[size={int(dp(11))}]Created: {formatted_created_time}[/size]"
         task_button.text = display_text

         # Find the timer label directly within the passed task_row's children
         timer_label_widget = None
         # Find the info_layout first (assuming structure from _create_task_row)
         info_layout = next((w for w in task_row.children if isinstance(w, BoxLayout) and hasattr(w, 'is_info_layout')), None)
         if info_layout:
             # Find the label with the marker inside info_layout
             timer_label_widget = next((w for w in info_layout.children if isinstance(w, Label) and hasattr(w, 'is_timer_label')), None)

         # Now, apply the text color if the widget was found
         if timer_label_widget:
             # Use per-task timer color if set, else global, else fallback
             color = self.timer_colors.get(str(index), None)
             if color is None:
                 color = getattr(self, 'timer_label_color', None)
             if color is None:
                 color = text_color
             timer_label_widget.color = color

         # Apply stop timer label color if present
         stop_timer_label_widget = next((w for w in info_layout.children if isinstance(w, Label) and hasattr(w, 'is_stop_timer_label')), None)
         if stop_timer_label_widget:
             color = self.stop_timer_colors.get(str(index), None)
             if color is None:
                 color = getattr(self, 'timer_label_color', None)
             if color is None:
                 color = text_color
             stop_timer_label_widget.color = color

    def select_task(self, index):
        if not (0 <= index < len(self.tasks)): return
        current_time = time.time(); is_double_click = (self.last_click_index == index and self.last_click_time is not None and current_time - self.last_click_time < 0.5)
        previous_index = self.selected_index; self.selected_index = index
        # Deselect previous row
        if previous_index is not None and previous_index != index and previous_index in self.task_widgets:
             prev_row = self.task_widgets.get(previous_index);
             if prev_row: prev_button = next((w for w in prev_row.children if isinstance(w, Button)), None);
             if prev_button: self.update_task_row_style(previous_index, prev_row, prev_button) # Update style to deselected
        # Select current row
        if index in self.task_widgets:
             current_row = self.task_widgets.get(index);
             if current_row: current_button = next((w for w in current_row.children if isinstance(w, Button)), None);
             if current_button: self.update_task_row_style(index, current_row, current_button) # Update style to selected

        self.last_click_index = index; self.last_click_time = current_time; self.update_action_buttons_state()
        if is_double_click: logging.info(f"Double-click detected on task {index}."); self.annotate_task_gui(index)

    def update_action_buttons_state(self):
        has_selection = self.selected_index is not None and 0 <= self.selected_index < len(self.tasks); can_move_up = has_selection and self.selected_index > 0; can_move_down = has_selection and self.selected_index < len(self.tasks) - 1
        button_states = {"Move Up": False, "Move Down": False, "Change Title": False, "Mark Completed": False, "Delete Task": False, "Set Due Date": False, "Set Alarm": False, "Annotate Task": False, "Add Subtask": False, "Toggle Subtasks": False, "Start Timer": False, "Stop Timer": False, "Reset Timer": False,}
        mark_complete_text = "Mark Completed"
        if has_selection:
            task = self.tasks[self.selected_index]; is_running = task.get('timer_running', False); has_time = task.get('timer', 0) > 0; is_completed = task.get('completed', False)
            has_subtasks = len(task.get('subtasks', [])) > 0
            button_states.update({"Move Up": can_move_up, "Move Down": can_move_down, "Change Title": True, "Mark Completed": True, "Delete Task": True, "Set Due Date": True, "Set Alarm": True, "Annotate Task": True, "Add Subtask": True, "Toggle Subtasks": has_subtasks, "Start Timer": not is_running and not is_completed, "Stop Timer": is_running, "Reset Timer": (has_time or is_running) and not is_completed,})
            mark_complete_text = "Undo Mark Completed" if is_completed else "Mark Completed"
        for key, button in self.action_buttons.items():
            if key in button_states: button.disabled = not button_states[key];
            if key == "Mark Completed": button.text = mark_complete_text

    # --- Timer Logic ---
    def start_timer(self, index):
        if not (0 <= index < len(self.tasks)): return
        task = self.tasks[index];
        if task.get('timer_running') or task.get('completed', False): return
        try: task['timer_running'] = True; task['start_time_unix'] = time.time(); self.mark_tasks_changed(); self.update_action_buttons_state(); logging.info(f"Started timer for task {index}: {task['task']}")
        except Exception as e: logging.error(f"Error starting timer for task {index}: {e}", exc_info=True)
    def stop_timer(self, index):
        if not (0 <= index < len(self.tasks)): return
        task = self.tasks[index];
        if not task.get('timer_running'): return
        try:
            final_time = task.get('timer', 0); start_time = task.get('start_time_unix')
            if isinstance(start_time, (int, float)): elapsed = time.time() - start_time;
            if elapsed > 0: final_time += elapsed
            task['timer'] = final_time; task['timer_running'] = False; task['start_time_unix'] = None; self.mark_tasks_changed(); self.update_timer_label(index, final_time); self.update_action_buttons_state(); logging.info(f"Stopped timer for task {index}: {task['task']}. Total: {format_timedelta(task['timer'])}")
        except Exception as e: logging.error(f"Error stopping timer for task {index}: {e}", exc_info=True)
    def reset_timer(self, index):
        if not (0 <= index < len(self.tasks)): return
        task = self.tasks[index];
        if task.get('completed', False): return
        try:
            was_running = task.get('timer_running', False); task['timer'] = 0; task['timer_running'] = False; task['start_time_unix'] = None; self.mark_tasks_changed(); self.update_timer_label(index, 0); self.update_action_buttons_state(); logging.info(f"Reset timer for task {index}: {task['task']}")
            if was_running: logging.info(f"Timer for task {index} was stopped during reset.")
        except Exception as e: logging.error(f"Error resetting timer for task {index}: {e}", exc_info=True)
    def update_timers_and_display(self, dt):
        # Performance optimization: only update if enough time has passed
        now_unix = time.time()
        if now_unix - self._last_timer_update < 0.1:  # Throttle updates to max 10 FPS
            return
        self._last_timer_update = now_unix
        
        active_timer_running = False
        # Only update running timers to reduce CPU usage
        for index, task in enumerate(self.tasks):
            if task.get('timer_running') and isinstance(task.get('start_time_unix'), (int, float)):
                current_total_time = task.get('timer', 0) + (now_unix - task['start_time_unix'])
                self.update_timer_label(index, current_total_time)
                active_timer_running = True
        
        # Only update window title when necessary
        if active_timer_running or self.minimized:
            self.update_window_title_display()
        elif not self.minimized and Window.title != "Productivity App":
            Window.set_title("Productivity App")
    def update_timer_label(self, index, current_total_time=None):
        if index in self.timer_labels:
            label_widget = self.timer_labels.get(index)
            if label_widget:
                if current_total_time is None:
                    if 0 <= index < len(self.tasks):
                        task = self.tasks[index]
                        if task.get('timer_running') and isinstance(task.get('start_time_unix'), (int, float)):
                            current_total_time = task.get('timer', 0) + (time.time() - task['start_time_unix'])
                        else:
                            current_total_time = task.get('timer', 0)
                    else:
                        current_total_time = 0
                
                # Performance optimization: only update text if it has changed
                new_text = f"Timer: {format_timedelta(current_total_time)}"
                if label_widget.text != new_text:
                    label_widget.text = new_text

    # --- Time Display Logic ---
    def update_live_time_displays(self, dt):
        try:
            if self._manual_time_mode:
                now_naive = datetime.now(); manual_dt = now_naive + self._manual_time_offset; ph_display = manual_dt.strftime('%A, %Y-%m-%d %I:%M:%S %p') + " (Manual)"
                utc_now = datetime.now(timezone.utc); ph_real = utc_now.astimezone(PH_TZ); hou_real = utc_now.astimezone(HOUSTON_TZ)
                try:
                    current_offset_delta = ph_real.utcoffset() - hou_real.utcoffset()
                except (TypeError, AttributeError):
                    current_offset_delta = timedelta(hours=13)
                    logging.warning(f"Timezone offset calculation failed (PH: {ph_real}, Houston: {hou_real}), using fallback. Please check timezone data.")
                houston_manual_dt = manual_dt - current_offset_delta; houston_display = houston_manual_dt.strftime('%A, %Y-%m-%d %I:%M:%S %p') + " (Manual)"
            else:
                utc_now = datetime.now(timezone.utc)
                ph_time = utc_now.astimezone(PH_TZ)
                houston_time = utc_now.astimezone(HOUSTON_TZ)
                ph_display = ph_time.strftime('%A, %Y-%m-%d %I:%M:%S %p %Z')
                houston_display = houston_time.strftime('%A, %Y-%m-%d %I:%M:%S %p %Z')
            if hasattr(self, 'ph_time_display'): self.ph_time_display.text = ph_display
            if hasattr(self, 'houston_time_display'): self.houston_time_display.text = houston_display
        except Exception as e:
            logging.error(f"Error updating live time displays: {e}", exc_info=True)
            if hasattr(self, 'ph_time_display'): self.ph_time_display.text = "Error PHT"
            if hasattr(self, 'houston_time_display'): self.houston_time_display.text = "Error HOU"
    def on_time_field_right_click(self, instance, touch):
        if touch.button == 'right' and instance.collide_point(*touch.pos): logging.info("Right-click detected on time field."); is_ph_field = (instance == self.ph_time_display); self.show_manual_time_entry_popup(is_ph_field); return True
        return False
    def show_manual_time_entry_popup(self, for_philippines_time):
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10)); time_input_layout = BoxLayout(orientation='horizontal', spacing=dp(5), size_hint_y=None, height=dp(40)); hour_input = TextInput(hint_text='HH', input_filter='int', multiline=False, size_hint_x=0.3); minute_input = TextInput(hint_text='MM', input_filter='int', multiline=False, size_hint_x=0.3); second_input = TextInput(hint_text='SS', input_filter='int', multiline=False, size_hint_x=0.3); time_input_layout.add_widget(hour_input); time_input_layout.add_widget(minute_input); time_input_layout.add_widget(second_input); ampm_spinner = Spinner(text='AM', values=('AM', 'PM'), size_hint=(None, None), size=(dp(80), dp(40))); content.add_widget(Label(text="Enter desired time (for today):")); content.add_widget(time_input_layout); content.add_widget(ampm_spinner); button_layout = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10)); save_button = Button(text='Set Manual Time'); cancel_button = Button(text='Cancel'); button_layout.add_widget(save_button); button_layout.add_widget(cancel_button); content.add_widget(button_layout); popup_title = f"Set {'Philippines' if for_philippines_time else 'Houston'} Time Manually"; content.bind(minimum_height=content.setter('height')); popup = Popup(title=popup_title, content=content, size_hint=(None, None), size=(dp(350), dp(280)), auto_dismiss=False)
        def on_save(instance):
            try:
                hour_str, minute_str, second_str = hour_input.text.strip(), minute_input.text.strip(), second_input.text.strip(); hour = int(hour_str) if hour_str.isdigit() else -1; minute = int(minute_str) if minute_str.isdigit() else -1; second = int(second_str) if second_str.isdigit() else -1; ampm = ampm_spinner.text
                if not (1 <= hour <= 12 and 0 <= minute <= 59 and 0 <= second <= 59): raise ValueError("Invalid time values.")
                hour_24 = hour;
                if ampm == 'PM' and hour != 12: hour_24 += 12
                elif ampm == 'AM' and hour == 12: hour_24 = 0
                now_naive = datetime.now().replace(microsecond=0); target_naive_dt = now_naive.replace(hour=hour_24, minute=minute, second=second); self._manual_time_offset = target_naive_dt - now_naive; self._manual_time_mode = True; logging.info(f"Manual time mode enabled. Offset calculated: {self._manual_time_offset}"); self.update_live_time_displays(None); popup.dismiss()
            except ValueError as ve: show_error_popup(f"Invalid time entered.\nPlease use HH(1-12), MM(0-59), SS(0-59).")
            except Exception as e: logging.error(f"Error setting manual time: {e}", exc_info=True); show_error_popup(f"An unexpected error occurred setting the time: {e}")
        save_button.bind(on_press=on_save); cancel_button.bind(on_press=popup.dismiss); popup.open()
    def reset_time_to_system(self, instance):
        self._manual_time_mode = False; self._manual_time_offset = timedelta(0); logging.info("Time reset to system time."); self.update_live_time_displays(None)

    # --- Other Actions & GUI Handlers ---
    def add_task_gui(self, instance):
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10)); task_input = TextInput(hint_text='Enter new task name', multiline=False, size_hint_y=None, height=dp(40)); content.add_widget(task_input); button_layout = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10)); save_button = Button(text='Save'); cancel_button = Button(text='Cancel'); button_layout.add_widget(save_button); button_layout.add_widget(cancel_button); content.add_widget(button_layout); content.bind(minimum_height=content.setter('height')); popup_height = max(dp(180), content.minimum_height + dp(70)); popup = Popup(title='Add New Task', content=content, size_hint=(0.7, None), height=popup_height, auto_dismiss=False)
        def save_action(instance):
            task_name = task_input.text.strip();
            if task_name: self.add_task(task_name); popup.dismiss()
            else: task_input.hint_text = "Task name cannot be empty!"; task_input.background_color = (1, 0.8, 0.8, 1)
        save_button.bind(on_press=save_action); cancel_button.bind(on_press=popup.dismiss); popup.open(); task_input.focus = True
    def delete_task_gui(self, instance):
        if self.selected_index is None: show_error_popup("Select a task first."); return
        if not (0 <= self.selected_index < len(self.tasks)): return
        task_name = self.tasks[self.selected_index].get('task', 'this task'); content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10)); label = Label(text=f"Are you sure you want to delete:\n'{task_name}'?"); label.bind(size=lambda *x: setattr(label, 'text_size', (content.width*0.95, None))); content.add_widget(label); button_layout = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10)); yes_button = Button(text='Yes, Delete'); no_button = Button(text='No, Cancel'); button_layout.add_widget(yes_button); button_layout.add_widget(no_button); content.add_widget(button_layout); content.bind(minimum_height=content.setter('height')); popup_height = max(dp(180), content.minimum_height + dp(70)); popup = Popup(title='Confirm Deletion', content=content, size_hint=(0.6, None), height=popup_height, auto_dismiss=False)
        def confirm_delete(instance): popup.dismiss(); self.delete_task(self.selected_index)
        yes_button.bind(on_press=confirm_delete); no_button.bind(on_press=popup.dismiss); popup.open()
    def move_task_up_gui(self, instance):
        if self.selected_index is not None: self.move_task(self.selected_index, -1)
    def move_task_down_gui(self, instance):
         if self.selected_index is not None: self.move_task(self.selected_index, 1)
    def start_timer_gui(self, instance):
        if self.selected_index is not None: self.start_timer(self.selected_index)
    def stop_timer_gui(self, instance):
        if self.selected_index is not None: self.stop_timer(self.selected_index)
    def reset_timer_gui(self, instance):
        if self.selected_index is not None: self.reset_timer(self.selected_index)
    def export_tasks_gui(self, instance):
        from kivy.uix.filechooser import FileChooserIconView
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        filechooser = FileChooserIconView(path=os.getcwd(), filters=['*.json'], size_hint_y=0.8)
        filename_input = TextInput(text='tasks_export.json', size_hint_y=None, height=dp(40))
        content.add_widget(filechooser)
        content.add_widget(Label(text='Filename:', size_hint_y=None, height=dp(20)))
        content.add_widget(filename_input)
        button_layout = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        save_button = Button(text='Export')
        cancel_button = Button(text='Cancel')
        button_layout.add_widget(save_button)
        button_layout.add_widget(cancel_button)
        content.add_widget(button_layout)
        popup = Popup(title='Export Tasks', content=content, size_hint=(0.8, 0.7), auto_dismiss=False)

        def do_export(instance):
            export_path = filechooser.path
            export_name = filename_input.text.strip() or 'tasks_export.json'
            full_path = os.path.join(export_path, export_name)
            try:
                with open(full_path, 'w', encoding='utf-8') as f:
                    import json
                    json.dump(self.tasks, f, ensure_ascii=False, indent=2)
                popup.dismiss()
                show_confirmation_popup(f'Tasks exported to:\n{full_path}')
            except Exception as e:
                show_error_popup(f'Failed to export tasks:\n{e}')
        save_button.bind(on_press=do_export)
        cancel_button.bind(on_press=popup.dismiss)
        popup.open()

    def import_tasks_gui(self, instance):
        from kivy.uix.filechooser import FileChooserIconView
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        filechooser = FileChooserIconView(path=os.getcwd(), filters=['*.json'], size_hint_y=0.8)
        content.add_widget(filechooser)
        button_layout = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        import_button = Button(text='Import')
        cancel_button = Button(text='Cancel')
        button_layout.add_widget(import_button)
        button_layout.add_widget(cancel_button)
        content.add_widget(button_layout)
        popup = Popup(title='Import Tasks', content=content, size_hint=(0.8, 0.7), auto_dismiss=False)

        def do_import(instance):
            if not filechooser.selection:
                show_error_popup('Please select a JSON file to import.')
                return
            import_path = filechooser.selection[0]
            try:
                with open(import_path, 'r', encoding='utf-8') as f:
                    import json
                    imported_data = json.load(f)
                # Accept either a list of tasks or a dict with 'tasks' key
                if isinstance(imported_data, list):
                    self.tasks = imported_data
                elif isinstance(imported_data, dict) and isinstance(imported_data.get('tasks'), list):
                    self.tasks = imported_data['tasks']
                else:
                    raise ValueError('Imported file must contain a JSON array of tasks or an object with a "tasks" array.')
                self.mark_tasks_changed()
                self.update_task_view()
                popup.dismiss()
                show_confirmation_popup(f'Tasks imported from:\n{import_path}')
            except Exception as e:
                show_error_popup(f'Failed to import tasks:\n{e}')
        import_button.bind(on_press=do_import)
        cancel_button.bind(on_press=popup.dismiss)
        popup.open()

    def sync_to_todoist_gui(self, instance):
        """Sync tasks.json to Todoist using import_todoist.py"""
        import os, sys, subprocess
        from kivy.clock import Clock
        
        # Validate file structure first
        base_dir = os.getcwd()
        script_path = os.path.join(base_dir, "Calendar Converter", "import_todoist.py")
        input_json = os.path.join(base_dir, TASKS_FILE)
        csv_path = os.path.join(base_dir, "Calendar Converter", "todoist_import.csv")
        
        # Check if required files/directories exist
        if not os.path.exists(os.path.join(base_dir, "Calendar Converter")):
            show_error_popup("Error: 'Calendar Converter' folder not found in project root.")
            return
            
        if not os.path.exists(script_path):
            show_error_popup(f"Error: import_todoist.py script not found at:\n{script_path}")
            return
            
        if not os.path.exists(input_json):
            show_error_popup(f"Error: tasks.json file not found at:\n{input_json}")
            return
        
        # Check API token
        token = os.getenv("TODOIST_API_TOKEN")
        if not token:
            show_error_popup("Please set TODOIST_API_TOKEN in your .env file.\n\nGet your token from:\nhttps://todoist.com/prefs/integrations")
            return
        
        # Ensure Calendar Converter directory has write permissions
        try:
            test_file = os.path.join(base_dir, "Calendar Converter", "test_write.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
        except Exception as e:
            show_error_popup(f"Error: No write permission in Calendar Converter directory:\n{e}")
            return
        
        def run_sync(dt):
            try:
                # Run the sync script
                proc = subprocess.run([sys.executable, script_path, input_json, "--csv", csv_path, "--token", token], 
                                    capture_output=True, text=True, timeout=30)
                
                if proc.returncode == 0:
                    # Count tasks that were synced
                    tasks_data = self.load_tasks()
                    todoist_tasks = [t for t in tasks_data if t.get('todone', False) and not t.get('completed', False)]
                    
                    show_confirmation_popup(f"Successfully synced {len(todoist_tasks)} tasks to Todoist!\n\nCSV file created: {csv_path}")
                else:
                    error_msg = proc.stderr.strip() if proc.stderr.strip() else proc.stdout.strip()
                    if not error_msg:
                        error_msg = f"Sync failed with return code {proc.returncode}"
                    show_error_popup(f"Sync failed:\n{error_msg}")
                    
            except subprocess.TimeoutExpired:
                show_error_popup("Sync timed out. Please check your internet connection and try again.")
            except FileNotFoundError:
                show_error_popup(f"Python interpreter not found. Please ensure Python is installed and accessible.")
            except Exception as e:
                show_error_popup(f"Exception during sync:\n{str(e)}")
                
        Clock.schedule_once(run_sync, 0)

        from kivy.uix.filechooser import FileChooserIconView
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        filechooser = FileChooserIconView(path=os.getcwd(), filters=['*.json'], size_hint_y=0.8)
        content.add_widget(filechooser)
        button_layout = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        import_button = Button(text='Import')
        cancel_button = Button(text='Cancel')
        button_layout.add_widget(import_button)
        button_layout.add_widget(cancel_button)
        content.add_widget(button_layout)
        popup = Popup(title='Import Tasks', content=content, size_hint=(0.8, 0.7), auto_dismiss=False)

        def do_import(instance):
            if not filechooser.selection:
                show_error_popup('Please select a JSON file to import.')
                return
            import_path = filechooser.selection[0]
            try:
                with open(import_path, 'r', encoding='utf-8') as f:
                    import json
                    imported_data = json.load(f)
                # Accept either a list of tasks or a dict with 'tasks' key
                if isinstance(imported_data, list):
                    self.tasks = imported_data
                elif isinstance(imported_data, dict) and isinstance(imported_data.get('tasks'), list):
                    self.tasks = imported_data['tasks']
                else:
                    raise ValueError('Imported file must contain a JSON array of tasks or an object with a "tasks" array.')
                self.mark_tasks_changed()
                self.update_task_view()
                popup.dismiss()
                show_confirmation_popup(f'Tasks imported from:\n{import_path}')
            except Exception as e:
                show_error_popup(f'Failed to import tasks:\n{e}')
        import_button.bind(on_press=do_import)
        cancel_button.bind(on_press=popup.dismiss)
        popup.open()

    
    # --- Gratitude Journal GUI ---
    def add_gratitude_gui(self, instance):
        """Shows a popup for adding a gratitude journal entry"""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        # Title and instructions
        title_label = Label(
            text="What are you grateful for today?", 
            size_hint_y=None, 
            height=dp(40),
            font_size=dp(16)
        )
        content.add_widget(title_label)
        
        # Today's date display
        today_str = datetime.now().strftime('%A, %d %B %Y')
        date_label = Label(
            text=f"Today: {today_str}",
            size_hint_y=None,
            height=dp(30),
            font_size=dp(14)
        )
        content.add_widget(date_label)
        
        # Existing entries for today (if any)
        today_key = datetime.now().strftime('%Y-%m-%d')
        today_entries = self.gratitude_entries.get(today_key, [])
        
        if today_entries:
            content.add_widget(Label(
                text="Today's entries:",
                size_hint_y=None,
                height=dp(30)
            ))
            
            entries_scroll = ScrollView(size_hint=(1, 0.3))
            entries_layout = GridLayout(cols=1, spacing=dp(5), size_hint_y=None)
            entries_layout.bind(minimum_height=entries_layout.setter('height'))
            
            for entry in today_entries:
                entry_text = entry.get('text', '')
                entry_time = datetime.fromisoformat(entry.get('timestamp', '')).strftime('%H:%M:%S')
                entry_label = Label(
                    text=f"[{entry_time}] {entry_text}",
                    size_hint_y=None,
                    height=dp(30),
                    halign='left'
                )
                entry_label.bind(size=lambda *x: setattr(entry_label, 'text_size', (entry_label.width, None)))
                entries_layout.add_widget(entry_label)
                
            entries_scroll.add_widget(entries_layout)
            content.add_widget(entries_scroll)
        
        # Input for new entry
        content.add_widget(Label(
            text="New gratitude entry:",
            size_hint_y=None,
            height=dp(30)
        ))
        
        gratitude_input = TextInput(
            hint_text="I am grateful for...",
            multiline=True,
            size_hint=(1, 0.4)
        )
        content.add_widget(gratitude_input)
        
        # Buttons
        button_layout = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        save_button = Button(text='Save Entry')
        close_button = Button(text='Close')
        button_layout.add_widget(save_button)
        button_layout.add_widget(close_button)
        content.add_widget(button_layout)
        
        # Create and configure popup
        popup_height = min(dp(500), Window.height * 0.7)
        popup_width = min(dp(500), Window.width * 0.7)
        self._gratitude_popup = Popup(
            title='Gratitude Journal',
            content=content,
            size_hint=(None, None),
            size=(popup_width, popup_height),
            auto_dismiss=False
        )
        
        # Button actions
        def save_gratitude(instance):
            entry_text = gratitude_input.text.strip()
            if entry_text:
                if self.add_gratitude_entry(entry_text):
                    # Clear input and refresh the popup to show the new entry
                    gratitude_input.text = ""
                    self._gratitude_popup.dismiss()
                    Clock.schedule_once(lambda dt: self.add_gratitude_gui(None), 0.1)
            else:
                show_error_popup("Please enter something you're grateful for.")
        
        save_button.bind(on_press=save_gratitude)
        close_button.bind(on_press=self._gratitude_popup.dismiss)
        self._gratitude_popup.bind(on_dismiss=lambda x: setattr(self, '_gratitude_popup', None))
        
        # Show the popup
        self._gratitude_popup.open()
        gratitude_input.focus = True

    # --- Due Date Implementation ---
    def set_due_date_gui(self, instance):
        if self.selected_index is None: show_error_popup("Select a task first."); return
        if not (0 <= self.selected_index < len(self.tasks)): return
        task_index = self.selected_index; task = self.tasks[task_index]; task_title = task.get('task', 'Task'); current_due_date_str = task.get('due_date')
        now = datetime.now(); current_year, current_month_name, current_day = now.year, calendar.month_name[now.month], now.day
        if current_due_date_str:
            try: parsed_date = datetime.strptime(current_due_date_str, '%d-%B-%Y'); current_year, current_month_name, current_day = parsed_date.year, calendar.month_name[parsed_date.month], parsed_date.day
            except (ValueError, TypeError) as e: logging.warning(f"Could not parse due date '{current_due_date_str}': {e}. Defaulting to today.")
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10)); content.add_widget(Label(text='Select Due Date:', size_hint_y=None, height=dp(25)))
        date_grid = GridLayout(cols=3, spacing=dp(5), size_hint_y=None, height=dp(40)); year_values = [str(y) for y in range(now.year - 1, now.year + 10)]; year_spinner = Spinner(text=str(current_year), values=year_values, size_hint_x=0.4); month_values = [calendar.month_name[m] for m in range(1, 13)]; month_spinner = Spinner(text=current_month_name, values=month_values, size_hint_x=0.4); day_values = [str(d) for d in range(1, 32)]; day_spinner = Spinner(text=str(current_day), values=day_values, size_hint_x=0.2); date_grid.add_widget(year_spinner); date_grid.add_widget(month_spinner); date_grid.add_widget(day_spinner); content.add_widget(date_grid)
        def update_days(*args):
            # Outer try for general errors in getting year/month/day
            try:
                year = int(year_spinner.text); month_str = month_spinner.text; month_list = list(calendar.month_name); month = month_list.index(month_str) if month_str in month_list else 1; _, num_days = calendar.monthrange(year, month); current_day_val = int(day_spinner.text) if day_spinner.text.isdigit() else 1; day_spinner.values = [str(d) for d in range(1, num_days + 1)];

                # Inner try specifically for adjusting the day value based on num_days
                try:
                    if current_day_val > num_days:
                        day_spinner.text = '1'
                    else: # This else pairs with the 'if current_day_val > num_days'
                       if day_spinner.text not in day_spinner.values:
                           day_spinner.text = str(min(current_day_val, num_days))

                except Exception as e: # Catch errors from the inner logic
                    logging.error(f"Error checking/setting day spinner value (Due Date): {e}")
                    # Fallback if something went wrong inside the inner try
                    if day_spinner.text not in day_spinner.values:
                        day_spinner.text = '1'

            except (ValueError, IndexError) as e:
                 logging.warning(f"Error updating day spinner (Due Date - outer): {e}");
                 day_spinner.values = [str(d) for d in range(1, 32)] # Fallback values

        year_spinner.bind(text=update_days); month_spinner.bind(text=update_days); update_days()
        button_layout = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10)); save_button = Button(text='Save Due Date'); clear_button = Button(text='Clear Due Date'); cancel_button = Button(text='Cancel'); button_layout.add_widget(save_button); button_layout.add_widget(clear_button); button_layout.add_widget(cancel_button); content.add_widget(button_layout)
        content.bind(minimum_height=content.setter('height')); popup_height = max(dp(220), content.minimum_height + dp(70)); popup_width = min(dp(450), Window.width * 0.6); due_date_popup = Popup(title=f'Set Due Date for: {task_title[:30]}{"..." if len(task_title)>30 else ""}', content=content, size_hint=(None, None), size=(popup_width, popup_height), auto_dismiss=False)
        save_button.bind(on_press=lambda instance: self._save_due_date(task_index, year_spinner, month_spinner, day_spinner, due_date_popup)); clear_button.bind(on_press=lambda instance: self._clear_due_date(task_index, due_date_popup)); cancel_button.bind(on_press=due_date_popup.dismiss); due_date_popup.open()
    def _save_due_date(self, task_index, year_spin, month_spin, day_spin, popup_instance):
        try:
            year, month_str, day = int(year_spin.text), month_spin.text, int(day_spin.text); month_list = list(calendar.month_name); month = month_list.index(month_str) if month_str in month_list else 0;
            if month == 0: raise ValueError("Invalid month selected.")
            selected_date = datetime(year, month, day); due_date_str = selected_date.strftime('%d-%B-%Y')
            if not (0 <= task_index < len(self.tasks)): raise IndexError("Task index out of bounds.")
            task = self.tasks[task_index]; task['due_date'] = due_date_str; self.mark_tasks_changed(); logging.info(f"Set due date for task {task_index} to {due_date_str}"); popup_instance.dismiss(); self.update_task_view()
        except (ValueError, IndexError, TypeError) as e: show_error_popup(f"Invalid due date setting:\n{e}")
        except Exception as e: logging.error(f"Error saving due date: {e}", exc_info=True); show_error_popup(f"Error setting due date:\n{e}")
    def _clear_due_date(self, task_index, popup_instance):
        try:
            if not (0 <= task_index < len(self.tasks)): raise IndexError("Task index out of bounds.")
            task = self.tasks[task_index];
            if task.get('due_date') is not None: task['due_date'] = None; self.mark_tasks_changed(); logging.info(f"Cleared due date for task {task_index}")
            popup_instance.dismiss(); self.update_task_view()
        except IndexError: show_error_popup("Error: Task not found.")
        except Exception as e: logging.error(f"Error clearing due date: {e}", exc_info=True); show_error_popup(f"Error clearing due date:\n{e}")

    # --- Alarm System Implementation ---
    def _get_available_alarm_sounds(self):
        sounds = ["(None)"];
        if not os.path.exists(ALARM_FOLDER): logging.warning(f"Alarm sound folder not found: {ALARM_FOLDER}"); return sounds
        try:
            for filename in sorted(os.listdir(ALARM_FOLDER)):
                if filename.lower().endswith(('.mp3', '.wav', '.ogg')): sounds.append(filename)
        except OSError as e: logging.error(f"Error reading alarm folder '{ALARM_FOLDER}': {e}")
        return sounds
    def set_alarm_gui(self, instance):
        if self.selected_index is None: show_error_popup("Select a task first."); return
        if not (0 <= self.selected_index < len(self.tasks)): return
        task_index = self.selected_index; task = self.tasks[task_index]; task_title = task.get('task', 'Task'); available_sounds = self._get_available_alarm_sounds(); content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10)); content.add_widget(Label(text='Current Alarms:', size_hint_y=None, height=dp(25))); existing_alarms_scroll = ScrollView(size_hint=(1, 0.35), do_scroll_x=False, bar_width=dp(10)); existing_alarms_layout = GridLayout(cols=1, spacing=dp(5), size_hint_y=None); existing_alarms_layout.bind(minimum_height=existing_alarms_layout.setter('height')); current_alarms = task.get('alarms', [])
        if not current_alarms: existing_alarms_layout.add_widget(Label(text='No alarms set for this task.', size_hint_y=None, height=dp(30)))
        else:
            now_ts = time.time()
            for alarm_entry in current_alarms:
                alarm_id = alarm_entry.get('id'); alarm_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(5)); ts_unix = alarm_entry.get('target_timestamp_unix'); formatted_time = "Invalid Time"; is_active = False; is_past = False
                if isinstance(ts_unix, (int, float)):
                    try: dt_local = datetime.fromtimestamp(ts_unix); formatted_time = dt_local.strftime('%Y-%m-%d %H:%M:%S'); is_enabled = alarm_entry.get('enabled', False); is_past = ts_unix <= now_ts; is_active = is_enabled and not is_past
                    except (ValueError, OSError): formatted_time = f"Timestamp: {ts_unix}"
                sound = os.path.basename(alarm_entry.get('sound_file', 'N/A'));
                if is_active: status_str = "[color=00ff00](Active)[/color]"
                elif is_past and alarm_entry.get('enabled'): status_str = "[color=ffff00](Past/Triggered)[/color]"
                else: status_str = "[color=ff0000](Inactive)[/color]"
                alarm_label = Label(text=f"{formatted_time} - {sound} {status_str}", markup=True, size_hint_x=0.85, halign='left', valign='middle'); alarm_label.bind(size=lambda *args: setattr(alarm_label, 'text_size', (alarm_label.width, None))); alarm_row.add_widget(alarm_label); delete_btn = Button(text='Del', size_hint=(None, 1), width=dp(50), on_press=lambda inst, t_idx=task_index, a_id=alarm_id: self._delete_alarm_and_refresh(t_idx, a_id)); alarm_row.add_widget(delete_btn); existing_alarms_layout.add_widget(alarm_row)
        existing_alarms_scroll.add_widget(existing_alarms_layout); content.add_widget(existing_alarms_scroll); content.add_widget(BoxLayout(size_hint_y=None, height=dp(5))); content.add_widget(Label(text='Set New Alarm:', size_hint_y=None, height=dp(25))); new_alarm_grid = GridLayout(cols=2, spacing=dp(5), size_hint_y=None, height=dp(130)); now = datetime.now(); new_alarm_grid.add_widget(Label(text='Date (Y/M/D):')); date_box = BoxLayout(spacing=dp(3)); year_spinner = Spinner(text=str(now.year), values=[str(y) for y in range(now.year, now.year + 6)], size_hint_x=0.4); month_spinner = Spinner(text=calendar.month_name[now.month], values=[calendar.month_name[m] for m in range(1, 13)], size_hint_x=0.4); day_spinner = Spinner(text=str(now.day), values=[str(d) for d in range(1, 32)], size_hint_x=0.2); date_box.add_widget(year_spinner); date_box.add_widget(month_spinner); date_box.add_widget(day_spinner); new_alarm_grid.add_widget(date_box)
        def update_days(*args):
             # Outer try for general errors in getting year/month/day
            try:
                year = int(year_spinner.text)
                month_str = month_spinner.text
                month_list = list(calendar.month_name)
                month = month_list.index(month_str) if month_str in month_list else 1
                _, num_days = calendar.monthrange(year, month)
                current_day_val = int(day_spinner.text) if day_spinner.text.isdigit() else 1
                day_spinner.values = [str(d) for d in range(1, num_days + 1)]

                # Inner try specifically for adjusting the day value based on num_days
                try:
                    if current_day_val > num_days:
                        day_spinner.text = '1'
                    else:
                        if day_spinner.text not in day_spinner.values:
                            day_spinner.text = str(min(current_day_val, num_days))
                except Exception as e:
                    logging.error(f"Error checking/setting day spinner value (Alarm): {e}")
                    # Fallback if something went wrong inside the inner try
                    if day_spinner.text not in day_spinner.values:
                        day_spinner.text = '1'
            except (ValueError, IndexError) as e:
                logging.warning(f"Error updating day spinner (Alarm - outer): {e}")
                day_spinner.values = [str(d) for d in range(1, 32)]  # Fallback values

        new_alarm_grid.add_widget(Label(text='Time (H:M:S):')); time_box = BoxLayout(spacing=dp(3)); hour_spinner = Spinner(text='00', values=[str(h).zfill(2) for h in range(24)], size_hint_x=0.2); minute_spinner = Spinner(text='00', values=[str(m).zfill(2) for m in range(60)], size_hint_x=0.2); second_spinner = Spinner(text='00', values=[str(s).zfill(2) for s in range(60)], size_hint_x=0.2); time_box.add_widget(hour_spinner); time_box.add_widget(minute_spinner); time_box.add_widget(second_spinner); new_alarm_grid.add_widget(time_box)
        new_alarm_grid.add_widget(Label(text='AM/PM:')); ampm_spinner = Spinner(text='AM', values=['AM', 'PM'], size_hint_x=0.2); new_alarm_grid.add_widget(ampm_spinner)
        new_alarm_grid.add_widget(Label(text='Alarm Sound:'))
        sound_spinner = Spinner(text='(None)', values=available_sounds, size_hint_x=0.4)
        # Add upload button next to spinner
        sound_row = BoxLayout(orientation='horizontal', spacing=dp(5))
        sound_row.add_widget(sound_spinner)
        upload_button = Button(text='Upload', size_hint_x=0.3, size_hint_y=None, height=dp(32))
        def upload_alarm_sound(instance):
            self._open_alarm_sound_uploader(sound_spinner)
        upload_button.bind(on_press=upload_alarm_sound)
        sound_row.add_widget(upload_button)
        new_alarm_grid.add_widget(sound_row)
        content.add_widget(new_alarm_grid)
        button_layout = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10)); save_button = Button(text='Save Alarm'); cancel_button = Button(text='Cancel'); button_layout.add_widget(save_button); button_layout.add_widget(cancel_button); content.add_widget(button_layout)
        content.bind(minimum_height=content.setter('height')); popup_height = max(dp(420), content.minimum_height + dp(70)); popup_width = min(dp(450), Window.width * 0.6); alarm_popup = Popup(title=f'Set Alarm for: {task_title[:30]}{"..." if len(task_title)>30 else ""}', content=content, size_hint=(None, None), size=(popup_width, popup_height), auto_dismiss=False)
        save_button.bind(on_press=lambda instance: self._save_alarm(task_index, year_spinner, month_spinner, day_spinner, hour_spinner, minute_spinner, second_spinner, ampm_spinner, sound_spinner, alarm_popup)); cancel_button.bind(on_press=alarm_popup.dismiss); alarm_popup.open()

    def _open_alarm_sound_uploader(self, sound_spinner=None):
        import threading
        import tkinter as tk
        from tkinter import filedialog
        import shutil
        import os
        from kivy.clock import Clock

        def open_file_picker():
            root = tk.Tk()
            root.withdraw()
            start_path = os.path.expanduser('~')
            filetypes = [
                ("Audio files", ".mp3 .wav .ogg"),
                ("All files", "*.*")
            ]
            file_path = filedialog.askopenfilename(
                title="Select Alarm Sound",
                initialdir=start_path,
                filetypes=filetypes
            )
            root.destroy()
            def handle_selection():
                if file_path:
                    try:
                        alarm_folder = ALARM_FOLDER if os.path.isabs(ALARM_FOLDER) else os.path.join(os.getcwd(), ALARM_FOLDER)
                        if not os.path.exists(alarm_folder):
                            os.makedirs(alarm_folder)
                        dest_path = os.path.join(alarm_folder, os.path.basename(file_path))
                        shutil.copy2(file_path, dest_path)
                        if sound_spinner is not None:
                            # Refresh the spinner values and select the new file
                            sound_spinner.values = self._get_available_alarm_sounds()
                            sound_spinner.text = os.path.basename(file_path)
                        show_confirmation_popup(f"Alarm sound uploaded successfully:\n{os.path.basename(file_path)}")
                    except Exception as e:
                        show_error_popup(f"Failed to upload alarm sound:\n{e}")
            Clock.schedule_once(lambda dt: handle_selection())

        threading.Thread(target=open_file_picker, daemon=True).start()

    def _reorder_task(self, from_idx, to_idx):
        if from_idx == to_idx or not (0 <= from_idx < len(self.tasks)) or not (0 <= to_idx < len(self.tasks)):
            return
        task = self.tasks.pop(from_idx)
        self.tasks.insert(to_idx, task)
        self.mark_tasks_changed()
        self.update_task_view()
        
    def _insert_task_at_position(self, from_idx, to_position):
        """Insert a task at a specific position, pushing other tasks up or down"""
        if not (0 <= from_idx < len(self.tasks)):
            return
            
        # Clamp to_position to valid range
        to_position = max(0, min(len(self.tasks), to_position))
        
        # If inserting at the same position, do nothing
        if from_idx == to_position or (from_idx + 1 == to_position):
            return
            
        # Remove the task from its current position
        task = self.tasks.pop(from_idx)
        
        # Adjust insertion position if we removed an item before it
        if from_idx < to_position:
            to_position -= 1
            
        # Insert at the new position
        self.tasks.insert(to_position, task)
        
        # Update selected index if needed
        if self.selected_index == from_idx:
            self.selected_index = to_position
        elif self.selected_index is not None:
            if from_idx < self.selected_index <= to_position:
                self.selected_index -= 1
            elif to_position <= self.selected_index < from_idx:
                self.selected_index += 1
        
        self.mark_tasks_changed()
        self.update_task_view()
        
        logging.info(f"Inserted task from position {from_idx} to position {to_position}")

    def prompt_new_task_for_date(self, due_date_str):
        from kivy.uix.textinput import TextInput
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        label = Label(text=f"Enter a name for the new task due on {due_date_str}:", size_hint_y=None, height=dp(30))
        task_input = TextInput(hint_text='Task name', multiline=False, size_hint_y=None, height=dp(40))
        content.add_widget(label)
        content.add_widget(task_input)
        button_layout = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        ok_button = Button(text='Create')
        cancel_button = Button(text='Cancel')
        button_layout.add_widget(ok_button)
        button_layout.add_widget(cancel_button)
        content.add_widget(button_layout)
        popup = Popup(title='New Task for Date', content=content, size_hint=(0.7, None), height=dp(200), auto_dismiss=False)
        def create_task(instance):
            name = task_input.text.strip()
            if name:
                self.add_task_with_due_date(name, due_date_str)
                popup.dismiss()
            else:
                task_input.hint_text = "Task name cannot be empty!"
                task_input.background_color = (1, 0.8, 0.8, 1)
        ok_button.bind(on_press=create_task)
        cancel_button.bind(on_press=popup.dismiss)
        popup.open()

    def add_task_with_due_date(self, task_name, due_date_str):
        if not task_name or not task_name.strip():
            show_error_popup("Task name cannot be empty.")
            return
        try:
            now_iso = datetime.now().isoformat()
            new_task = {
                'task': task_name.strip(),
                'timer': 0,
                'localTime': datetime.now(PH_TZ).strftime('%Y-%m-%d %H:%M:%S %Z'),
                'createdAt': now_iso,
                'timer_running': False,
                'start_time_unix': None,
                'completed': False,
                'due_date': due_date_str,
                'icon': None,
                'alarms': [],
                'annotations': [],
                'titleHistory': [{'title': task_name.strip(), 'timestamp': now_iso}]
            }
            self.tasks.append(new_task)
            self.mark_tasks_changed()
            self.update_task_view()
            logging.info(f"Added task '{task_name}' with due date {due_date_str}")
            new_index = len(self.tasks) - 1
            self.select_task(new_index)
            if hasattr(self, 'task_list_layout') and new_index in self.task_widgets:
                scroll_view = self.task_list_layout.parent
                if scroll_view:
                    widget_to_scroll = self.task_widgets.get(new_index)
                    if widget_to_scroll:
                        scroll_view.scroll_to(widget_to_scroll, padding=dp(10), animate=True)
        except Exception as e:
            logging.error(f"Error adding task '{task_name}' with due date {due_date_str}: {e}", exc_info=True)
            show_error_popup("Failed to add the task.")

    def setup_gui(self, instance):
        content = BoxLayout(orientation='vertical', spacing=dp(15), padding=[dp(15), dp(100), dp(15), dp(15)])
        content.add_widget(Label(text='Groq API Settings', size_hint_y=None, height=dp(35), font_size=dp(16), bold=True))

        # Row for Groq API Key input and help button
        api_row = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(40))
        api_key_input = TextInput(text=os.getenv('GROQ_API_KEY', ''), hint_text='Groq API Key', multiline=False, size_hint_x=0.7)
        def open_groq_help(instance):
            import webbrowser
            webbrowser.open('https://console.groq.com/keys')
        help_button = Button(text='?', size_hint_x=0.15, size_hint_y=None, height=dp(40), background_color=(0.7,0.8,1,1), bold=True)
        help_button.bind(on_press=open_groq_help)
        api_row.add_widget(api_key_input)
        api_row.add_widget(help_button)
        content.add_widget(api_row)

        # Model and prompt
        model_input = TextInput(text=os.getenv('GROQ_MODEL_NAME', 'llama3-70b-8192'), hint_text='Groq Model Name', multiline=False, size_hint_y=None, height=dp(30))
        prompt_input = TextInput(text=os.getenv('SYSTEM_PROMPT', 'You are a helpful assistant.'), hint_text='System Prompt', multiline=True, size_hint_y=None, height=dp(60))
        # Model Name row with help button
        model_row = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(40))
        model_row.add_widget(model_input)
        def open_model_help(instance):
            import webbrowser
            webbrowser.open('https://console.groq.com/docs/models')
        model_help_button = Button(text='?', size_hint_x=0.15, size_hint_y=None, height=dp(40), background_color=(0.7,0.8,1,1), bold=True)
        model_help_button.bind(on_press=open_model_help)
        model_row.add_widget(model_help_button)
        content.add_widget(Label(text='Model Name:', size_hint_y=None, height=dp(25)))
        content.add_widget(model_row)
        # Hint text under the model name field
        content.add_widget(Label(text='Copy the MODEL ID and paste it in the field above ^', size_hint_y=None, height=dp(20), font_size=dp(13), color=(0.4,0.4,0.4,1)))
        # System Prompt row with help button
        sys_prompt_row = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(40))
        sys_prompt_row.add_widget(prompt_input)
        def show_sys_prompt_help(instance):
            popup = Popup(
                title='What is a System Prompt?',
                content=Label(
                    text=(
                        "System prompts are the hidden instructions that set the stage for a language model's behavior during an interaction. "
                        "They provide context, guide tone, and even determine when to invoke specific tool calls. When designed well, these prompts help LLMs deliver reliable and tailored responses for your applications."
                    ),
                    size_hint_y=None,
                    height=dp(180),
                    font_size=dp(15),
                    halign='left',
                    valign='top',
                    text_size=(dp(420), None),
                ),
                size_hint=(None, None),
                size=(dp(480), dp(250)),
                auto_dismiss=True
            )
            popup.open()
        sys_prompt_help_button = Button(text='?', size_hint_x=0.15, size_hint_y=None, height=dp(40), background_color=(0.7,0.8,1,1), bold=True)
        sys_prompt_help_button.bind(on_press=show_sys_prompt_help)
        sys_prompt_row.add_widget(sys_prompt_help_button)
        content.add_widget(Label(text='System Prompt:', size_hint_y=None, height=dp(25)))
        content.add_widget(sys_prompt_row)


        # --- User Display Name ---
        display_name_input = TextInput(text=os.getenv('USER_DISPLAY_NAME', ''), hint_text="What's your name?", multiline=False, size_hint_y=None, height=dp(40))
        content.add_widget(Label(text="What's your name?", size_hint_y=None, height=dp(25)))
        content.add_widget(display_name_input)

        # Background image selection
        content.add_widget(Label(text='Background Image', size_hint_y=None, height=dp(25), font_size=dp(16), bold=True))
        bg_box = BoxLayout(orientation='horizontal', spacing=dp(5), size_hint_y=None, height=dp(40))
        self._background_spinner = Spinner(text="(None)", values=self._get_available_backgrounds(), size_hint_x=0.7)
        current_bg_path = os.getenv('BACKGROUND_IMAGE_PATH', '')
        if current_bg_path and os.path.exists(current_bg_path):
            current_bg_file = os.path.basename(current_bg_path)
            if current_bg_file in self._background_spinner.values:
                self._background_spinner.text = current_bg_file
        bg_box.add_widget(self._background_spinner)
        upload_button = Button(text='Upload New', size_hint_x=0.3, on_press=self._open_background_uploader)
        bg_box.add_widget(upload_button)
        content.add_widget(bg_box)

        # --- Todoist API Token ---
        # Row for Todoist API Token input and help button
        todoist_row = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(40))
        todoist_token_input = TextInput(text=os.getenv('TODOIST_API_TOKEN', ''), hint_text='Todoist API Token', multiline=False, size_hint_x=0.7)
        def open_todoist_help(instance):
            import webbrowser
            webbrowser.open('https://www.todoist.com/help/articles/find-your-api-token-Jpzx9IIlB')
        todoist_help_button = Button(text='?', size_hint_x=0.15, on_press=open_todoist_help)
        todoist_row.add_widget(todoist_token_input)
        todoist_row.add_widget(todoist_help_button)
        content.add_widget(Label(text='Todoist API Token:', size_hint_y=None, height=dp(25)))
        content.add_widget(todoist_row)

        # Save/Cancel buttons
        action_buttons = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        save_button = Button(text='Save Settings')
        cancel_button = Button(text='Cancel')
        action_buttons.add_widget(save_button)
        action_buttons.add_widget(cancel_button)
        content.add_widget(action_buttons)

        popup_height = min(dp(700), Window.height * 0.95)
        popup_width = min(dp(800), Window.width * 0.95)
        self._setup_popup = Popup(title='Application Setup', content=content, size_hint=(None, None), size=(popup_width, popup_height), auto_dismiss=False)
        self._setup_popup.bind(on_dismiss=lambda x: setattr(self, '_setup_popup', None))
        save_button.bind(on_press=lambda instance: self._save_setup_settings(api_key_input.text, model_input.text, prompt_input.text, self._background_spinner.text, self._setup_popup, display_name_input.text, todoist_token_input.text))
        cancel_button.bind(on_press=self._setup_popup.dismiss)
        self._setup_popup.open()

    def _save_setup_settings(self, api_key, model_name, prompt, background_image, popup, user_display_name, todoist_token=None):
        """
        Save the setup settings, including user display name, to tasks.json in the meta section. Also saves API keys and background to .env.
        """
        import json
        import os
        from dotenv import set_key
        logging.info(f"_save_setup_settings called with user_display_name={user_display_name}, background_image={background_image}")
        
        # Save settings to .env file
        try:
            env_path = os.path.join(os.getcwd(), '.env')
            
            # Save API keys and settings
            if api_key:
                set_key(env_path, 'GROQ_API_KEY', api_key)
            if model_name:
                set_key(env_path, 'GROQ_MODEL_NAME', model_name)
            if prompt:
                set_key(env_path, 'SYSTEM_PROMPT', prompt)
            if user_display_name:
                set_key(env_path, 'USER_DISPLAY_NAME', user_display_name)
            if todoist_token is not None:
                set_key(env_path, 'TODOIST_API_TOKEN', todoist_token)
                
            # Handle background image selection
            if background_image and background_image != "(None)":
                # If it's just a filename, construct the full path
                if not os.path.isabs(background_image):
                    background_path = os.path.join('graphics', 'background', background_image)
                else:
                    background_path = background_image
                    
                # Verify the file exists
                if os.path.exists(background_path):
                    set_key(env_path, 'BACKGROUND_IMAGE_PATH', background_path)
                    # Apply the background immediately
                    self._apply_background_image(background_path)
                    logging.info(f"Background image set to: {background_path}")
                else:
                    logging.warning(f"Background image file not found: {background_path}")
            elif background_image == "(None)":
                # Clear background image
                set_key(env_path, 'BACKGROUND_IMAGE_PATH', '')
                self._apply_background_image(None)
                logging.info("Background image cleared")
                
        except Exception as e:
            logging.error(f"Failed to save settings to .env: {e}")
            show_error_popup(f"Failed to save settings to .env:\n{e}")
            return
            
        try:
            # Load existing data for user display name in tasks.json
            try:
                with open(TASKS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except FileNotFoundError:
                data = {}
            except json.JSONDecodeError:
                data = {}

            # If old format (just a list), convert to dict
            if isinstance(data, list):
                data = {"tasks": data}

            # Save display name in tasks.json
            data["user_display_name"] = user_display_name
            self.user_display_name = user_display_name
            logging.info(f"Saving user_display_name to tasks.json: {user_display_name}")

            # Write back to file
            with open(TASKS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logging.info(f"Wrote data to tasks.json: {list(data.keys())}")
            
            if popup:
                popup.dismiss()
            show_confirmation_popup("Settings saved successfully!")
            
        except Exception as e:
            logging.error(f"Error saving settings to tasks.json: {e}", exc_info=True)
            show_error_popup(f"Failed to save settings:\n{e}")


    def _save_alarm(self, task_index, year_spin, month_spin, day_spin, hour_spin, minute_spin, second_spin, ampm_spin, sound_spin, popup_instance):
        try:
            year, month_str, day = int(year_spin.text), month_spin.text, int(day_spin.text); month_list = list(calendar.month_name); month = month_list.index(month_str) if month_str in month_list else 0;
            if month == 0: raise ValueError("Invalid month selected.")
            hour, minute, second = int(hour_spin.text), int(minute_spin.text), int(second_spin.text); ampm = ampm_spin.text; sound_file_short = sound_spin.text
            if sound_file_short == "(None)": raise ValueError("Please select an alarm sound.")
            sound_file_full = os.path.join(ALARM_FOLDER, sound_file_short);
            if not os.path.exists(sound_file_full): raise ValueError(f"Sound file not found:\n{sound_file_short}")
            hour_24 = hour;
            if ampm == 'PM' and hour != 12: hour_24 += 12
            elif ampm == 'AM' and hour == 12: hour_24 = 0
            target_dt = datetime(year, month, day, hour_24, minute, second); target_timestamp_unix = target_dt.timestamp()
            if target_timestamp_unix <= time.time(): raise ValueError("Alarm time must be in the future.")
            alarm_id = f"{task_index}_{target_timestamp_unix}_{uuid4().hex[:6]}"; alarm_entry = {"id": alarm_id, "target_timestamp_unix": target_timestamp_unix, "sound_file": sound_file_full, "enabled": True}
            if not (0 <= task_index < len(self.tasks)): raise IndexError("Task index out of bounds.")
            task = self.tasks[task_index]; task['alarms'].append(alarm_entry); self.mark_tasks_changed()
            if self._schedule_alarm(task_index, alarm_entry): logging.info(f"Set and scheduled alarm {alarm_id} for task {task_index} at {target_dt}")
            else: logging.error(f"Failed to schedule newly created alarm {alarm_id}")
            popup_instance.dismiss(); Clock.schedule_once(lambda dt: self.set_alarm_gui(None), 0.1)
        except (ValueError, IndexError, TypeError) as e: show_error_popup(f"Invalid alarm setting:\n{e}")
        except Exception as e: logging.error(f"Error saving alarm: {e}", exc_info=True); show_error_popup(f"An unexpected error occurred setting the alarm:\n{e}")
    def _schedule_alarm(self, task_index, alarm_entry):
        target_timestamp = alarm_entry.get('target_timestamp_unix'); alarm_id = alarm_entry.get('id'); sound_file = alarm_entry.get('sound_file'); is_enabled = alarm_entry.get('enabled', False)
        if not all([target_timestamp, alarm_id, sound_file]): logging.error(f"Cannot schedule alarm: Missing data in entry for task {task_index}: {alarm_entry}"); return False
        if not is_enabled: return False
        if not os.path.exists(sound_file): logging.error(f"Cannot schedule alarm {alarm_id}: Sound file not found '{sound_file}'"); alarm_entry['enabled'] = False; self.mark_tasks_changed(); show_error_popup(f"Alarm sound missing:\n{os.path.basename(sound_file)}\nAlarm disabled."); return False
        delay_seconds = target_timestamp - time.time()
        if delay_seconds <= 0:
             if alarm_entry.get('enabled'): alarm_entry['enabled'] = False; self.mark_tasks_changed()
             return False
        existing_event = self.scheduled_alarms.pop(alarm_id, None);
        if existing_event: existing_event.cancel()
        try: clock_event = Clock.schedule_once(lambda dt: self._trigger_alarm_action(task_index, alarm_id), delay_seconds); self.scheduled_alarms[alarm_id] = clock_event; logging.info(f"Scheduled alarm {alarm_id} (Task {task_index}) -> Trigger in {delay_seconds:.2f}s."); return True
        except Exception as e: logging.error(f"Failed to schedule alarm {alarm_id}: {e}", exc_info=True); self.scheduled_alarms.pop(alarm_id, None); return False
    def _trigger_alarm_action(self, task_index, alarm_id):
        logging.info(f"Triggering alarm action -> Task Index: {task_index}, Alarm ID: {alarm_id}"); self.scheduled_alarms.pop(alarm_id, None)
        if not (0 <= task_index < len(self.tasks)): logging.warning(f"Alarm triggered for non-existent task index {task_index}. Alarm ID: {alarm_id}"); return
        task = self.tasks[task_index]; alarm_entry = next((a for a in task.get('alarms', []) if a.get('id') == alarm_id), None)
        if not alarm_entry: logging.warning(f"Alarm {alarm_id} triggered but not found in task {task_index} data."); return
        if not alarm_entry.get('enabled'): logging.info(f"Alarm {alarm_id} triggered but is disabled. Ignoring."); return
        sound_file = alarm_entry.get('sound_file')
        if not sound_file or not os.path.exists(sound_file): logging.error(f"Alarm {alarm_id} sound file '{sound_file}' missing at trigger time! Disabling alarm."); alarm_entry['enabled'] = False; self.mark_tasks_changed(); show_error_popup(f"Alarm for task:\n'{task.get('task', 'N/A')}'\n\nSound file missing:\n{os.path.basename(sound_file)}"); return
        try:
            if not pygame.mixer.get_init(): pygame.mixer.init()
            pygame.mixer.music.load(sound_file); pygame.mixer.music.play(loops=-1); logging.info(f"Playing alarm sound: {sound_file} for alarm {alarm_id}")
            content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10)); msg = f"ALARM!\n\nTask:\n'{task.get('task', 'N/A')}'"; label = Label(text=msg, halign='center', valign='middle'); label.bind(size=lambda *x: setattr(label, 'text_size', (content.width*0.95, None))); content.add_widget(label); dismiss_button = Button(text='Dismiss', size_hint_y=None, height=dp(40)); content.add_widget(dismiss_button); content.bind(minimum_height=content.setter('height')); popup_height = max(dp(180), content.minimum_height + dp(70)); alarm_popup = Popup(title='ALARM!', content=content, size_hint=(0.6, None), height=popup_height, auto_dismiss=False)
            def dismiss_action(instance):
                try:
                    if pygame.mixer.get_init(): pygame.mixer.music.stop()
                except pygame.error as e: logging.warning(f"Pygame error stopping music during dismiss: {e}")
                alarm_entry['enabled'] = False; self.mark_tasks_changed(); alarm_popup.dismiss(); logging.info(f"Alarm {alarm_id} dismissed by user and disabled.")
                if hasattr(self, 'alarm_popup') and self.alarm_popup and self.alarm_popup.content: self.alarm_popup.dismiss(); Clock.schedule_once(lambda dt: self.set_alarm_gui(None), 0.1)
            dismiss_button.bind(on_press=dismiss_action); alarm_popup.open()
        except pygame.error as e: logging.error(f"Pygame error playing alarm {alarm_id} sound '{sound_file}': {e}"); alarm_entry['enabled'] = False; self.mark_tasks_changed(); show_error_popup(f"Error playing alarm sound for:\n'{task.get('task', 'N/A')}'\n\nError: {e}")
        except Exception as e: logging.error(f"Unexpected error during alarm trigger {alarm_id}: {e}", exc_info=True); alarm_entry['enabled'] = False; self.mark_tasks_changed(); show_error_popup(f"Unexpected error during alarm for:\n'{task.get('task', 'N/A')}'")
    def _reschedule_pending_alarms(self):
        logging.info("Rescheduling pending alarms from loaded tasks..."); rescheduled_count = 0; now_ts = time.time(); tasks_need_saving = False
        for task_index, task in enumerate(self.tasks):
            task_updated = False; alarms_to_keep = []
            for alarm_entry in task.get('alarms', []):
                should_keep = True
                if alarm_entry.get('enabled'):
                    target_time = alarm_entry.get('target_timestamp_unix'); alarm_id = alarm_entry.get('id'); sound_file = alarm_entry.get('sound_file')
                    if not all([target_time, alarm_id, sound_file]): logging.warning(f"Disabling alarm with missing data task {task_index}: {alarm_entry}"); alarm_entry['enabled'] = False; task_updated = True;
                    elif not os.path.exists(sound_file): logging.warning(f"Disabling alarm {alarm_id} task {task_index} due to missing sound file: {sound_file}"); alarm_entry['enabled'] = False; task_updated = True
                    elif target_time <= now_ts:
                        if alarm_entry.get('enabled'): logging.info(f"Disabling past alarm {alarm_id} task {task_index}"); alarm_entry['enabled'] = False; task_updated = True
                    else:
                        if self._schedule_alarm(task_index, alarm_entry): rescheduled_count += 1
                        else: logging.error(f"Failed to reschedule alarm {alarm_id} task {task_index}. Disabling."); alarm_entry['enabled'] = False; task_updated = True
                alarms_to_keep.append(alarm_entry)
            if task_updated: task['alarms'] = alarms_to_keep; tasks_need_saving = True
        if tasks_need_saving: self.mark_tasks_changed()
        if rescheduled_count > 0: logging.info(f"Successfully rescheduled {rescheduled_count} pending alarms.")
        else: logging.info("No pending alarms needed rescheduling.")
    def _delete_alarm_and_refresh(self, task_index, alarm_id):
        if hasattr(self, 'alarm_popup') and self.alarm_popup and self.alarm_popup.content: self.alarm_popup.dismiss(); self.alarm_popup = None
        deleted = self._delete_alarm(task_index, alarm_id);
        if deleted and 0 <= task_index < len(self.tasks): Clock.schedule_once(lambda dt: self.set_alarm_gui(None), 0.1)
    def _delete_alarm(self, task_index, alarm_id):
        if not (0 <= task_index < len(self.tasks)): return False
        task = self.tasks[task_index]; original_length = len(task.get('alarms', []))
        task['alarms'] = [a for a in task.get('alarms', []) if a.get('id') != alarm_id]
        if len(task['alarms']) < original_length:
            event = self.scheduled_alarms.pop(alarm_id, None);
            if event: event.cancel(); logging.info(f"Cancelled scheduled Clock event for deleted alarm {alarm_id}.")
            self.mark_tasks_changed(); logging.info(f"Deleted alarm {alarm_id} from task {task_index}."); return True
        else: logging.warning(f"Could not find alarm ID {alarm_id} to delete in task {task_index}."); return False

    # --- Annotation & Task Icon System Implementation ---

    def annotate_task_gui_proxy(self, instance):
        if self.selected_index is not None: self.annotate_task_gui(self.selected_index)
        else: show_error_popup("Please select a task to annotate.")

    def annotate_task_gui(self, index):
        """Shows the popup for viewing/adding annotations AND selecting task icon."""
        if not (0 <= index < len(self.tasks)): return
        task = self.tasks[index]; task_title = task.get('task', 'Task')

        # --- Build Popup Content ---
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        # Clear existing ids if popup is reused (safer)
        content.ids.clear()

        # --- Task Icon Display & Selection Button ---
        icon_box = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(40))
        icon_box.add_widget(Label(text='Task Icon:', size_hint_x=0.3))
        current_icon_path = task.get('icon', '')
        preview_image = Image(source=current_icon_path if current_icon_path and os.path.exists(current_icon_path) else '', size_hint=(None, None), size=(dp(32), dp(32)), allow_stretch=True, keep_ratio=True)
        preview_image.id = 'annotation_icon_preview' # Assign ID directly
        content.ids['annotation_icon_preview'] = preview_image # Store weakref in ids dictionary
        icon_box.add_widget(preview_image)
        change_icon_button = Button(text='Change...', size_hint_x=0.5)
        # *** MODIFIED: Call the new file chooser function ***
        change_icon_button.bind(on_press=lambda x, idx=index: self._open_task_icon_chooser(idx))
        icon_box.add_widget(change_icon_button); content.add_widget(icon_box)
        content.add_widget(BoxLayout(size_hint_y=None, height=dp(5))) # Spacer
        # --- End Task Icon Display ---

        # --- Annotation History ---
        content.add_widget(Label(text='Annotation History:', size_hint_y=None, height=dp(25)))
        history_scroll = ScrollView(size_hint=(1, 0.55), do_scroll_x=False, bar_width=dp(10))
        history_layout = GridLayout(cols=1, spacing=dp(5), size_hint_y=None); history_layout.bind(minimum_height=history_layout.setter('height'))
        annotations = task.get('annotations', [])
        if not annotations: history_layout.add_widget(Label(text='No previous annotations.', size_hint_y=None, height=dp(30)))
        else:
            for ann_index, annotation_data in enumerate(reversed(annotations)):
                original_index = len(annotations) - 1 - ann_index; ann_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(45), spacing=dp(5)); ts_str = annotation_data.get('timestamp'); formatted_ts = "Unknown Time"
                if ts_str:
                    try: formatted_ts = datetime.fromisoformat(ts_str).strftime('%Y-%m-%d %H:%M:%S')
                    except (ValueError, TypeError): formatted_ts = str(ts_str)
                ann_text = annotation_data.get('text', ''); display_label_text = f"{formatted_ts}:\n{ann_text}"; ann_label = Label(text=display_label_text, size_hint_x=0.85, halign='left', valign='top'); ann_label.bind(size=lambda *args: setattr(ann_label, 'text_size', (ann_label.width, None))); ann_row.add_widget(ann_label); delete_btn = Button(text='Del', size_hint=(None, 1), width=dp(50), on_press=lambda instance, t_idx=index, a_idx=original_index: self._delete_annotation_and_refresh(t_idx, a_idx)); ann_row.add_widget(delete_btn); history_layout.add_widget(ann_row)
        history_scroll.add_widget(history_layout); content.add_widget(history_scroll)
        # --- End Annotation History ---

        # --- New Annotation Input ---
        content.add_widget(Label(text='New Annotation:', size_hint_y=None, height=dp(25)))
        new_annotation_input = TextInput(hint_text='Type annotation here...', multiline=True, size_hint=(1, 0.25))
        content.add_widget(new_annotation_input)
        # --- End New Annotation Input ---

        # --- Action Buttons ---
        button_layout = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10)); save_button = Button(text='Save Annotation'); close_button = Button(text='Close'); button_layout.add_widget(save_button); button_layout.add_widget(close_button); content.add_widget(button_layout)
        # --- End Action Buttons ---

        popup_height = min(dp(650), Window.height * 0.85); popup_width = min(dp(500), Window.width * 0.7)
        self._annotation_popup = Popup(title=f'Details for: {task_title[:40]}{"..." if len(task_title)>40 else ""}', content=content, size_hint=(None, None), size=(popup_width, popup_height), auto_dismiss=False)
        save_button.bind(on_press=lambda instance: self._save_new_annotation(index, new_annotation_input, self._annotation_popup))
        self._annotation_popup.bind(on_dismiss=lambda x: setattr(self, '_annotation_popup', None))
        close_button.bind(on_press=self._annotation_popup.dismiss)
        self._annotation_popup.open(); new_annotation_input.focus = True

    # --- REMOVED _get_available_task_icons ---
    # --- REMOVED _open_icon_selector_popup ---

    # *** NEW: Function to open a file chooser for task icons ***
    def _open_task_icon_chooser(self, task_index):
        import threading
        import tkinter as tk
        from tkinter import filedialog

        def open_file_picker():
            # Open the file picker in a separate thread to avoid blocking Kivy
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            icon_dir = os.path.join(ICON_FOLDER, TASK_ICON_SUBFOLDER)
            start_path = icon_dir if os.path.isdir(icon_dir) else os.path.expanduser('~')
            filetypes = [
                ("Image files", ".png .jpg .jpeg .webp .gif .bmp"),
                ("All files", "*.*")
            ]
            file_path = filedialog.askopenfilename(
                title="Select Task Icon",
                initialdir=start_path,
                filetypes=filetypes
            )
            root.destroy()
            # Pass result back to Kivy's main thread
            def handle_selection():
                # Use the same chooser_popup interface for consistency
                self._handle_task_icon_selection(task_index, [file_path] if file_path else None, chooser_popup)
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: handle_selection())

        # Minimal Kivy popup for clear/cancel
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        info_label = Label(text="Use Windows Explorer to pick an image for your task icon.", size_hint_y=None, height=dp(30))
        button_box = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        select_button = Button(text='Pick Icon...')
        clear_button = Button(text='Clear Icon')
        cancel_button = Button(text='Cancel')
        button_box.add_widget(select_button)
        button_box.add_widget(clear_button)
        button_box.add_widget(cancel_button)
        content.add_widget(info_label)
        content.add_widget(button_box)
        chooser_popup = Popup(title='Select Task Icon', content=content, size_hint=(0.5, 0.2))
        select_button.bind(on_press=lambda x: threading.Thread(target=open_file_picker, daemon=True).start())
        clear_button.bind(on_press=lambda x: self._handle_task_icon_selection(task_index, None, chooser_popup))
        cancel_button.bind(on_press=chooser_popup.dismiss)
        chooser_popup.open()


    # *** NEW: Function to handle the result of the file chooser ***
    def _handle_task_icon_selection(self, task_index, selection, chooser_popup):
        selected_path = None # Default to None (clearing the icon)
        if selection: # If selection list is not empty (i.e., user selected a file)
            source_path = selection[0]
            if os.path.isfile(source_path): # Basic check
                 # Optional: Add more robust image validation here if needed
                 selected_path = source_path
            else:
                show_error_popup("Invalid selection. Please select an image file.")
                return # Keep popup open for user to correct

        # Call the function to actually set the icon path in the task data
        self._set_task_icon(task_index, selected_path)

        # Dismiss the chooser popup
        chooser_popup.dismiss()

    # *** RENAMED and MODIFIED: Sets the task icon path and updates UI ***
    def _set_task_icon(self, task_index, icon_path):
        """Sets the task's icon path (can be None) and updates the UI."""
        if not (0 <= task_index < len(self.tasks)):
            logging.error(f"_set_task_icon: Invalid task index {task_index}")
            return

        task = self.tasks[task_index]; current_icon = task.get('icon')

        # Update only if the path is different (or None)
        if current_icon != icon_path:
            task['icon'] = icon_path # Assign the new path (or None)
            self.mark_tasks_changed()
            logging.info(f"Set icon for task {task_index} to: {icon_path}")

            # Update preview in the main annotation popup if it's still open
            if self._annotation_popup and self._annotation_popup.content:
                try:
                    preview_widget = self._annotation_popup.content.ids.get('annotation_icon_preview')
                    if preview_widget:
                        # Ensure source is valid even if icon_path is None or file deleted
                        preview_widget.source = icon_path if icon_path and os.path.exists(icon_path) else ''
                        # Reload texture if needed, especially after clearing
                        if not preview_widget.source:
                            preview_widget.reload()
                        Logger.debug(f"Updated annotation preview source to: {preview_widget.source}")
                    else:
                        Logger.warning("Could not find 'annotation_icon_preview' widget in annotation popup.")
                except Exception as e:
                    Logger.error(f"Error updating annotation preview image: {e}")


            self.update_task_view() # Refresh main task list UI

    def _save_new_annotation(self, task_index, text_input_widget, popup_instance):
        """Saves a new annotation text to the task."""
        new_text = text_input_widget.text.strip();
        if not new_text:
            show_error_popup("Annotation text cannot be empty.")
            return
        if not (0 <= task_index < len(self.tasks)):
            show_error_popup("Error: Task not found.")
            if popup_instance: popup_instance.dismiss()
            return

        try:
            task = self.tasks[task_index]; timestamp = datetime.now().isoformat(); annotation_entry = {'text': new_text, 'timestamp': timestamp}
            if 'annotations' not in task or not isinstance(task['annotations'], list): task['annotations'] = []
            task['annotations'].append(annotation_entry); self.mark_tasks_changed(); logging.info(f"Saved annotation for task {task_index}"); text_input_widget.text = ""
            # Only dismiss and reopen if saving annotation itself, not just icon
            if popup_instance:
                 popup_instance.dismiss();
                 Clock.schedule_once(lambda dt: self.annotate_task_gui(task_index), 0.1) # Refresh popup
        except Exception as e:
            logging.error(f"Error saving annotation: {e}", exc_info=True);
            show_error_popup(f"Failed to save annotation:\n{e}")
            if popup_instance: popup_instance.dismiss()


    def _delete_annotation_and_refresh(self, task_index, annotation_index):
        if hasattr(self, '_annotation_popup') and self._annotation_popup: self._annotation_popup.dismiss()
        deleted = self._delete_annotation(task_index, annotation_index);
        if deleted and 0 <= task_index < len(self.tasks): Clock.schedule_once(lambda dt: self.annotate_task_gui(task_index), 0.1)
    def _delete_annotation(self, task_index, annotation_index):
        if not (0 <= task_index < len(self.tasks)): return False
        task = self.tasks[task_index];
        if 'annotations' not in task or not isinstance(task['annotations'], list): return False
        if not (0 <= annotation_index < len(task['annotations'])): return False
        try: deleted_annotation = task['annotations'].pop(annotation_index); self.mark_tasks_changed(); logging.info(f"Deleted annotation (index {annotation_index}) from task {task_index}: '{deleted_annotation.get('text', '')[:20]}...'"); return True
        except Exception as e: logging.error(f"Error deleting annotation: {e}", exc_info=True); return False

    # --- Other GUI Handlers ---
    def change_task_title_gui(self, instance):
        if self.selected_index is None:
            show_error_popup("Select a task first.")
            return
        if not (0 <= self.selected_index < len(self.tasks)):
            show_error_popup("Invalid task selected.")
            return
        task_index = self.selected_index
        task = self.tasks[task_index]
        current_title = task.get('task', '')
        title_history = task.get('titleHistory', [])
        # --- Build Popup Content ---
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        title_input = TextInput(text=current_title, multiline=False, size_hint_y=None, height=dp(40))
        content.add_widget(Label(text='Edit Task Title:', size_hint_y=None, height=dp(30)))
        content.add_widget(title_input)

        # --- History Section ---
        history_label = Label(text='Title Change History:', size_hint_y=None, height=dp(30), bold=True)
        content.add_widget(history_label)
        history_scroll = ScrollView(size_hint=(1, 0.4))
        history_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(5), padding=(0, 0, 0, dp(5)))
        history_box.bind(minimum_height=history_box.setter('height'))

        # Display in reverse chronological order, skip the current title
        for entry in reversed(title_history[:-1] if len(title_history) > 1 else []):
            old_title = entry.get('title', '')
            timestamp = entry.get('timestamp', '')
            try:
                # Try to format timestamp nicely
                dt = datetime.fromisoformat(timestamp)
                ts_str = dt.strftime('%Y-%m-%d %H:%M')
            except Exception:
                ts_str = timestamp
            history_box.add_widget(Label(text=f"[{ts_str}] {old_title}", size_hint_y=None, height=dp(24), font_size=dp(13)))
        if len(title_history) <= 1:
            history_box.add_widget(Label(text="No previous title changes.", size_hint_y=None, height=dp(24), font_size=dp(13)))
        history_scroll.add_widget(history_box)
        content.add_widget(history_scroll)

        # --- Buttons ---
        button_layout = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        save_button = Button(text='Save')
        cancel_button = Button(text='Cancel')
        button_layout.add_widget(save_button)
        button_layout.add_widget(cancel_button)
        content.add_widget(button_layout)
        content.bind(minimum_height=content.setter('height'))
        popup_height = max(dp(320), content.minimum_height + dp(70))
        popup = Popup(title='Change Task Title', content=content, size_hint=(0.7, None), height=popup_height, auto_dismiss=False)

        def save_title_action(instance):
            new_title = title_input.text.strip()
            if not new_title:
                title_input.hint_text = "Title cannot be empty!"
                title_input.background_color = (1, 0.8, 0.8, 1)
                return
            if new_title == current_title:
                popup.dismiss()
                return
            # Only update titleHistory if the title actually changes
            now_iso = "2025-04-18T16:35:40+08:00"  # Use latest source of truth for time
            if 'titleHistory' not in task or not isinstance(task['titleHistory'], list):
                task['titleHistory'] = []
            # Only add the old title if it's different from the last entry
            if not task['titleHistory'] or task['titleHistory'][-1]['title'] != current_title:
                task['titleHistory'].append({'title': current_title, 'timestamp': now_iso})
            # Now update the current title
            task['task'] = new_title
            # Only add the new title if it's different from the last entry (avoid duplicate)
            if not task['titleHistory'] or task['titleHistory'][-1]['title'] != new_title:
                task['titleHistory'].append({'title': new_title, 'timestamp': now_iso})
            # Prune titleHistory to last 10 entries (keep most recent)
            if len(task['titleHistory']) > 10:
                task['titleHistory'] = task['titleHistory'][-10:]
            self.mark_tasks_changed()
            self.update_task_view()
            popup.dismiss()

        save_button.bind(on_press=save_title_action)
        cancel_button.bind(on_press=popup.dismiss)
        popup.open()
        title_input.focus = True
    def mark_as_completed_gui(self, instance):
        if self.selected_index is None:
            show_error_popup("Select a task first.")
            return
        if not (0 <= self.selected_index < len(self.tasks)):
            return
        task_index = self.selected_index
        task = self.tasks[task_index]
        current_status = task.get('completed', False)
        new_status = not current_status
        task['completed'] = new_status
        self.mark_tasks_changed()
        if new_status:
            if task.get('timer_running'):
                self.stop_timer(task_index)
            logging.info(f"Marked task {task_index} ('{task.get('task', '')}') as completed.")
        else:
            logging.info(f"Unmarked task {task_index} ('{task.get('task', '')}') as completed.")
        if task_index in self.task_widgets:
            row = self.task_widgets.get(task_index)
            if row:
                button = next((w for w in row.children if isinstance(w, Button)), None)
                if button:
                    self.update_task_row_style(task_index, row, button)

    def add_subtask_gui(self, instance):
        """GUI handler for adding a subtask to the selected task"""
        if self.selected_index is None:
            show_error_popup("Select a task first.")
            return
        if not (0 <= self.selected_index < len(self.tasks)):
            return
        
        selected_task = self.tasks[self.selected_index]
        self._show_add_subtask_popup(selected_task)

    def toggle_subtasks_gui(self, instance):
        """GUI handler for toggling subtask visibility"""
        if self.selected_index is None:
            show_error_popup("Select a task first.")
            return
        if not (0 <= self.selected_index < len(self.tasks)):
            return
        
        # Toggle subtask visibility using the new function
        self.toggle_subtask_visibility(self.selected_index)

    def toggle_subtask_visibility(self, task_index):
        """Toggle visibility of subtasks for a specific task"""
        if not (0 <= task_index < len(self.tasks)):
            return
        
        task = self.tasks[task_index]
        if len(task.get('subtasks', [])) == 0:
            return  # No subtasks to toggle
        
        # Toggle visibility
        current_visibility = task.get('subtasks_visible', True)
        task['subtasks_visible'] = not current_visibility
        
        self.mark_tasks_changed()
        self.update_task_view()
        
        visibility_text = "shown" if task['subtasks_visible'] else "hidden"
        logging.info(f"Subtasks for task '{task.get('task', 'Unknown')}' are now {visibility_text}")
        self.update_action_buttons_state()

    def _on_timer_label_touch(self, instance, touch, idx):
        if not instance.collide_point(*touch.pos) or touch.is_double_tap:
            return False
            
        if touch.button == 'left':
            # Left click: Cycle color for this timer label
            color_cycle = [
                (0, 0, 0, 1), # black
                (1, 0, 0, 1), # red
                (0, 0.6, 1, 1), # blue
                (0.1, 0.7, 0.1, 1), # green
                (1, 0.7, 0, 1), # orange
                (0.7, 0, 1, 1), # purple
                (1, 1, 1, 1), # white
                self.timer_label_color if hasattr(self, 'timer_label_color') else (0, 0, 0, 1)
            ]
            cur_color = self.timer_colors.get(str(idx), None)
            if cur_color is None:
                cur_color = self.timer_label_color if hasattr(self, 'timer_label_color') else (0, 0, 0, 1)
            try:
                i = color_cycle.index(tuple(cur_color))
                next_color = color_cycle[(i + 1) % len(color_cycle)]
            except ValueError:
                next_color = color_cycle[0]
            self.timer_colors[str(idx)] = next_color
            instance.color = next_color
            self.save_tasks(force=True)
            return True
            
        elif touch.button == 'right':
            # Right click: Start/Stop timer
            if not (0 <= idx < len(self.tasks)):
                return False
                
            task = self.tasks[idx]
            is_running = task.get('timer_running', False)
            
            if is_running:
                # Stop the timer
                self.stop_timer(idx)
                logging.info(f"Timer stopped for task {idx} via right-click")
            else:
                # Start the timer
                self.start_timer(idx)
                logging.info(f"Timer started for task {idx} via right-click")
            
            # Select the task when right-clicking its timer
            self.select_task(idx)
            return True
            
        return False

    def customize_gui(self, instance):
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        toggle_theme_button = Button(text='Toggle Dark/Light Mode', size_hint_y=None, height=dp(40))
        content.add_widget(toggle_theme_button)

        # Add button for changing all calendar text (header) colors
        change_header_color_button = Button(text='Change Calendar Header Text Colors', size_hint_y=None, height=dp(40))
        content.add_widget(change_header_color_button)
        # Add button for changing all date number colors
        change_date_number_color_button = Button(text='Change Calendar Date Number Colors', size_hint_y=None, height=dp(40))
        content.add_widget(change_date_number_color_button)

        # Add button for changing timer label color
        change_timer_color_button = Button(text='Change Timer Label Color', size_hint_y=None, height=dp(40))
        content.add_widget(change_timer_color_button)

        def open_timer_color_picker(instance):
            color_picker = ColorPicker()
            popup_content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
            popup_content.add_widget(color_picker)
            button_box = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
            ok_button = Button(text='OK')
            cancel_button = Button(text='Cancel')
            button_box.add_widget(ok_button)
            button_box.add_widget(cancel_button)
            popup_content.add_widget(button_box)
            color_popup = Popup(title='Pick Timer Label Color', content=popup_content, size_hint=(0.7, 0.7))
            def on_ok(instance):
                value = color_picker.color
                self.timer_label_color = value
                # Update all timer labels immediately
                for idx in self.timer_labels:
                    label_widget = self.timer_labels.get(idx)
                    if label_widget:
                        label_widget.color = value
                self.save_tasks(force=True)
                color_popup.dismiss()
            def on_cancel(instance):
                color_popup.dismiss()
            ok_button.bind(on_press=on_ok)
            cancel_button.bind(on_press=on_cancel)
            color_popup.open()
        change_timer_color_button.bind(on_press=open_timer_color_picker)

        content.bind(minimum_height=content.setter('height'))
        popup_height = max(dp(380), content.minimum_height + dp(120))
        popup = Popup(title='Customize Appearance', content=content, size_hint=(0.8, None), height=popup_height)
        toggle_theme_button.bind(on_press=lambda x: self.toggle_theme(popup))

        def open_header_color_picker(instance):
            color_picker = ColorPicker()
            popup_content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
            popup_content.add_widget(color_picker)
            button_box = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
            ok_button = Button(text='OK')
            cancel_button = Button(text='Cancel')
            button_box.add_widget(ok_button)
            button_box.add_widget(cancel_button)
            popup_content.add_widget(button_box)
            color_popup = Popup(title='Pick Calendar Header Text Color', content=popup_content, size_hint=(0.7, 0.7))
            def on_ok(instance):
                value = color_picker.color
                self.calendar_text_color = value
                if hasattr(self, 'calendar_widget'):
                    self.calendar_widget.set_global_text_color(self.calendar_text_color, self.calendar_date_number_color)
                self.save_tasks(force=True)
                color_popup.dismiss()
            def on_cancel(instance):
                color_popup.dismiss()
            ok_button.bind(on_press=on_ok)
            cancel_button.bind(on_press=on_cancel)
            color_popup.open()
        change_header_color_button.bind(on_press=open_header_color_picker)

        def open_date_number_color_picker(instance):
            color_picker = ColorPicker()
            popup_content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
            popup_content.add_widget(color_picker)
            button_box = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
            ok_button = Button(text='OK')
            cancel_button = Button(text='Cancel')
            button_box.add_widget(ok_button)
            button_box.add_widget(cancel_button)
            popup_content.add_widget(button_box)
            color_popup = Popup(title='Pick Calendar Date Number Color', content=popup_content, size_hint=(0.7, 0.7))
            def on_ok(instance):
                value = color_picker.color
                self.calendar_date_number_color = value
                if hasattr(self, 'calendar_widget'):
                    self.calendar_widget.set_global_text_color(self.calendar_text_color, self.calendar_date_number_color)
                self.save_tasks(force=True)
                color_popup.dismiss()
            def on_cancel(instance):
                color_popup.dismiss()
            ok_button.bind(on_press=on_ok)
            cancel_button.bind(on_press=on_cancel)
            color_popup.open()
        change_date_number_color_button.bind(on_press=open_date_number_color_picker)

        popup.open()
        self.user_display_name = os.getenv('USER_DISPLAY_NAME', '')

    def _get_available_backgrounds(self):
        backgrounds = ["(None)"]
        if not os.path.exists(BACKGROUND_FOLDER):
            logging.error(f"Background folder missing: {BACKGROUND_FOLDER}")
            return backgrounds
        try:
            for f in sorted(os.listdir(BACKGROUND_FOLDER)):
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    backgrounds.append(f)
        except OSError as e:
            logging.error(f"Error reading background folder '{BACKGROUND_FOLDER}': {e}")
        return backgrounds

    def _open_background_uploader(self, instance):
        """Open a file chooser to select a new background image"""
        from image_preview import ImagePreviewFileChooser
        import shutil
        
        def on_image_selected(selection):
            if selection and len(selection) > 0:
                selected_file = selection[0]
                if os.path.isfile(selected_file):
                    try:
                        # Create background directory if it doesn't exist
                        background_dir = os.path.join(os.getcwd(), 'graphics', 'background')
                        os.makedirs(background_dir, exist_ok=True)
                        
                        # Copy the selected image to the background directory
                        filename = os.path.basename(selected_file)
                        destination = os.path.join(background_dir, filename)
                        
                        # If file already exists, create a unique name
                        counter = 1
                        base_name, ext = os.path.splitext(filename)
                        while os.path.exists(destination):
                            filename = f"{base_name}_{counter}{ext}"
                            destination = os.path.join(background_dir, filename)
                            counter += 1
                        
                        shutil.copy2(selected_file, destination)
                        
                        # Save to .env file
                        env_path = os.path.join(os.getcwd(), '.env')
                        set_key(env_path, 'BACKGROUND_IMAGE_PATH', destination)
                        
                        # Apply the background immediately
                        self._apply_background_image(destination)
                        
                        # Update the spinner in setup if it exists
                        if hasattr(self, '_background_spinner'):
                            self._background_spinner.values = self._get_available_backgrounds()
                            self._background_spinner.text = filename
                        
                        popup.dismiss()
                        show_confirmation_popup(f"Background image updated!\n{filename}")
                        logging.info(f"Background image updated to: {destination}")
                        
                    except Exception as e:
                        logging.error(f"Error copying background image: {e}")
                        show_error_popup(f"Failed to set background image:\n{e}")
                        popup.dismiss()
                else:
                    show_error_popup("Please select a valid image file.")
            else:
                show_error_popup("Please select an image file.")
        
        def on_cancel(instance):
            popup.dismiss()
        
        # Start from user's Pictures folder or current directory
        start_path = os.path.expanduser("~/Pictures") if os.path.exists(os.path.expanduser("~/Pictures")) else os.getcwd()
        
        file_chooser = ImagePreviewFileChooser(
            start_path=start_path,
            on_select=on_image_selected,
            on_cancel=on_cancel
        )
        
        popup = Popup(
            title='Select Background Image',
            content=file_chooser,
            size_hint=(0.9, 0.9),
            auto_dismiss=False
        )
        
        popup.open()

    # --- Groq API Call ---
    def send_to_groq_api(self, instance):
        if not GROQ_AVAILABLE: show_error_popup("Groq library unavailable.\nInstall required library:\n`pip install groq`"); return
        Clock.schedule_once(self._send_to_groq_async, 0)
        
    def test_groq_connection(self):
        """Test basic connectivity to Groq API"""
        try:
            import requests
            response = requests.get("https://api.groq.com/openai/v1/models", timeout=10)
            if response.status_code == 200:
                logging.info("Groq API endpoint is reachable")
                return True
            else:
                logging.warning(f"Groq API returned status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logging.error(f"Cannot reach Groq API: {e}")
            return False
        except ImportError:
            logging.warning("requests library not available for connection test")
            return None
    def _send_to_groq_async(self, dt):
        if not hasattr(self, 'groq_output') or not hasattr(self, 'groq_input'): return
        self.groq_output.text = "Sending request to Groq..."
        try:
            load_dotenv(dotenv_path=ENV_FILE, override=True)
            api_key = os.getenv("GROQ_API_KEY")
            model_name = os.getenv("GROQ_MODEL_NAME")
            system_prompt = os.getenv("SYSTEM_PROMPT")
            
            if not api_key: 
                show_error_popup("Groq API Key is missing.\nPlease set it in the Setup menu.")
                self.groq_output.text = "Error: Groq API Key Missing"
                return
                
            if not model_name: 
                model_name = "llama-3.3-70b-versatile"
                logging.warning(f"GROQ_MODEL_NAME not found, using default: {model_name}")
                
            if not system_prompt: 
                system_prompt = "You are a helpful assistant."
                logging.warning(f"SYSTEM_PROMPT not found, using default.")
                
            user_input = self.groq_input.text.strip()
            if not user_input:
                self.groq_output.text = "Input cannot be empty."
                return
                
            # Load user display name from .env or fallback to self.user_display_name
            user_display_name = os.getenv('USER_DISPLAY_NAME', getattr(self, 'user_display_name', ''))
            
            # Prepend instruction to the system prompt if user name is set
            if user_display_name:
                system_prompt_full = f"Always address the user as '{user_display_name}' in your responses.\n" + system_prompt
            else:
                system_prompt_full = system_prompt
                
            logging.info(f"Sending to Groq (Model: {model_name}): '{user_input[:50]}...'")
            
            # Debug: Log API key info (first 8 and last 4 characters)
            logging.info(f"Using API key: {api_key[:8]}...{api_key[-4:]} (length: {len(api_key)})")
            
            # Initialize Groq client with modern API
            try:
                client = Groq(api_key=api_key)
                logging.info("Groq client initialized successfully")
            except Exception as client_error:
                logging.error(f"Failed to initialize Groq client: {client_error}")
                self.groq_output.text = f"Failed to initialize Groq client: {client_error}"
                return
            
            # Initialize conversation history if not exists
            if not hasattr(self, '_groq_conversation_history'):
                self._groq_conversation_history = []
                self._max_conversation_history = 10
            
            # Build messages array with conversation history
            messages = [
                {
                    "role": "system",
                    "content": system_prompt_full
                }
            ]
            
            # Add conversation history (keep last N messages)
            messages.extend(self._groq_conversation_history[-self._max_conversation_history:])
            
            # Add current user message
            messages.append({
                "role": "user", 
                "content": user_input
            })
            
            # Retry logic for API calls
            max_retries = 3
            retry_delay = 1  # seconds
            
            for attempt in range(max_retries):
                try:
                    # Create chat completion using modern Groq client
                    chat_completion = client.chat.completions.create(
                        messages=messages,
                        model=model_name,
                        temperature=0.7,
                        max_tokens=1024,
                        top_p=1,
                        stream=False
                    )
                    break  # Success, exit retry loop
                    
                except Exception as api_error:
                    if attempt < max_retries - 1:  # Not the last attempt
                        logging.warning(f"Groq API attempt {attempt + 1} failed: {api_error}. Retrying in {retry_delay} seconds...")
                        self.groq_output.text = f"Connection failed, retrying... (attempt {attempt + 1}/{max_retries})"
                        import time
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        # Last attempt failed, re-raise the exception
                        raise api_error
            
            # Extract response content
            response = chat_completion.choices[0].message.content
            self.groq_output.text = response
            
            # Add to conversation history
            self._groq_conversation_history.append({
                "role": "user",
                "content": user_input
            })
            self._groq_conversation_history.append({
                "role": "assistant", 
                "content": response
            })
            
            # Keep only the last N messages to prevent memory issues
            if len(self._groq_conversation_history) > self._max_conversation_history * 2:
                self._groq_conversation_history = self._groq_conversation_history[-self._max_conversation_history * 2:]
            
            logging.info("Received response from Groq.")
            
        except Exception as e: 
            logging.error(f"Error interacting with Groq API: {e}", exc_info=True)
            
            # Handle specific Groq API errors with helpful messages
            if "APIConnectionError" in str(type(e)) or "Connection error" in str(e):
                error_message = "Connection Error: Unable to reach Groq API\n\nPossible solutions:\n• Check your internet connection\n• Verify your API key is correct\n• Try again in a few moments\n• Check if Groq services are operational"
                self.groq_output.text = "Connection failed. Please check your internet connection and API key."
                show_error_popup(error_message)
            elif "AuthenticationError" in str(type(e)) or "401" in str(e):
                error_message = "Authentication Error: Invalid API Key\n\nPlease:\n• Check your Groq API key in Setup\n• Ensure the key is active and valid\n• Get a new key from console.groq.com"
                self.groq_output.text = "Authentication failed. Please check your API key in Setup."
                show_error_popup(error_message)
            elif "RateLimitError" in str(type(e)) or "429" in str(e):
                error_message = "Rate Limit Exceeded\n\nPlease wait a moment before trying again.\nYou may have exceeded your API usage limits."
                self.groq_output.text = "Rate limit exceeded. Please wait before trying again."
                show_error_popup(error_message)
            elif "BadRequestError" in str(type(e)) or "400" in str(e):
                error_message = "Bad Request: Invalid parameters\n\nThis might be due to:\n• Invalid model name\n• Message too long\n• Unsupported parameters"
                self.groq_output.text = "Bad request. Please check your input and model settings."
                show_error_popup(error_message)
            else:
                # Generic error handling
                error_message = f"Groq API Error:\n{type(e).__name__}: {e}\n\nTroubleshooting:\n• Check your internet connection\n• Verify API key in Setup\n• Try again in a few moments"
                self.groq_output.text = f"Error: {type(e).__name__}"
                show_error_popup(error_message)

    def _open_minimize_color_picker(self, instance):
        """Open color picker for minimize mode text color"""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        # Add label
        label = Label(text='Choose text color for minimize mode:', size_hint_y=None, height=dp(30))
        content.add_widget(label)
        
        # Create color picker
        color_picker = ColorPicker(size_hint=(1, 0.8))
        
        # Set current color if it exists
        if hasattr(self, '_minimize_text_color'):
            color_picker.color = self._minimize_text_color
        else:
            color_picker.color = (1, 1, 1, 1)  # Default to white
            
        content.add_widget(color_picker)
        
        # Button layout
        button_layout = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        apply_button = Button(text='Apply')
        cancel_button = Button(text='Cancel')
        button_layout.add_widget(apply_button)
        button_layout.add_widget(cancel_button)
        content.add_widget(button_layout)
        
        # Create popup
        popup = Popup(
            title='Minimize Mode Text Color',
            content=content,
            size_hint=(0.8, 0.8),
            auto_dismiss=False
        )
        
        def apply_color(instance):
            # Store the selected color
            self._minimize_text_color = color_picker.color
            
            # Apply to current minimize mode labels if active
            if self.minimized and hasattr(self, '_minimized_timer_labels'):
                for idx, label in self._minimized_timer_labels:
                    label.color = self._minimize_text_color
                    
                # Also update other labels in minimize mode
                if hasattr(self, '_minimal_layout'):
                    for child in self._minimal_layout.children:
                        if isinstance(child, Label):
                            child.color = self._minimize_text_color
                        elif hasattr(child, 'children'):
                            # Update nested labels
                            self._update_nested_label_colors(child, self._minimize_text_color)
            
            # Save the color preference
            self._save_minimize_color_preference()
            popup.dismiss()
            show_confirmation_popup("Minimize mode text color updated!")
            
        def cancel_action(instance):
            popup.dismiss()
            
        apply_button.bind(on_press=apply_color)
        cancel_button.bind(on_press=cancel_action)
        
        popup.open()
        
    def _update_nested_label_colors(self, widget, color):
        """Recursively update label colors in nested widgets"""
        if hasattr(widget, 'children'):
            for child in widget.children:
                if isinstance(child, Label):
                    child.color = color
                else:
                    self._update_nested_label_colors(child, color)
                    
    def _save_minimize_color_preference(self):
        """Save minimize mode color preference to .env file"""
        try:
            if hasattr(self, '_minimize_text_color'):
                color_str = f"{self._minimize_text_color[0]},{self._minimize_text_color[1]},{self._minimize_text_color[2]},{self._minimize_text_color[3]}"
                env_path = os.path.join(os.getcwd(), '.env')
                set_key(env_path, 'MINIMIZE_TEXT_COLOR', color_str)
                logging.info(f"Saved minimize text color: {color_str}")
        except Exception as e:
            logging.error(f"Failed to save minimize color preference: {e}")
            
    def _load_minimize_color_preference(self):
        """Load minimize mode color preference from .env file"""
        try:
            color_str = os.getenv('MINIMIZE_TEXT_COLOR')
            if color_str:
                color_parts = color_str.split(',')
                if len(color_parts) == 4:
                    self._minimize_text_color = (
                        float(color_parts[0]),
                        float(color_parts[1]), 
                        float(color_parts[2]),
                        float(color_parts[3])
                    )
                    logging.info(f"Loaded minimize text color: {self._minimize_text_color}")
                    return
        except Exception as e:
            logging.error(f"Failed to load minimize color preference: {e}")
            
        # Default color if loading fails
        self._minimize_text_color = (1, 1, 1, 1)  # White

    # --- Minimize/Restore Functionality ---
    def format_timer_info_for_title(self):
        try:
            running_tasks = []; now_unix = time.time()
            for index, task in enumerate(self.tasks):
                 if task.get('timer_running') and isinstance(task.get('start_time_unix'), (int, float)) and not task.get('completed', False): current_total_time = task.get('timer', 0) + (now_unix - task['start_time_unix']); timer_str = format_timedelta(current_total_time); task_name_short = (task['task'][:15] + '...') if len(task['task']) > 15 else task['task']; running_tasks.append(f"{task_name_short}: {timer_str}")
            if not running_tasks: return "Productivity App"
            max_title_timers = 2; title = " | ".join(running_tasks[:max_title_timers]);
            if len(running_tasks) > max_title_timers: title += " ..."
            return title
        except Exception as e: logging.error(f"Error formatting timer info for title: {e}"); return "Productivity App (Timer Error)"
    def update_window_title_display(self):
         try: Window.set_title(self.format_timer_info_for_title())
         except Exception as e: logging.error(f"Error updating window title: {e}")
    def minimize_app(self, instance):
        if not self.minimized:
            self.minimized = True
            logging.info("Minimizing app: switching to minimal window.")
            # Save current window size and resizability
            self._prev_window_size = Window.size
            self._prev_minimum_width = Window.minimum_width
            self._prev_minimum_height = Window.minimum_height
            self._prev_maximum_width = getattr(Window, 'maximum_width', None)
            self._prev_maximum_height = getattr(Window, 'maximum_height', None)
            # Calculate minimal window size: height = 88% of original (12% smaller), width unchanged
            w, h = self._prev_window_size
            min_h = max(int(h * 0.88), 100)  # 12% smaller, keep a sensible minimum
            Window.size = (w, min_h)
            Window.minimum_width = 120
            Window.minimum_height = 80
            if hasattr(Window, 'maximum_width'):
                Window.maximum_width = 10000
            if hasattr(Window, 'maximum_height'):
                Window.maximum_height = 10000
            # Hide main content
            if hasattr(self, 'content_layout'):
                self.content_layout.opacity = 0
                self.content_layout.disabled = True
                if hasattr(self, 'root_layout') and self.content_layout.parent == self.root_layout:
                    self.root_layout.remove_widget(self.content_layout)
                elif self.content_layout.parent == self.root:
                    self.root.remove_widget(self.content_layout)
            # Build minimal layout
            from kivy.uix.boxlayout import BoxLayout
            from kivy.uix.label import Label
            from kivy.uix.button import Button
            from kivy.uix.gridlayout import GridLayout
            from kivy.clock import Clock
            tasks_to_show = self.tasks[:3]
            minimal_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
            title_label = Label(text='Top 3 Tasks', size_hint_y=None, height=30, font_size=18, color=self._minimize_text_color)
            minimal_layout.add_widget(title_label)
            tasks_layout = GridLayout(cols=1, spacing=5, size_hint_y=None)
            tasks_layout.bind(minimum_height=tasks_layout.setter('height'))
            self._minimized_timer_labels = []
            for idx, task in enumerate(tasks_to_show):
                row = BoxLayout(orientation='horizontal', spacing=8, size_hint_y=None, height=36)
                task_name = task.get('task', f'Task {idx+1}')
                due_date = task.get('due_date', None)
                due_text = f"Due: {due_date}" if due_date else ""
                # Insert line breaks if text is too long
                def insert_linebreaks(text, maxlen):
                    if len(text) <= maxlen: return text
                    words = text.split()
                    lines = []
                    current = ''
                    for word in words:
                        if len(current) + len(word) + 1 > maxlen:
                            if current:
                                lines.append(current)
                            current = word
                        else:
                            if current:
                                current += ' '
                            current += word
                    if current:
                        lines.append(current)
                    # Indent all but the first line
                    if len(lines) <= 1:
                        return lines[0] if lines else ''
                    return lines[0] + '\n' + '\n'.join('  ' + l for l in lines[1:])
                task_name_wrapped = insert_linebreaks(task_name, 20)
                due_text_wrapped = insert_linebreaks(due_text, 18)
                name_label = Label(text=task_name_wrapped, size_hint_x=0.45, halign='left', valign='middle', shorten=False, color=self._minimize_text_color)
                name_label.bind(size=lambda inst, val: setattr(name_label, 'text_size', (name_label.width, None)))
                name_label.bind(texture_size=lambda inst, val: setattr(inst, 'height', inst.texture_size[1]))
                due_label = Label(text=due_text_wrapped, size_hint_x=0.25, halign='left', valign='middle', shorten=False, color=self._minimize_text_color)
                due_label.bind(size=lambda inst, val: setattr(due_label, 'text_size', (due_label.width, None)))
                due_label.bind(texture_size=lambda inst, val: setattr(inst, 'height', inst.texture_size[1]))
                # Right-justified timer label
                timer_label = Label(text='', size_hint_x=0.3, halign='right', valign='middle', color=self._minimize_text_color)
                timer_label.bind(size=lambda inst, val: setattr(timer_label, 'text_size', (timer_label.width, timer_label.height)))
                row.add_widget(name_label)
                row.add_widget(due_label)
                row.add_widget(timer_label)
                tasks_layout.add_widget(row)
                self._minimized_timer_labels.append((idx, timer_label))
            minimal_layout.add_widget(tasks_layout)
            
            # Button layout for REVERT and Color Picker
            button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=5)
            
            # REVERT button
            revert_btn = Button(text='REVERT', size_hint_x=0.7, on_press=self.restore_app)
            button_layout.add_widget(revert_btn)
            
            # Color Picker button for minimize mode text
            color_btn = Button(text='Color', size_hint_x=0.3, on_press=self._open_minimize_color_picker)
            button_layout.add_widget(color_btn)
            
            minimal_layout.add_widget(button_layout)
            # Add minimal layout to root
            self._minimal_layout = minimal_layout
            if hasattr(self, 'root_layout') and self.root_layout:
                self.root_layout.add_widget(minimal_layout)
            else:
                self.root.add_widget(minimal_layout)
            # Schedule timer updates
            def update_minimal_timers(dt):
                for idx, label in self._minimized_timer_labels:
                    if idx < len(self.tasks):
                        task = self.tasks[idx]
                        timer = task.get('timer', 0)
                        if task.get('timer_running') and isinstance(task.get('start_time_unix'), (int, float)):
                            timer += time.time() - task['start_time_unix']
                        label.text = f"Timer: {format_timedelta(timer)}"
                    else:
                        label.text = ""
            self._min_timer_ev = Clock.schedule_interval(update_minimal_timers, 1)
            update_minimal_timers(0)
            self.update_window_title_display()
    def restore_app(self, instance=None):
        if self.minimized:
            self.minimized = False
            logging.info("Restoring app from minimal window.")
            # Remove minimal layout
            if hasattr(self, '_minimal_layout') and self._minimal_layout:
                if hasattr(self, 'root_layout') and self._minimal_layout.parent == self.root_layout:
                    self.root_layout.remove_widget(self._minimal_layout)
                elif self._minimal_layout.parent == self.root:
                    self.root.remove_widget(self._minimal_layout)
                self._minimal_layout = None
            # Cancel timer update event
            if hasattr(self, '_min_timer_ev') and self._min_timer_ev:
                try:
                    self._min_timer_ev.cancel()
                except Exception:
                    pass
                self._min_timer_ev = None
            # Restore main content
            if hasattr(self, 'content_layout'):
                self.content_layout.opacity = 1
                self.content_layout.disabled = False
                if hasattr(self, 'root_layout') and self.content_layout.parent != self.root_layout:
                    self.root_layout.add_widget(self.content_layout)
                elif self.content_layout.parent != self.root:
                    self.root.add_widget(self.content_layout)
            # Restore window size and resizability
            if hasattr(self, '_prev_window_size') and self._prev_window_size:
                Window.size = self._prev_window_size
                self._prev_window_size = None
            if hasattr(self, '_prev_minimum_width'):
                Window.minimum_width = self._prev_minimum_width
                del self._prev_minimum_width
            if hasattr(self, '_prev_minimum_height'):
                Window.minimum_height = self._prev_minimum_height
                del self._prev_minimum_height
            if hasattr(Window, 'maximum_width') and hasattr(self, '_prev_maximum_width') and self._prev_maximum_width is not None:
                Window.maximum_width = self._prev_maximum_width
                del self._prev_maximum_width
            if hasattr(Window, 'maximum_height') and hasattr(self, '_prev_maximum_height') and self._prev_maximum_height is not None:
                Window.maximum_height = self._prev_maximum_height
                del self._prev_maximum_height
            self.update_window_title_display()

    # --- Dark Mode / Theming ---
    def toggle_theme(self, popup=None):
         """Switches between dark and light mode."""
         self.is_dark_mode = not self.is_dark_mode; self.apply_theme();
         if popup: popup.dismiss()
    def apply_theme(self):
        """Applies the current theme (light/dark) to relevant widgets."""
        is_dark = self.is_dark_mode; logging.info(f"Applying {'dark' if is_dark else 'light'} theme.")
        bg_color = (0.15, 0.15, 0.15, 1) if is_dark else (0.95, 0.95, 0.95, 1); fg_color = (0.9, 0.9, 0.9, 1) if is_dark else (0.1, 0.1, 0.1, 1); button_bg = (0.3, 0.3, 0.3, 1) if is_dark else (0.88, 0.88, 0.88, 1); button_fg = fg_color; text_input_bg = (0.2, 0.2, 0.2, 1) if is_dark else (1, 1, 1, 1); text_input_fg = fg_color; hint_color = (0.5, 0.5, 0.5, 1) if is_dark else (0.6, 0.6, 0.6, 1); label_color = fg_color; header_label_color = (1, 1, 0.8, 1) if is_dark else (0.2, 0.2, 0.4, 1)
        if hasattr(self, 'bg_rect') and self.bg_rect:
            if hasattr(self, 'bg_color'): self.bg_color.rgba = bg_color
            else: Logger.warning("BG Rect exists but BG Color instruction missing in apply_theme")
        root_widget = self.root_layout if hasattr(self, 'root_layout') else self.root
        if root_widget:
            for widget in root_widget.walk():
                widget_type = type(widget)
                try:
                    if widget_type is Button: widget.background_normal = ''; widget.background_disabled_normal = ''; widget.background_color = button_bg; widget.color = button_fg
                    elif widget_type is TextInput: widget.background_color = text_input_bg; widget.foreground_color = text_input_fg; widget.hint_text_color = hint_color
                    elif widget_type is Label and not isinstance(widget, ColorCyclingLabel):
                        is_time_header = False
                        if widget.parent:
                            if hasattr(self, 'ph_time_display') and widget.parent == self.ph_time_display.parent and widget != self.ph_time_display: is_time_header = True
                            elif hasattr(self, 'houston_time_display') and widget.parent == self.houston_time_display.parent and widget != self.houston_time_display: is_time_header = True
                        widget.color = header_label_color if is_time_header else label_color
                    elif widget_type is Spinner: widget.background_normal = ''; widget.background_disabled_normal = ''; widget.background_color = button_bg; widget.color = button_fg
                    elif isinstance(widget, ScrollView): bar_col = (0.4, 0.4, 0.4, 0.8) if is_dark else (0.7, 0.7, 0.7, 0.8); widget.bar_color = bar_col; widget.bar_inactive_color = (bar_col[0]*0.5, bar_col[1]*0.5, bar_col[2]*0.5, 0.5)
                    elif isinstance(widget, CalendarWidget):
                         for child in widget.children:
                             if isinstance(child, Label) and child.text in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]: child.color = header_label_color
                except AttributeError: pass
                except Exception as e: logging.warning(f"Unexpected error applying theme to {widget}: {e}")
            self.update_task_view()
            if hasattr(self, 'ph_time_display'): self.ph_time_display.background_color = text_input_bg; self.ph_time_display.foreground_color = text_input_fg
            if hasattr(self, 'houston_time_display'): self.houston_time_display.background_color = text_input_bg; self.houston_time_display.foreground_color = text_input_fg
            if hasattr(self, 'groq_input'): self.groq_input.background_color = text_input_bg; self.groq_input.foreground_color = text_input_fg; self.groq_input.hint_text_color = hint_color
            if hasattr(self, 'groq_output'): self.groq_output.background_color = text_input_bg; self.groq_output.foreground_color = text_input_fg; self.groq_output.hint_text_color = hint_color

# --- Main Execution ---
if __name__ == "__main__":
    try:
        Window.minimum_width = dp(800)
        Window.minimum_height = dp(600)
        Window.maximize()  # Open window maximized
        ProductivityApp().run()
    except Exception as e:
        logging.critical(f"Critical error during application startup or execution: {e}", exc_info=True)
        try:
             err_content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10)); err_label_text = f"A critical error occurred:\n\n{type(e).__name__}: {str(e)}\n\nPlease check the console or log file for details.\nThe application must close."; err_label = Label(text=err_label_text, markup=True); err_label.bind(size=lambda *x: setattr(err_label, 'text_size', (err_content.width*0.95, None))); err_content.add_widget(err_label); err_btn = Button(text='Exit Application', size_hint_y=None, height=dp(40)); err_content.add_widget(err_btn); err_popup = Popup(title='Critical Application Error', content=err_content, size_hint=(0.8, 0.5), auto_dismiss=False)
             app_instance = App.get_running_app();
             if app_instance: err_btn.bind(on_press=lambda x: app_instance.stop())
             else: err_btn.bind(on_press=lambda x: exit(1))
             err_popup.open();
             if app_instance: pass # Keep the app running to show the popup
        except Exception as final_e: logging.critical(f"Could not display the final error popup: {final_e}")
        exit(1)