from flask import Flask, render_template, request
from zapv2 import ZAPv2
from flask_socketio import SocketIO
import time
import threading
from flask import redirect

# app intitalization 
app = Flask(__name__)
socketio = SocketIO(app)

# Set the ZAP proxy URL
zap_proxy_url = 'http://localhost:8080'

# Create ZAP API client
zap = ZAPv2(apikey='up41v4rs2e3fnucl1ctfs27djn', proxies={'http': zap_proxy_url, 'https': zap_proxy_url})

# Global variable to store the Ajax Spider status
ajax_spider_status = None
spider_completed = False

# Function to perform the Ajax Spider scan
def perform_ajax_spider_scan(target_url):
    global ajax_spider_status, spider_completed

    # Perform the Ajax Spider scan
    zap.ajaxSpider.scan(target_url)

    # Poll the status and update global variable
    while zap.ajaxSpider.status == "running":
        ajax_spider_status = f"Spider progress: {zap.ajaxSpider.status}"
        socketio.emit('update_status', {'status': ajax_spider_status}, namespace='/')

        time.sleep(5)

    # Retrieve the Ajax Spider results
    ajax_spider_results = zap.ajaxSpider.results(target_url)
    f = open("ajax_spider_results.txt", "w")
    f.write(str(ajax_spider_results))
    f.close()

    ajax_spider_status = "Spider completed"
    spider_completed = True
    socketio.emit('update_status', {'status': ajax_spider_status, 'completed': spider_completed}, namespace='/')

    # Generate a report when the spider completes
    report_path = generate_report(target_url)
def generate_report(target_url):
    # Generate the HTML report
    report_path = f"reports/{target_url.replace('://', '_').replace('/', '_')}_report.html"
    zap.core.htmlreport(apikey='up41v4rs2e3fnucl1ctfs27djn', baseurl=target_url, filename=report_path)

    return report_path

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/show_report')
def show_report():
    return render_template('Report.html')

@app.route('/download_report/<path:report_path>')
def download_report(report_path):
    full_path = os.path.join('reports', report_path)
    return send_file(full_path, as_attachment=True)


@socketio.on('start_spider', namespace='/')
def start_spider(message):
    target_url = message['target_url']

    # Create a new thread to perform the Ajax Spider scan
    spider_thread = threading.Thread(target=perform_ajax_spider_scan, args=(target_url,))
    spider_thread.start()

    ajax_spider_status = "Spider started"
    socketio.emit('update_status', {'status': ajax_spider_status}, namespace='/')


if __name__ == '__main__':
    socketio.run(app, debug=True)
