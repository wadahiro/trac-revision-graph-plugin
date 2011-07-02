# -*- coding: utf-8 -*-
#
# Copyright (C) 2003-2009 Edgewall Software
# Copyright (C) 2003-2005 Jonas Borgström <jonas@edgewall.com>
# Copyright (C) 2005-2007 Christian Boos <cboos@neuf.fr>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://trac.edgewall.org/log/.
#
# Author: Jonas Borgström <jonas@edgewall.com>
#         Christian Boos <cboos@neuf.fr>

from itertools import izip

from genshi.builder import tag

from trac.resource import ResourceNotFound 
from trac.util.datefmt import datetime, utc
from trac.util.translation import tag_, _
from trac.versioncontrol.api import Changeset, NoSuchNode, NoSuchChangeset

__all__ = ['make_log_graph']

def make_log_graph(repos, revs):
    """Generate graph information for the given revisions.
    
    Returns a tuple `(threads, vertices, columns)`, where:
    
     * `threads`: List of paint command lists `[(type, column, line)]`, where
       `type` is either 0 for "move to" or 1 for "line to", and `column` and
       `line` are coordinates.
     * `vertices`: List of `(column, thread_index)` tuples, where the `i`th
       item specifies the column in which to draw the dot in line `i` and the
       corresponding thread.
     * `columns`: Maximum width of the graph.
    """
    threads = []
    vertices = []
    columns = 0
    revs = iter(revs)
    
    def add_edge(thread, column, line):
        if thread and thread[-1][:2] == [1, column] \
                and thread[-2][1] == column:
            thread[-1][2] = line
        else:
            thread.append([1, column, line])
        
    try:
        next_rev = revs.next()
        line = 0
        active = []
        active_thread = []
        while True:
            rev = next_rev
            if rev not in active:
                # Insert new head
                threads.append([[0, len(active), line]])
                active_thread.append(threads[-1])
                active.append(rev)
            
            columns = max(columns, len(active))
            column = active.index(rev)
            vertices.append((column, threads.index(active_thread[column])))
            
            next_rev = revs.next() # Raises StopIteration when no more revs
            next = active[:]
            parents = list(repos.parent_revs(rev))
            
            # Replace current item with parents not already present
            new_parents = [p for p in parents if p not in active]
            next[column : column + 1] = new_parents
            
            # Add edges to parents
            for col, (r, thread) in enumerate(izip(active, active_thread)):
                if r in next:
                    add_edge(thread, next.index(r), line + 1)
                elif r == rev:
                    if new_parents: 
                        parents.remove(new_parents[0])
                        parents.append(new_parents[0])
                    for parent in parents:
                        if parent != parents[0]:
                            thread.append([0, col, line])
                        add_edge(thread, next.index(parent), line + 1)
            
            if not new_parents:
                del active_thread[column]
            else:
                base = len(threads)
                threads.extend([[0, column + 1 + i, line + 1]]
                                for i in xrange(len(new_parents) - 1))
                active_thread[column + 1 : column + 1] = threads[base:]
            
            active = next
            line += 1
    except StopIteration:
        pass
    return threads, vertices, columns
