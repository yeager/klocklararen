import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gdk, Gio
import gettext, locale, os, json, time, random
__version__ = "0.1.0"

APP_ID = "se.danielnylander.klocklararen"
LOCALE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'share', 'locale')
if not os.path.isdir(LOCALE_DIR): LOCALE_DIR = '/usr/share/locale'
try:
    locale.bindtextdomain(APP_ID, LOCALE_DIR)
    gettext.bindtextdomain(APP_ID, LOCALE_DIR)
    gettext.textdomain(APP_ID)
except Exception: pass
_ = gettext.gettext
def N_(s): return s
import math as _math

class ClockFace(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self._hour = 8
        self._minute = 0
        self.set_content_width(200)
        self.set_content_height(200)
        self.set_draw_func(self._draw)
    def _draw(self, area, cr, w, h):
        cx, cy, r = w/2, h/2, min(w,h)/2-10
        cr.set_source_rgba(1,1,1,0.1)
        cr.arc(cx, cy, r, 0, 2*_math.pi)
        cr.fill()
        cr.set_source_rgba(1,1,1,0.7)
        cr.arc(cx, cy, r, 0, 2*_math.pi)
        cr.set_line_width(3)
        cr.stroke()
        for i in range(12):
            a = _math.pi/6*i - _math.pi/2
            x1,y1 = cx+_math.cos(a)*(r-10), cy+_math.sin(a)*(r-10)
            x2,y2 = cx+_math.cos(a)*r, cy+_math.sin(a)*r
            cr.move_to(x1,y1)
            cr.line_to(x2,y2)
            cr.stroke()
            cr.set_font_size(14)
            tx,ty = cx+_math.cos(a)*(r-25), cy+_math.sin(a)*(r-25)
            t = str(i if i else 12)
            ext = cr.text_extents(t)
            cr.move_to(tx-ext.width/2, ty+ext.height/2)
            cr.show_text(t)
        # Hour hand
        ha = _math.pi/6*(self._hour%12 + self._minute/60) - _math.pi/2
        cr.set_line_width(4)
        cr.set_source_rgba(1,1,1,0.9)
        cr.move_to(cx,cy)
        cr.line_to(cx+_math.cos(ha)*r*0.5, cy+_math.sin(ha)*r*0.5)
        cr.stroke()
        # Minute hand
        ma = _math.pi/30*self._minute - _math.pi/2
        cr.set_line_width(2)
        cr.move_to(cx,cy)
        cr.line_to(cx+_math.cos(ma)*r*0.75, cy+_math.sin(ma)*r*0.75)
        cr.stroke()
    def set_time(self, h, m):
        self._hour = h
        self._minute = m
        self.queue_draw()

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title(_('Clock Teacher'))
        self.set_default_size(450, 550)
        self._target_h = random.randint(1,12)
        self._target_m = random.choice([0,15,30,45])
        self._score = 0

        header = Adw.HeaderBar()
        menu_btn = Gtk.MenuButton(icon_name='open-menu-symbolic')
        menu = Gio.Menu()
        menu.append(_('About'), 'app.about')
        menu_btn.set_menu_model(menu)
        header.pack_end(menu_btn)

        main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main.append(header)

        self._clock = ClockFace()
        main.append(self._clock)

        self._digital = Gtk.Label()
        self._digital.add_css_class('title-1')
        main.append(self._digital)

        self._q = Gtk.Label(label=_('What time is it?'))
        self._q.add_css_class('title-3')
        main.append(self._q)

        self._answers = Gtk.FlowBox()
        self._answers.set_max_children_per_line(4)
        self._answers.set_selection_mode(Gtk.SelectionMode.NONE)
        self._answers.set_halign(Gtk.Align.CENTER)
        self._answers.set_margin_start(16)
        self._answers.set_margin_end(16)
        main.append(self._answers)

        self._feedback = Gtk.Label()
        self._feedback.add_css_class('title-3')
        main.append(self._feedback)

        self._score_label = Gtk.Label(label=_('Score: 0'))
        self._score_label.add_css_class('dim-label')
        main.append(self._score_label)

        next_btn = Gtk.Button(label=_('Next'))
        next_btn.add_css_class('pill')
        next_btn.add_css_class('suggested-action')
        next_btn.set_halign(Gtk.Align.CENTER)
        next_btn.set_margin_bottom(16)
        next_btn.connect('clicked', lambda b: self._new_q())
        main.append(next_btn)

        self.set_content(main)
        self._new_q()

    def _new_q(self):
        self._target_h = random.randint(1,12)
        self._target_m = random.choice([0,15,30,45])
        self._clock.set_time(self._target_h, self._target_m)
        self._digital.set_text('')
        self._feedback.set_text('')
        correct = f'{self._target_h}:{self._target_m:02d}'
        opts = {correct}
        while len(opts) < 4:
            h = random.randint(1,12)
            m = random.choice([0,15,30,45])
            opts.add(f'{h}:{m:02d}')
        opts = list(opts)
        random.shuffle(opts)
        while child := self._answers.get_first_child():
            self._answers.remove(child)
        for o in opts:
            btn = Gtk.Button(label=o)
            btn.add_css_class('pill')
            btn.add_css_class('title-4')
            btn.connect('clicked', self._check, o, correct)
            self._answers.insert(btn, -1)

    def _check(self, btn, chosen, correct):
        if chosen == correct:
            self._score += 1
            self._feedback.set_text(_('Correct! 🌟'))
        else:
            self._feedback.set_text(_('It was %s') % correct)
        self._digital.set_text(correct)
        self._score_label.set_text(_('Score: %d') % self._score)

class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id='se.danielnylander.klocklararen')
        self.connect('activate', lambda a: MainWindow(application=a).present())
        about = Gio.SimpleAction.new('about', None)
        about.connect('activate', lambda a,p: Adw.AboutDialog(application_name=_('Clock Teacher'),
            application_icon=APP_ID, version=__version__, developer_name='Daniel Nylander',
            website='https://github.com/yeager/klocklararen', license_type=Gtk.License.GPL_3_0,
            comments=_('Learn to read the clock')).present(self.get_active_window()))
        self.add_action(about)

def main(): App().run()
if __name__ == '__main__': main()

