# this is needed for supporting Windows 10 with OpenGL < v2.0
# Example: VirtualBox w/ OpenGL v1.1
import platform, os
if platform.system() == 'Windows':
    os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'
import win32timezone
import json
import mimetypes
import os
import random
from kivy.uix.image import AsyncImage
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivymd.app import MDApp
from kivymd.uix.menu import MDDropdownMenu
from kivymd.theming import ThemableBehavior
from kivymd.uix.behaviors import RectangularElevationBehavior
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.uix.modalview import ModalView
from kivymd.uix.snackbar import Snackbar
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ListProperty, ConfigParserProperty, StringProperty, ObjectProperty, NumericProperty
from kivy.config import ConfigParser
from os.path import isdir, exists, join, expanduser
from os import listdir
from distutils import dir_util
from shutil import copy2
from kivy.tools.packaging.pyinstaller_hooks import get_deps_minimal, get_deps_all, hookspath, runtime_hooks
home_directory = expanduser("~").replace("\\", "/")
config = ConfigParser()
config.read("labelbox.ini")

Builder.load_string("""
#:import colors kivymd.color_definitions.colors
#:import get_color_from_hex kivy.utils.get_color_from_hex
<FileManager>:
    FloatLayout:
        FileChooserIconView:
            id: customfilechooser
            dirselect: True
            rootpath: {}
        AnchorLayout:
            anchor_x: 'right'
            anchor_y: 'bottom'
            size_hint_y: None
            height: dp(56)
            padding: dp(10)
            MDFloatingActionButton:
                id: floatingbutton
                size_hint: None, None
                size:dp(56), dp(56)
                icon: "check"
                opposite_colors: True
                elevation: dp(8)
                on_release: root.callback(args[0])
                md_bg_color: get_color_from_hex(colors["Blue"]["500"])
""".format(repr(home_directory)))


class FileManager(ModalView):
    # callback to bind on floating button
    callback = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


Builder.load_string('''
#:import colors kivymd.color_definitions.colors
#:import get_color_from_hex kivy.utils.get_color_from_hex
<CustomToolbar>:
    padding: "5dp"
    spacing: "12dp"
    MDIconButton:
        id: button_1
        icon: "gra.png"
        pos_hint: {"center_y": .5}
        #theme_text_color: "Primary"
        user_font_size: "18sp"

    MDLabel:
        text: "Box Label"
        pos_hint: {"center_y": .5}
        size_hint_x: None
        width: self.texture_size[0]
        text_size: None, None
        font_style: 'H6'
        theme_text_color: "Primary"
        
    Widget:
    
    MDIconButton:
        id: button_2
        icon: "dots-vertical"
        pos_hint: {"center_y": .5}
        on_release: root.parent.menu.open()


<MainPage>:
    name: "mainScreen"
    CustomToolbar:
        id: toolbar
        elevation: 10
        pos_hint: {"top": 1}
        size_hint_y: .08
    GridLayout:
	    id: gridlayout
		cols: 4
		rows: 1
		pos_hint:{"top": .9}
		spacing: dp(10)
		padding: dp(10)
		
    MDFloatingActionButtonSpeedDial:
        id: speeddial
        data: {"plus": "Positive", "minus": "Negative", "alert-circle-outline": "Suspicious"}
        rotation_root_button: False
        callback: root.callback
        hint_animation: True
        #bg_hint_color: app.theme_cls.primary_light
        
    
    BoxLayout:
        pos_hint: {"center_x": .42, "y": 0}
        height: dp(56)
        size_hint_y: None
        size_hint: None, None
        size:dp(65), dp(56)
        padding: dp(10)
        MDIconButton:
            icon: "skip-backward-outline"
            pos_hint: {"center_x": .5, "center_y": .5}
            on_release: root.backward()
        MDLabel:
            id: buttom_label
            text: f"{root.position}/{root.length}"
            pos_hint: {"center_x": .5, "center_y": .5}
            size_hint_x: None
            #width: self.texture_size[0]
            text_size: None, None
            # font_style: 'H6'
            halighn: "center"
            theme_text_color: "Primary"

        MDIconButton:
            id: forward
            icon: "skip-forward-outline"
            pos_hint: {"center_y": .5}
            on_release: root.forward()
            
<AddSamples>:
    current_selected_directory: open_folder.secondary_text
    current_destination_directory: destnation_folder.secondary_text
    BoxLayout:
        pos_hint: {"top": 1.0, }
        size_hint: 1, 0.1
        MDIconButton:
            icon:"arrow-left"
            on_release: root.callback()
        MDLabel: 
            text: "Add Samples"
            theme_text_color: "Primary"
            size_hint: 0.8, 1
    ScrollView:
        pos_hint: {"top": .9}
        MDList:
            TwoLineIconListItem:
                id: open_folder
                text: "Upload Directory"
                secondary_text: root.current_selected_directory
                on_release: root.choose_item(args[0])
                IconLeftWidget:
                    icon: "folder-plus-outline"
            TwoLineIconListItem:
                id: destnation_folder
                text: "Destination Directory"
                on_release: root.choose_item(args[0])
                secondary_text: root.current_destination_directory
                IconLeftWidget:
                    icon: "folder-outline"
                                    		
''')


