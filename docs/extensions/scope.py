import os, re
from sphinx import addnodes

docs_to_remove = []

def setup(app):
    app.ignore = []
    app.connect('builder-inited', builder_inited)
    app.connect('env-get-outdated', env_get_outdated)
    app.connect('doctree-read', doctree_read)

def builder_inited(app):
    for doc in app.env.found_docs:
        first_directive = None
        with open(app.env.srcdir + os.sep + doc + app.env.config.source_suffix, 'r') as f:
            first_directive = f.readline() + f.readline()
        if first_directive:
            m = re.match(r'^\.\. meta::\s+:scope: (.*)$', first_directive)
            if m:
                tags = m.group(1).split(' ')
                # print "d1:", doc, m.group(1), tags, app.tags.has(m.group(1))
                include = reduce (lambda a, b: a or b,
                                  [app.tags.has(t) for t in tags])
                if not include: 
                    docs_to_remove.append(doc)

    app.env.found_docs.difference_update(docs_to_remove)

def env_get_outdated(app, env, added, changed, removed):
    added.difference_update(docs_to_remove)
    changed.difference_update(docs_to_remove)
    removed.update(docs_to_remove)
    return []

def doctree_read(app, doctree):
    for toctreenode in doctree.traverse(addnodes.toctree):
        for e in toctreenode['entries']:
            ref = str(e[1])
            if ref in docs_to_remove:
                toctreenode['entries'].remove(e)
