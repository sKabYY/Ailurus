#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# Ailurus - make Linux easier to use
#
# Copyright (C) 2007-2010, Trusted Digital Technology Laboratory, Shanghai Jiao Tong University, China.
# Copyright (C) 2009-2010, Ailurus Developers Team
#
# Ailurus is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Ailurus is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ailurus; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

from __future__ import with_statement
import gtk, os, sys
from lib import *
from libu import *
from loader import *

def detect_running_instances():
    string = get_output('ps -a -u $USER | grep ailurus', True)
    if string!='':
        notify(_('Warning!'), 
           _('Another instance of Ailurus is running. '
              'It is not recommended to run multiple instance concurrently.') )

def change_task_name():
    import ctypes
    libc = ctypes.CDLL('libc.so.6')
    libc.prctl(15, 'ailurus', 0, 0, 0)

def set_default_window_icon():
    gtk.window_set_default_icon_from_file(D+'suyun_icons/default.png')

def with_same_content(file1, file2):
    import os
    if not os.path.exists(file1) or not os.path.exists(file2):
        return False
    with open(file1) as f:
        content1 = f.read()
    with open(file2) as f:
        content2 = f.read()
    return content1 == content2

def check_required_packages():
    ubuntu_missing = []
    fedora_missing = []
    archlinux_missing = []

    try: import pynotify
    except: 
        ubuntu_missing.append('python-notify')
        fedora_missing.append('notify-python')
        archlinux_missing.append('python-notify')
    try: import vte
    except: 
        ubuntu_missing.append('python-vte')
        fedora_missing.append('vte')
        archlinux_missing.append('vte')
    try: import apt
    except: 
        ubuntu_missing.append('python-apt')
    try: import rpm
    except: 
        fedora_missing.append('rpm-python')
    try: import dbus
    except: 
        ubuntu_missing.append('python-dbus')
        fedora_missing.append('dbus-python')
        archlinux_missing.append('dbus-python')
    try: import gnomekeyring
    except:
        ubuntu_missing.append('python-gnomekeyring')
        fedora_missing.append('gnome-python2-gnomekeyring')
        archlinux_missing.append('python-gnomekeyring') # I am not sure. python-gnomekeyring is on AUR. get nothing from pacman -Ss python*keyring 
    if not os.path.exists('/usr/bin/unzip'):
        ubuntu_missing.append('unzip')
        fedora_missing.append('unzip')
        archlinux_missing.append('unzip')
    if not os.path.exists('/usr/bin/wget'):
        fedora_missing.append('wget')
        archlinux_missing.append('wget')
    if not os.path.exists('/usr/bin/xterm'):
        fedora_missing.append('xterm')
        archlinux_missing.append('xterm')

    error = ((UBUNTU or UBUNTU_DERIV) and ubuntu_missing) or (FEDORA and fedora_missing) or (ARCHLINUX and archlinux_missing)
    if error:
        import StringIO
        message = StringIO.StringIO()
        print >>message, _('Necessary packages are not installed. Ailurus cannot work.')
        print >>message, ''
        print >>message, _('Please install these packages:')
        print >>message, ''
        if UBUNTU or UBUNTU_DERIV:
            print >>message, '<span color="blue">', ' '.join(ubuntu_missing), '</span>'
        if FEDORA:
            print >>message, '<span color="blue">', ' '.join(fedora_missing), '</span>'
        if ARCHLINUX:
            print >>message, '<span color="blue">', ' '.join(archlinux_missing), '</span>'
        dialog = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
        dialog.set_title('Ailurus ' + AILURUS_VERSION)
        dialog.set_markup(message.getvalue())
        dialog.run()
        dialog.destroy()

