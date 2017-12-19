"""
A simple server used to show mpld3 images -- based on _server in the mpld3 package.

Version: 2015dec29
"""

from pylab import ion, ioff, isinteractive, close
import optima as op
import threading
import webbrowser
import socket
import itertools
import random
try: import BaseHTTPServer as server # Python 2.x
except: from http import server # Python 3.x


def generate_handler(html, files=None):
    if files is None:
        files = {}

    class MyHandler(server.BaseHTTPRequestHandler):
        def do_GET(self):
            """Respond to a GET request."""
            if self.path == '/':
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(html.encode())
            elif self.path in files:
                content_type, content = files[self.path]
                self.send_response(200)
                self.send_header("Content-type", content_type)
                self.end_headers()
                self.wfile.write(content.encode())
            else:
                self.send_error(404)

    return MyHandler


def find_open_port(ip, port, n=50):
    """Find an open port near the specified port"""
    ports = itertools.chain((port + i for i in range(n)), (port + random.randint(-2 * n, 2 * n)))
    for port in ports:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = s.connect_ex((ip, port))
        s.close()
        if result != 0: return port
    raise ValueError("No open ports found")


def serve(html, ip='127.0.0.1', port=8888, n_retries=50):
    """Start a server serving the given HTML, and open a browser

    Example:
       html = '<b>Hello, world!</b>'
       import optima as op
       op._webserver.serve(html)

    Parameters
    ----------
    html : string
        HTML to serve
    ip : string (default = '127.0.0.1')
        ip address at which the HTML will be served.
    port : int (default = 8888)
        the port at which to serve the HTML
    n_retries : int (default = 50)
        the number of nearby ports to search if the specified port is in use.
    """
    port = find_open_port(ip, port, n_retries)
    Handler = generate_handler(html)

    # Create server
    srvr = server.HTTPServer((ip, port), Handler)

    # Use a thread to open a web browser pointing to the server
    try: browser = webbrowser.get('google-chrome') # CK: Try google Chrome first
    except: browser = webbrowser.get() # If not, just use whatever
    b = lambda: browser.open('http://{0}:{1}'.format(ip, port))
    threading.Thread(target=b).start()

    # CK: don't serve forever, just create it once
    srvr.handle_request()


def browser(results, toplot=None, doplot=True):
    ''' 
    Create an MPLD3 GUI and display in the browser. This is basically a testbed for 
    the Optima frontend.
    
    Usage example:
    	import optima as op
    	P = op.demo(0)
        browser(P.result())
    
    where results is the output of e.g. runsim() and toplot is an optional list of form e.g.
        toplot = ['prev-tot', 'inci-pop']
    
    With doplot=True, launch a web server. Otherwise, return the HTML representation of the figures.
    
    Version: 2017aug02
    '''
    import mpld3 # Only import this if needed, since might not always be available
    import json

    ## Specify the div style, and create the HTML template we'll add the data to
    divstyle = "float: left"
    html = '''
    <html>
    <head><script src="https://code.jquery.com/jquery-1.11.3.min.js"></script></head>
    <body>
    !MAKE DIVS!
    <script>function mpld3_load_lib(url, callback){var s = document.createElement('script'); s.src = url; s.async = true; s.onreadystatechange = s.onload = callback; s.onerror = function(){console.warn("failed to load library " + url);}; document.getElementsByTagName("head")[0].appendChild(s)} mpld3_load_lib("https://mpld3.github.io/js/d3.v3.min.js", function(){mpld3_load_lib("https://mpld3.github.io/js/mpld3.v0.3git.js", function(){
    !DRAW FIGURES!
    })});
    </script>
    <script>
    function move_year() {
        console.log('trying to move year');
        var al = $('.mpld3-baseaxes').length;
        var dl = $('div.fig').length
        if (al === dl) {
            $('.mpld3-baseaxes > text').each(function() {
                var value = $(this).text();
                if (value === 'Year') {
                    console.log('found year');
                    $(this).attr('y', parseInt($(this).attr('y'))+10);
                    console.log($(this).attr('y'));
                }
            });
        } else {
            setTimeout(move_year, 150);
        }
    }
    function format_xaxis() {
        var axes = $('.mpld3-xaxis');
        var al = axes.length;
        var dl = $('div.fig').length;
        if (al === dl) {
            $(axes).find('g.tick > text').each(function() {
                $(this).text($(this).text().replace(',',''));
            });
        } else {
            setTimeout(format_xaxis, 150);
        }
    }
    function add_lines_to_legends() {
        console.log('adding lines to legends');
        var al = $('.mpld3-baseaxes').length;
        var dl = $('div.fig').length
        if (al === dl) {
            $('div.fig').each(function() {
                var paths = $(this).find('.mpld3-baseaxes > text');
                if (paths) {
                    var legend_length = paths.length - 2;
                    var lines = $(this).find('.mpld3-axes > path');
                    var lines_to_copy = lines.slice(lines.length - legend_length, lines.length);
                    $(this).find('.mpld3-baseaxes').append(lines_to_copy);
                }
            });
        } else {
            setTimeout(add_lines_to_legends, 150);
        }
    }
    $(document).ready(function() {
        format_xaxis();
        move_year();
        add_lines_to_legends();
    });
    </script>
    </body></html>
    '''
    
    # Preliminaries
    wasinteractive = isinteractive()
    if wasinteractive: ioff()

    ## Create the figures to plot
    jsons = [] # List for storing the converted JSONs
    plots = op.makeplots(results=results, toplot=toplot) # Generate the plots
    op.reanimateplots(plots)
    nplots = len(plots) # Figure out how many plots there are
    for p in range(nplots): # Loop over each plot
        mpld3.plugins.connect(plots[p], mpld3.plugins.MousePosition(fontsize=14,fmt='.4r')) # Add plugins
        jsons.append(str(json.dumps(mpld3.fig_to_dict(plots[p])))) # Save to JSON
        close(plots[p]) # We're done, close it
    if wasinteractive: ion()
    
    ## Create div and JSON strings to replace the placeholers above
    divstr = ''
    jsonstr = ''
    for p in range(nplots):
        divstr += '<div style="%s" id="fig%i" class="fig"></div>\n' % (divstyle, p) # Add div information: key is unique ID for each figure
        jsonstr += 'mpld3.draw_figure("fig%i", %s);\n' % (p, jsons[p]) # Add the JSON representation of each figure -- THIS IS KEY!
    html = html.replace('!MAKE DIVS!',divstr) # Populate div information
    html = html.replace('!DRAW FIGURES!',jsonstr) # Populate figure information
    
    ## Launch a server or return the HTML representation
    if doplot: serve(html)
    else: return html