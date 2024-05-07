from flask import Flask, render_template, request, send_file
from flask_socketio import SocketIO
import time
import threading
from zapv2 import ZAPv2
import os
import requests
import json

API_KEY = os.getenv("API_KEY")

app = Flask(__name__)
socketio = SocketIO(app)

zap_proxy_url = 'http://localhost:8080'
zap = ZAPv2(apikey=API_KEY, proxies={'http': zap_proxy_url, 'https': zap_proxy_url})

ajax_spider_status = None
spider_completed = False


def perform_ajax_spider_scan(target_url):
    global ajax_spider_status, spider_completed

    zap.ajaxSpider.scan(target_url)

    while zap.ajaxSpider.status == "running":
        ajax_spider_status = f"Spider progress: {zap.ajaxSpider.status}"
        socketio.emit('update_status', {'status': ajax_spider_status}, namespace='/')
        time.sleep(5)

    ajax_spider_results = zap.ajaxSpider.results(target_url)
    with open("ajax_spider_results.txt", "w") as f:
        f.write(str(ajax_spider_results))

    ajax_spider_status = "Spider completed"
    spider_completed = True
    socketio.emit('update_status', {'status': ajax_spider_status, 'completed': spider_completed}, namespace='/')

    report_path = generate_report(target_url)
    return report_path


def generate_report(target_url):
    report_title = "report"
    report_path = f"reports/{report_title}.json"

    # Generate the report in traditional JSON format
    report_content = zap.core.jsonreport(apikey=API_KEY)

    # Write the report content to a file
    with open(report_path, "w") as report_file:
        report_file.write(report_content)

    return report_path


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/report')
def report():
    return render_template('result.html')


@app.route('/show_report')
def show_report():
    # Read the JSON report file
    with open("reports/report.json", "r") as report_file:
        report_data = json.load(report_file)

    # Extract data from the report
    total_vulnerabilities = 0
    for site in report_data['site']:
        total_vulnerabilities += len(site.get('alerts', []))

    return render_template('result.html', total_vulnerabilities=total_vulnerabilities)


@app.route('/download_report/<path:report_path>')
def download_report(report_path):
    full_path = os.path.join('reports', report_path)
    return send_file(full_path, as_attachment=True)


@socketio.on('start_spider', namespace='/')
def start_spider(message):
    target_url = message['target_url']

    spider_thread = threading.Thread(target=perform_ajax_spider_scan, args=(target_url,))
    spider_thread.start()

    ajax_spider_status = "Spider started"
    socketio.emit('update_status', {'status': ajax_spider_status}, namespace='/')


if __name__ == '__main__':
    socketio.run(app, debug=True)