def check_dbus_daemon_status():
    correct_conf_files = True
    if not with_same_content('/etc/dbus-1/system.d/cn.ailurus.conf', '/usr/share/ailurus/support/cn.ailurus.conf'):
        correct_conf_files = False
    if not with_same_content('/usr/share/dbus-1/system-services/cn.ailurus.service', '/usr/share/ailurus/support/cn.ailurus.service'):
        correct_conf_files = False
    dbus_ok = True
    try:
        get_authentication_method()
    except:
        print_traceback()
        dbus_ok = False
    same_version = True
    try:
        running_version = get_dbus_daemon_version()
    except:
        print_traceback()
        running_version = 0
    from daemon import version as current_version
    same_version = (current_version == running_version)
    if correct_conf_files and dbus_ok and same_version: return
    def show_text_dialog(msg, icon=gtk.MESSAGE_ERROR):
        dialog = gtk.MessageDialog(type=icon, buttons=gtk.BUTTONS_OK)
        dialog.set_title('Ailurus')
        dialog.set_markup(msg)
        dialog.run()
        dialog.destroy()
    import StringIO
    message = StringIO.StringIO()
    print >>message, _('Error happened. You cannot install any software by Ailurus. :(')
    print >>message, ''
    if not correct_conf_files:
        print >>message, _('System configuration file should be updated.')
        print >>message, _('Please run these commands using <b>su</b> or <b>sudo</b>:')
        print >>message, ''
        print >>message, '<span color="blue">', 'cp /usr/share/ailurus/support/cn.ailurus.conf /etc/dbus-1/system.d/cn.ailurus.conf', '</span>'
        print >>message, '<span color="blue">', 'cp /usr/share/ailurus/support/cn.ailurus.service /usr/share/dbus-1/system-services/cn.ailurus.service', '</span>'
        print >>message, ''
        show_text_dialog(message.getvalue())
    elif not dbus_ok:
        print >>message, _("Ailurus' D-Bus daemon exited with error.")
        print >>message, _("Please restart your computer.")
        show_text_dialog(message.getvalue())
    elif not same_version:
        print >>message, _('We need to restart Ailurus daemon.')
        print >>message, _('Old version is %s.') % running_version, _('New version is %s') % current_version
        print >>message, ''
        print >>message, _('Press this button to restart daemon. Require authentication.')
        show_text_dialog(message.getvalue())
        try:
            restart_dbus_daemon()
            show_text_dialog(_('Ailurus daemon successfully restarted. Ailurus will work fine.'), icon=gtk.MESSAGE_INFO)
        except:
            print_traceback()

def wait_firefox_to_create_profile():
    if os.path.exists('/usr/bin/firefox'):
        propath = os.path.expanduser('~/.mozilla/firefox/profiles.ini')
        if not os.path.exists(propath):
            KillWhenExit.add('firefox -no-remote')
            import time
            start = time.time()
            while not os.path.exists(propath) and time.time() - start < 6:
                time.sleep(0.1)

def exception_happened(etype, value, tb):
    if etype == KeyboardInterrupt: return
    
    import traceback, StringIO, os, platform
    traceback.print_tb(tb, file=sys.stderr)
    msg = StringIO.StringIO()
    traceback.print_tb(tb, file=msg)
    print >>msg, etype, ':', value
    print >>msg, platform.dist()
    print >>msg, os.uname()
    print >>msg, 'Ailurus version:', AILURUS_VERSION

    title_box = gtk.HBox(False, 5)
    import os
    if os.path.exists(D+'umut_icons/bug.png'):
        image = gtk.Image()
        image.set_from_file(D+'umut_icons/bug.png')
        title_box.pack_start(image, False)
    title = label_left_align(_('A bug appears. Would you please tell Ailurus developers? Thank you!') + 
                             '\n' + _('Please copy and paste following text into bug report web-page.'))
    title_box.pack_start(title, False)
    
    textview_traceback = gtk.TextView()
    gray_bg(textview_traceback)
    textview_traceback.set_wrap_mode(gtk.WRAP_WORD)
    textview_traceback.get_buffer().set_text(msg.getvalue())
    textview_traceback.set_cursor_visible(False)
    scroll_traceback = gtk.ScrolledWindow()
    scroll_traceback.set_shadow_type(gtk.SHADOW_IN)
    scroll_traceback.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    scroll_traceback.add(textview_traceback)
    scroll_traceback.set_size_request(-1, 300)
    button_copy = image_stock_button(gtk.STOCK_COPY, _('Copy text to clipboard'))
    def clicked():
        buffer = textview_traceback.get_buffer()
        start = buffer.get_start_iter()
        end = buffer.get_end_iter()
        clipboard = gtk.clipboard_get()
        clipboard.set_text(buffer.get_text(start, end))
    button_copy.connect('clicked', lambda w: clicked())
    button_report_bug = image_stock_button(gtk.STOCK_DIALOG_WARNING, _('Click here to report bug via web-page') )
    button_report_bug.connect('clicked', lambda w: report_bug() )
    button_close = image_stock_button(gtk.STOCK_CLOSE, _('Close'))
    button_close.connect('clicked', lambda w: window.destroy())
    bottom_box = gtk.HBox(False, 10)
    bottom_box.pack_end(button_close, False)
    bottom_box.pack_end(button_report_bug, False)
    bottom_box.pack_end(button_copy, False)
    
    vbox = gtk.VBox(False, 5)
    vbox.pack_start(title_box, False)
    vbox.pack_start(scroll_traceback)
    vbox.pack_start(bottom_box, False)
    window = gtk.Window()
    window.set_title(_('Bug appears!'))
    window.set_border_width(10)
    window.add(vbox)
    window.show_all()

