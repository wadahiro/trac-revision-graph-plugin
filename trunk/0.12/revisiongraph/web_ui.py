# -*- coding: utf-8 -*-

import pkg_resources
import re

from genshi import Markup
from genshi.builder import tag
from genshi.filters import Transformer

from trac.config import ListOption
from trac.core import *
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import add_script, add_script_data, add_stylesheet, ITemplateProvider

from util import make_log_graph

class RevisionGraphModule(Component):
    
    implements(ITemplateProvider, ITemplateStreamFilter)

    graph_colors = ListOption('revisionlog', 'graph_colors',
        ['#cc0', '#0c0', '#0cc', '#00c', '#c0c', '#c00'],
        doc="""Comma-separated list of colors to use for the TracRevisionLog
        graph display. (''since 0.13'')""")

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return [('revisiongraph', pkg_resources.resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
    
    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'revisionlog.html':
            mode = data['mode']
            revranges = data['revranges']
            path = data['path']
            verbose = data['verbose']
            repos = data['repos']
            info = data['items']
            changes = data['changes']
            
            add_stylesheet(req, 'revisiongraph/css/revisiongraph.css')
            
            try:
                repos.parent_revs
                has_linear_changesets = False
            except AttributeError:
                has_linear_changesets = True
            
            if mode != 'path_history' and revranges is None:
                 show_graph = path == '/' and not verbose \
                         and not has_linear_changesets
            
            if show_graph:
               filters = self._make_graph(req, repos, info)
               for filter in filters:
                   stream = stream | filter
                   
            filters = self._show_branches_tags(req, info, changes)
            for filter in filters:
               stream = stream | filter
                
        return stream
    
    def _make_graph(self, req, repos, info):
        # Generate graph data
        graph = {}
        threads, vertices, columns = \
            make_log_graph(repos, (item['rev'] for item in info))
        graph.update(threads=threads, vertices=vertices, columns=columns,
                     colors=self.graph_colors,
                     line_width=0.04, dot_radius=0.1)
        add_script(req, 'revisiongraph/js/excanvas.js')
        add_script(req, 'revisiongraph/js/log_graph.js')
        add_script_data(req, {'graph': graph})
        
        script = Markup("//<![CDATA[") + """
        jQuery(document).ready(function($) {
          $('th.trac-graph, td.trac-graph').show();
          var canvas = $('""" + Markup("<canvas>") + """').css({width: '%dem',
                                          height: '%dem'})
                                    .appendTo('td.trac-graph')[0];
          canvas.width = $(canvas).width();
          canvas.height = $(canvas).height();
          if (typeof(G_vmlCanvasManager) != 'undefined')
            canvas = G_vmlCanvasManager.initElement(canvas);
          $.paintLogGraph(graph, canvas);
        });
        """ % (graph['columns'] * 2, len(info) * 2) + Markup("//]]>")
        
        th = tag.th('Graph', class_='trac-graph')
        td = tag.td(class_='trac-graph', rowspan='%d' % len(info))
        
        script_filter = Transformer('//head').append(tag.script(script, type="text/javascript"))
        table_filter = Transformer('//table[@class="listing chglist"]').attr('class', 'listing chglist trac-graph')
        th_filter = Transformer('//table/thead/tr/th[@class="diff"]').before(th)
        td_filter = Transformer('//table/tbody/tr[1]/td[@class="diff"]').before(td)
        
        return [script_filter, table_filter, th_filter, td_filter]

    def _show_branches_tags(self, req, info, changes):
        filters = []
        for idx, item in enumerate(info):
            change = changes[item['rev']]
            branch_filter = Transformer('//table/tbody/tr[%d]/td[@class="summary"]' % (idx+1))
            
            for name, head in change.get_branches():
                #if branch not in ('default', 'master'):
                
                span = tag.span(name, class_="branch" + (" head" if head else ''),
                              title="Branch head" if head else 'Branch')
                filters.append(branch_filter.append(span))
                
                
            for tagname in change.get_tag_contains():
                span = tag.span(tagname, class_="tag", title="Tag")
                filters.append(branch_filter.append(span))
            
        return filters
