# -*- coding: utf-8 -*-
#
# Authors: Jendrik Seipp (jendrikseipp@web.de)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

import os
import subprocess
import logging
from gettext import gettext as _

import gtk
import gobject

import tools
import modules
from tools import consts, prefs
from tools.log import logger


# Module information
MOD_INFO = ('Search', ('Search'), ('Search your filesystem for music'), [], True, False)
MOD_NAME = MOD_INFO[modules.MODINFO_NAME]

MIN_CHARS = 3
SEARCH_DIRS = ['/home/jendrik/Musik']



class Search(modules.ThreadedModule):

    def __init__(self):
        """ Constructor """
        handlers = {
                        #consts.MSG_EVT_MOD_LOADED:   self.onModLoaded,
                        consts.MSG_EVT_APP_STARTED:  self.onAppStarted,
                        consts.MSG_EVT_SEARCH_START: self.onSearch,
                   }

        modules.ThreadedModule.__init__(self, handlers)
        
        
    def search_dir(self, dir, query):
        cmd = ['find', dir]
        for part in query.split():
            cmd.extend(['-iwholename', '*%s*' % part])
        logging.info('Searching with command: %s' % ' '.join(cmd))
        output = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]
        output = sorted(output.splitlines(), key=lambda path: path.lower())
        logging.info('Results for %s: %s' % (query, len(output)))
        return output


    # --== Message handlers ==--


    def onAppStarted(self):
        """ The module has been loaded """
        wTree = tools.prefs.getWidgetsTree()
        self.searchbox = gtk.Entry()
        self.searchbox.set_size_request(210, -1)
        
        search_container = gtk.HBox()
        search_container.pack_start(self.searchbox, False)
        search_container.show_all()
        
        hbox3 = wTree.get_widget('hbox3')
        hbox3.pack_start(search_container)
        hbox3.set_property('homogeneous', True)
        hbox3.reorder_child(search_container, 0)
        
        
        if hasattr(self.searchbox, 'set_icon_from_stock'):
            #self.searchbox.set_icon_from_stock(0, gtk.STOCK_FIND)
            #self.searchbox.set_icon_sensitive(0, False)
            self.searchbox.set_icon_from_stock(1, gtk.STOCK_CLEAR)
            self.searchbox.connect('icon-press', self.on_searchbox_clear)
        
        self.searchbox.connect('activate', self.on_searchbox_activate)
        self.searchbox.connect('changed', self.on_searchbox_changed)
        
        # Cache results for a faster first search
        gobject.timeout_add_seconds(10, self.search_dir, SEARCH_DIRS[0], 'caching_files')
        
        
    def onSearch(self, query):
        dir = SEARCH_DIRS[0]
        results = self.search_dir(dir, query)
        modules.postMsg(consts.MSG_EVT_SEARCH_END, {'results': results, 'query': query})
        
        
    #------- GTK handlers ----------------
        
    def on_searchbox_activate(self, entry):
        query = self.searchbox.get_text().strip()
        if len(query) < MIN_CHARS:
            logging.info('Search term has to have at least %d characters' % MIN_CHARS)
            return
        #print repr(self.searchbox.get_text()), repr(self.searchbox.get_text().decode('utf-8'))
        query = self.searchbox.get_text().decode('utf-8')
        logging.info('Query: %s' % repr(query))
        modules.postMsg(consts.MSG_EVT_SEARCH_START, {'query': query})
        
        
    def on_searchbox_changed(self, entry):
        if self.searchbox.get_text().strip() == '':
            modules.postMsg(consts.MSG_EVT_SEARCH_RESET, {})
            
    
    def on_searchbox_clear(self, entry, icon_pos, event):
        if icon_pos == 1:
            self.searchbox.set_text('')
        
    