sys.excepthook = exception_happened

class toolitem(gtk.ToolItem):
    def __load_image(self):
        pixbuf = get_pixbuf(self.icon, self.image_size, self.image_size)
        image = gtk.image_new_from_pixbuf(pixbuf)
        child = self.align_image.get_child()
        if child:
            self.align_image.remove(child)
        self.align_image.add(image)
        self.align_image.set_size_request(3*self.image_size/2, -1)
        self.align_image.show_all()
    
    def refresh(self, size):
        if self.image_size != size:
            self.image_size = size
            self.__load_image()
            self.__change_font_size()
    
    def __change_font_size(self):
        import pango
        if self.image_size <= 25:
            font_size = 4
        elif 25 < self.image_size <= 30:
            font_size = 5
        elif 30 < self.image_size <= 40:
            font_size = 6
        else:
            font_size = 8
        self.text.modify_font(pango.FontDescription('Sans %s' % font_size))
        
    def __init__(self, icon, text, signal_name, callback, *callback_args):
        gtk.ToolItem.__init__(self)
        
        is_string_not_empty(icon)
        is_string_not_empty(text)
        is_string_not_empty(signal_name)
        assert callable(callback)
        
        self.image_size = 40;
        self.icon = icon
        self.align_image = align_image = gtk.Alignment(0.5, 0.5)
        self.__load_image()
        self.text = text = gtk.Label(text)
        import pango
        text.modify_font(pango.FontDescription('Sans 9'))
        text.set_alignment(0.5, 0.5)
        text.set_justify(gtk.JUSTIFY_CENTER)
        vbox = vbox = gtk.VBox(False, 5)
        vbox.pack_end(text)
        vbox.pack_end(align_image)
        button = gtk.Button()
        button.add(vbox)
        button.set_relief(gtk.RELIEF_NONE)
        button.connect(signal_name, callback, *callback_args)
        self.add(button)

class PaneLoader:
    def __init__(self, main_view, pane_class, content_function = None):
        import gobject
        assert isinstance(pane_class, gobject.GObjectMeta)
        assert callable(content_function) or content_function is None
        self.main_view = main_view
        self.pane_class = pane_class
        self.content_function = content_function
        self.pane_object = None
    def get_pane(self):
        if self.pane_object is None:
            if self.content_function: arg = [self.content_function()] # has argument
            else: arg = [] # no argument
            self.pane_object = self.pane_class(self.main_view, *arg)
        return self.pane_object
    def need_to_load(self):
        return self.pane_object is None

def create_menu_from(menuitems):
    assert isinstance(menuitems, list)
    menu = gtk.Menu()
    for item in menuitems:
        menu.append(item)
    menu.show_all()
    return menu

class DefaultPaneMenuItem(gtk.CheckMenuItem):
    def __init__(self, text, value, group):
        'text is displayed. value is saved in Config. group consists of all menu items'
        assert isinstance(text, str)
        assert isinstance(value, str)
        assert isinstance(group, list)
        for obj in group:
            assert isinstance(obj, gtk.CheckMenuItem)
        self.text = text
        self.value = value.replace('\n', '')
        self.group = group
        gtk.CheckMenuItem.__init__(self, text)
        self.set_draw_as_radio(True)
        self.set_active(Config.get_default_pane() == value)
        self.connect('toggled', lambda w: self.toggled())
    def toggled(self):
        if self.get_active():
            Config.set_default_pane(self.value)
            for obj in self.group:
                if obj != self:
                    obj.set_active(False)
        self.set_active(Config.get_default_pane() == self.value)