class MainPage(Screen):
    position = ConfigParserProperty(defaultvalue=0, section="Progress", key="position",
                                    config=config, val_type=int)
    json_file = ConfigParserProperty(defaultvalue="", section="Progress", key="json_file",
                                     config=None)
    length = NumericProperty(0)
    previous_position = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.directory_names = []
        menu_items = [{"text": i} for i in ["Add Samples", "Light theme", "Dark theme"]]
        self.menu = MDDropdownMenu(caller=self.ids.toolbar.ids.button_2, items=menu_items, width_mult=5,
                                   position="bottom", callback=self.Add_file,
                                   background_color=MDApp.get_running_app().theme_cls.bg_normal)

    def callback(self, instance):
        self.ids.speeddial.close_stack()
        print(instance.icon)
        mapping = {"plus": "Positive", "minus": "Negative", "alert-circle-outline": "Suspicious"}
        destination_folder = config.get("Destination Directory", "path")
        if destination_folder:
            dir_util.mkpath(join(destination_folder, mapping[instance.icon]))
            for widget in list(self.ids.gridlayout.children):
                print(widget.source, destination_folder)
                copy2(widget.source, join(destination_folder, mapping[instance.icon]))
            self.ids.gridlayout.clear_widgets()
            self.forward()
        else:
            Snackbar(text="Please set destination directory...").show()

    def Add_file(self, instance):
        if instance.text == "Add Samples":
            transition = sm.transition
            transition.direction = "left"
            sm.current = "Add_samples"
        else:
            if instance.text == "Dark theme":
                config.set("Theme Style", "theme", "Dark")
            else:
                config.set("Theme Style", "theme", "Light")
            config.update()
            config.write()
            Snackbar(text="Restart the BoxLabel that change to take effect").show()

    def forward(self):
        self.previous_position = self.position
        if self.position + 1 < self.length:
            config.set("Progress", "position", self.position + 1)
            config.write()


    def backward(self):
        self.previous_position = self.position
        if self.position > 0:
            config.set("Progress", "position", self.position - 1)
            config.write()


    def on_position(self, instance, value):
        print(self.previous_position, value)
        self.ids.buttom_label.text = f"{value}/{self.length - 1 if self.length > 0 else self.length}"
        if self.previous_position is not None:
            if value > self.previous_position:
                self.ids.gridlayout.clear_widgets()
                self.add_images()
            elif value < self.previous_position:
                self.ids.gridlayout.clear_widgets()
                self.add_images()

    def on_json_file(self, instance, value):
        self.directory_names = json.load(open(value))
        self.length = len(self.directory_names)
        self.ids.buttom_label.text = f"{self.position}/{self.length - 1 if self.length > 0 else self.length}"
        # add images on grid layout
        self.add_images()

    def add_images(self):
        if self.directory_names:
            subfiles = listdir(self.directory_names[self.position])
            for image_file in subfiles:
                mime_type, encoding = mimetypes.guess_type(image_file)
                if mime_type is None:
                    continue
                else:
                    main, sub = mime_type.split("/")
                    if main == "image":
                        image_widget = AsyncImage(source=join(self.directory_names[self.position], image_file))
                        self.ids.gridlayout.add_widget(image_widget)


