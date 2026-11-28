"""The public Vite assets shared by the dashboard and evidence archive."""
from .publication import inside, read

WORKBENCH_MANIFEST = 'workbench/.vite/manifest.json'
ASSET_TYPES = {'.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css',
               '.woff2': 'font/woff2', '.svg': 'image/svg+xml'}


def workbench_assets(site):
    """Register only the files named in the build manifest and the entry page."""
    manifest = site / WORKBENCH_MANIFEST
    if not manifest.exists():
        return {}
    paths = {'index.html'}
    for entry in read(manifest).values():
        paths.add(entry['file'])
        paths.update(entry.get('css', []))
        paths.update(entry.get('assets', []))
    registered = {}
    for name in sorted(paths):
        path = inside(site / 'workbench', name)
        if not path.is_file() or path.suffix not in ASSET_TYPES:
            raise ValueError('Invalid workbench asset: ' + name)
        registered['/workbench/' + name] = ('workbench/' + name, ASSET_TYPES[path.suffix])
    for route in ('/', '/workbench', '/workbench/'):
        registered[route] = ('workbench/index.html', 'text/html')
    return registered