class MainView:
    def create_default_pane_menu(self):
        'Create a menu, to select default pane.'
        menuitems = []
        reversed_order = self.ordered_key[:]
        reversed_order.reverse()
        for key in reversed_order:
            pane = self.contents[key]
            assert hasattr(pane, 'pane_class') # pane is a PaneLoader object
            assert hasattr(pane.pane_class, 'text')
            item = DefaultPaneMenuItem(pane.pane_class.text, pane.pane_class.__name__, menuitems)
            menuitems.append(item)
        return create_menu_from(menuitems)
    
    def add_quit_button(self):
        item_quit = toolitem(D+'sora_icons/m_quit.png', _('Quit'), 'clicked', self.terminate_program)
        self.toolbar.insert(item_quit, 0)

    def add_study_button_preference_button_other_button(self):
        item = toolitem(D+'sora_icons/m_others.png', _('Others'), 'button_release_event', 
                        self.__show_popupmenu_on_toolbaritem, create_menu_from(load_others_menuitems()))
        self.toolbar.insert(item, 0)
        self.menu_preference = create_menu_from(load_preferences_menuitems())
        default_pane_item = gtk.MenuItem(_('Default pane'))
        default_pane_item.set_submenu(self.create_default_pane_menu())
        self.menu_preference.append(default_pane_item)
        self.menu_preference.show_all()
        item = toolitem(D+'sora_icons/m_preference.png', _('Preferences'), 'button_release_event', 
                        self.__show_popupmenu_on_toolbaritem, self.menu_preference)
        self.toolbar.insert(item, 0)
        item = toolitem(D+'sora_icons/m_study_linux.png', _('Study\nLinux'), 'button_release_event', 
                        self.__show_popupmenu_on_toolbaritem, create_menu_from(load_study_linux_menuitems()))
        self.toolbar.insert(item, 0)

    def add_pane_buttons_in_toolbar(self):
        for key in self.ordered_key:
            pane_loader = self.contents[key]
            icon = pane_loader.pane_class.icon
            text = pane_loader.pane_class.text
            item = toolitem(icon, text, 'clicked', self.activate_pane, key)
            self.toolbar.insert(item, 0)
        
        self.activate_pane(None, Config.get_default_pane())

    def get_item_icon_size(self):
        return min( int(self.last_x / 20), 48)

    def __refresh_toolbar(self):
        icon_size = self.get_item_icon_size()
        for i in range(0, self.toolbar.get_n_items()):
            item = self.toolbar.get_nth_item(i)
            item.refresh(icon_size)

    def __show_popupmenu_on_toolbaritem(self, widget, event, menu):
        if event.type == gtk.gdk.BUTTON_RELEASE and event.button == 1:
            def func(menu):
                (x, y) = self.window.get_position()
                rectangle = widget.get_allocation()
                x += rectangle.x
                y += rectangle.y + rectangle.height + 20
                return (x, y, True)
            menu.popup(None, None, func, event.button, event.time)
            return True
        return False
    
    def activate_pane(self, widget, name):
        assert isinstance(name, str)
        self.current_pane = name
        for child in self.toggle_area.get_children():
            self.toggle_area.remove(child)
        pane_loader = self.contents[name]
        if pane_loader.need_to_load():
            import pango
            label = gtk.Label(_('Please wait a few seconds'))
            label.modify_font(pango.FontDescription('Sans 20'))
            self.toggle_area.add(label)
            self.toggle_area.show_all()
            while gtk.events_pending(): gtk.main_iteration()
            pane = pane_loader.get_pane() # load pane
            for child in self.toggle_area.get_children():
                self.toggle_area.remove(child)
            if hasattr(pane, 'get_preference_menuitems'): # insert preference_menuitems
                for item in pane.get_preference_menuitems():
                    self.menu_preference.append(item)
                self.menu_preference.show_all()
        self.toggle_area.add(pane_loader.get_pane())
        self.toggle_area.show_all()

    def lock(self):
        self.stop_delete_event = True
        self.toolbar.set_sensitive(False)
    
    def unlock(self):
        self.stop_delete_event = False
        self.toolbar.set_sensitive(True)

    def query_whether_exit(self):
        dialog = gtk.MessageDialog(self.window, 
                gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK_CANCEL, 
                _('Are you sure to exit?'))
        check_button = gtk.CheckButton(_('Do not query me any more.'))
        dialog.vbox.pack_start(check_button)
        dialog.vbox.show_all()
        ret = dialog.run()
        dialog.destroy()
        if ret == gtk.RESPONSE_OK:
            Config.set_query_before_exit(not check_button.get_active())
            return True
        else:
            return False

    def terminate_program(self, *w):
        if Config.get_query_before_exit() and not self.query_whether_exit():
            return True
        
        if self.stop_delete_event:
            return True
        
        from support.windowpos import WindowPos
        WindowPos.save(self.window,'main')

        gtk.main_quit()
        sys.exit()

    def register(self, pane_class, content_function = None):
        import gobject
        key = pane_class.__name__
        self.contents[key] = PaneLoader(self, pane_class, content_function)
        self.ordered_key.append(key)

    def __init__(self):
        self.window = None # MainView window
        self.stop_delete_event = False
        self.contents = {}
        self.ordered_key = [] # contains keys in self.contents, in calling order of self.register
        self.menu_preference = None # "Preference" menu
        
        self.toggle_area = gtk.VBox()
        self.toggle_area.set_border_width(5)
        
        vbox = gtk.VBox(False, 0)
        
        self.toolbar = gtk.Toolbar()
        self.toolbar.set_orientation(gtk.ORIENTATION_HORIZONTAL)
        self.toolbar.set_style(gtk.TOOLBAR_BOTH)
        vbox.pack_start(self.toolbar, False)
        
        vbox.pack_start(self.toggle_area, True, True)
        
        self.window = window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_title('Ailurus')
        self.last_x = self.window.get_size()[0]
        def configure_event(window, event, toolbar):
            if self.last_x != self.window.get_size()[0]:
                self.last_x = self.window.get_size()[0]
                self.__refresh_toolbar()
        self.window.connect('configure_event', configure_event, self.toolbar)
        window.connect("delete_event", self.terminate_program)
        window.add(vbox)

        from support.windowpos import WindowPos
        WindowPos.load(window,'main')
        
        from system_setting_pane import SystemSettingPane
        from clean_up_pane import CleanUpPane
        from info_pane import InfoPane
        from install_remove_pane import InstallRemovePane
        from computer_doctor_pane import ComputerDoctorPane
        if UBUNTU or UBUNTU_DERIV:
            from ubuntu.fastest_mirror_pane import UbuntuFastestMirrorPane
            from ubuntu.apt_recovery_pane import UbuntuAPTRecoveryPane
        if FEDORA:
            from fedora.fastest_mirror_pane import FedoraFastestMirrorPane
            from fedora.rpm_recovery_pane import FedoraRPMRecoveryPane

        self.register(ComputerDoctorPane, load_cure_objs)
        self.register(CleanUpPane)
        if UBUNTU or UBUNTU_DERIV:
            self.register(UbuntuAPTRecoveryPane)
            self.register(UbuntuFastestMirrorPane)
        if FEDORA:
            self.register(FedoraRPMRecoveryPane)
            self.register(FedoraFastestMirrorPane)
        self.register(InstallRemovePane, load_app_objs)
        self.register(SystemSettingPane, load_setting)
        self.register(InfoPane, load_info)
        
        self.add_quit_button()
        self.add_study_button_preference_button_other_button()
        self.add_pane_buttons_in_toolbar()
        self.window.show_all()

sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
change_task_name()
set_default_window_icon()
check_required_packages()
check_dbus_daemon_status()

#from support.splashwindow import SplashWindow
#splash = SplashWindow()
#splash.show_all()
while gtk.events_pending(): gtk.main_iteration()
main_view = MainView()
#splash.destroy()

gtk.gdk.threads_init()
gtk.gdk.threads_enter()
gtk.main()
gtk.gdk.threads_leave()
sys.exit()