class CustomToolbar(
    ThemableBehavior, RectangularElevationBehavior, MDBoxLayout,
):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = self.theme_cls.bg_light if MDApp.get_running_app().theme_cls.theme_style == "Dark" else self.theme_cls.primary_color


class AddSamples(FloatLayout):
    current_selected_directory = ConfigParserProperty("", "Project Directory", "path", None)
    current_destination_directory = ConfigParserProperty(defaultvalue="", section="Destination Directory", key="path",
                                                         config=None)
    item_pressed = ObjectProperty()
    _current_selected_directory_ = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.filemanager = FileManager(callback=self.on_closing)
        self.filemanager.ids.customfilechooser.bind(selection=self.on_select)

    def on_select(self, instance, value):

        if len(value) != 0:
            if isdir(value[0]):
                print(value)
                self._current_selected_directory_ = value[0]
            else:
                self._current_selected_directory_ = ""

    def choose_item(self, instance):
        self.item_pressed = instance
        self.filemanager.open()

    def on_closing(self, instance):
        if self._current_selected_directory_ != "" and os.access(self._current_selected_directory_, os.R_OK | os.W_OK):
            if self.item_pressed.text == "Upload Directory":
                self.ids.open_folder.secondary_text = self._current_selected_directory_
                print(self.current_selected_directory)
                #self.ids.destnation_folder.secondary_text = self._current_selected_directory_ if self.ids.destnation_folder.secondary_text == "" else self.ids.destnation_folder.secondary_text
                config.set("Progress", "position", 0)
                config.write()

                dirctorynames = [join(self._current_selected_directory_, directory) for directory in
                                 listdir(self._current_selected_directory_) if
                                 isdir(join(self._current_selected_directory_, directory))]
                file_name = "".join(random.sample('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', 20))
                json.dump(dirctorynames, open(f"{file_name}.json", "w"))
                old_file = config.get("Progress", "json_file")
                if exists(old_file):
                    print(old_file)
                    os.remove(old_file)
                config.set("Progress", "json_file", f"{file_name}.json")
                config.write()

            else:
                self.ids.destnation_folder.secondary_text = self._current_selected_directory_

        self.filemanager.dismiss()

    def callback(self):
        transition = sm.transition
        transition.direction = "right"
        sm.current = "mainScreen"

    def on_current_selected_directory(self, instance, value):
        pass


sm = ScreenManager()
config.setdefaults("Progress", {"json_file": "", "position": 0})
config.adddefaultsection("Theme Style")
config.adddefaultsection("Destination Directory")
config.setdefault("Theme Style", "theme", "Dark")
config.setdefault("Destination Directory", "path", "")
config.write()


class Test(MDApp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls.theme_style = config.get("Theme Style", "theme")

    def on_config_change(self, config_, section, key, value):
        if config_ is self.config:
            query = (section, key)
            if query == ("Theme Style", "theme"):
                self.theme_cls.theme_style = value
            elif query == ("Project Directory", "path"):
                pass
                # self.filenames = [directory for directory in listdir(value) if isdir(directory)]

    def build(self):
        main_page = MainPage()
        main_page.property('json_file').set_config(config)
        sm.add_widget(main_page)
        widget = AddSamples()
        widget.property('current_selected_directory').set_config(config)
        widget.property('current_destination_directory').set_config(config)
        add_sammples = Screen(name="Add_samples")
        add_sammples.add_widget(widget)
        sm.add_widget(add_sammples)
        return sm


if __name__ == '__main__':
    Test().run()



