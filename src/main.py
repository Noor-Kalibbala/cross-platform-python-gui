# this is needed for supporting Windows 10 with OpenGL < v2.0
# Example: VirtualBox w/ OpenGL v1.1
import platform, os
if platform.system() == 'Windows':
    os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

import json
import mimetypes
import os
import random
import win32timezone
from random import randint
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivymd.app import MDApp
from kivymd.uix.menu import MDDropdownMenu
from kivy.uix.modalview import ModalView
from kivymd.uix.snackbar import Snackbar
from kivy.uix.scatter import Scatter
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ListProperty, ConfigParserProperty, StringProperty, ObjectProperty, NumericProperty
from kivy.config import ConfigParser
from os.path import isdir, exists, join
from os import listdir
from distutils import dir_util
from shutil import copy2

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
""")


class FileManager(ModalView):
    # callback to bind on floating button
    callback = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


Builder.load_string('''
#:kivy 1.0
#:import kivy kivy
#:import win kivy.core.window
#:import colors kivymd.color_definitions.colors
#:import get_color_from_hex kivy.utils.get_color_from_hex

<Picture>:
    # each time a picture is created, the image can delay the loading
    # as soon as the image is loaded, ensure that the center is changed
    # to the center of the screen.
    #on_size: self.center = win.Window.center
    size: image.size
    size_hint: None, None
    Image:
        id: image
        source: root.source

        # create initial image to be 400 pixels width
        size: 300, 300 / self.image_ratio
        # add shadow background
        canvas.before:
            Color:
                rgba: 1,1,1,1
            BorderImage:
                source: 'shadow32.png'
                border: (36,36,36,36)
                size:(self.width+72, self.height+72)
                pos: (-36,-36)


<MainPage>:
    name: "mainScreen"
    canvas:
        Color:
            rgb: 1, 1, 1
        Rectangle:
            source: 'background.jpg'
            size: self.size

    BoxLayout:
        padding: 10
        spacing: 10
        size_hint: 1, None
        pos_hint: {'top': 1}
        height: 44
        Image:
            size_hint: None, None
            size: 24, 24
            source: 'gra.png'
        Label:
            height: 24
            text_size: self.width, None
            color: (1, 1, 1, .8)
            text: 'Label Box 1.0.0' 
        Widget:
    
        MDIconButton:
            id: button_2
            icon: "dots-vertical"
            pos_hint: {"center_y": .5}
            on_release: root.menu.open()

    MDFloatingActionButtonSpeedDial:
        id: speeddial
        data: {"plus": "Positive", "minus": "Negative"}
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


class Picture(Scatter):
    '''Picture is the class that will show the image with a white border and a
    shadow. They are nothing here because almost everything is inside the
    picture.kv. Check the rule named <Picture> inside the file, and you'll see
    how the Picture() is really constructed and used.

    The source property will be the filename to show.
    '''

    source = StringProperty(None)


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
        menu_items = [{"text": i} for i in ["Add Samples"]]
        self.menu = MDDropdownMenu(caller=self.ids.button_2, items=menu_items, width_mult=5,
                                   position="bottom", use_icon_item=False, callback=self.Add_file,
                                   background_color=MDApp.get_running_app().theme_cls.bg_normal)

    def callback(self, instance):
        self.ids.speeddial.close_stack()
        print(instance.icon)
        mapping = {"plus": "Positive", "minus": "Negative"}
        destination_folder = config.get("Destination Directory", "path")
        if destination_folder:
            dir_util.mkpath(join(destination_folder, mapping[instance.icon]))
            for widget in list(self.children):
                if isinstance(widget, Picture):
                    print(widget.source, destination_folder)
                    copy2(widget.source, join(destination_folder, mapping[instance.icon]))
            self.clear_pictures()
            self.forward()
        else:
            Snackbar(text="Please set destination directory...").show()

    def Add_file(self, instance):
        if instance.text == "Add Samples":
            transition = sm.transition
            transition.direction = "left"
            sm.current = "Add_samples"
        # else:
        #     if instance.text == "Dark theme":
        #         config.set("Theme Style", "theme", "Dark")
        #     else:
        #         config.set("Theme Style", "theme", "Light")
        #     config.update()
        #     config.write()
        #     Snackbar(text="Restart the BoxLabel that change to take effect").show()

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
                self.clear_pictures()
                self.add_images()
            elif value < self.previous_position:
                self.clear_pictures()
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
                        image_widget = Picture(source=join(self.directory_names[self.position], image_file),
                                               rotation=randint(-30, 30), x=Window.width/2 - 300/2, y=100)

                        self.add_widget(image_widget)

    def clear_pictures(self):
        for widget in list(self.children):
            if isinstance(widget, Picture):
                self.remove_widget(widget)



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
                # self.ids.destnation_folder.secondary_text = self._current_selected_directory_ if self.ids.destnation_folder.secondary_text == "" else self.ids.destnation_folder.secondary_text
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
    icon = "gra.png"
    title = "Label box"
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls.theme_style = "Dark"



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



