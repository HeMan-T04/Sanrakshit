from flask import Flask, render_template, request, send_file
from flask_socketio import SocketIO
import time
import threading
from zapv2 import ZAPv2
import os
import json

API_KEY = os.getenv("API_KEY")

app = Flask(__name__)
socketio = SocketIO(app)

zap_proxy_url = 'http://localhost:8080'
zap = ZAPv2(apikey=API_KEY, proxies={
            'http': zap_proxy_url, 'https': zap_proxy_url})

ajax_spider_status = None
spider_completed = False

def extract_confidence_and_risk(json_report_path):
    with open(json_report_path, "r") as json_report_file:
        report_data = json.load(json_report_file)
    
    confidence_values = []
    risk_values = []
    
    # Extract confidence and risk values
    for site in report_data['site']:
        for alert in site.get('alerts', []):
            confidence_values.append(alert.get('confidence', 0))
            risk_values.append(alert.get('riskcode', 0))
    
    return confidence_values, risk_values
def extract_active_scan_vulnerabilities(json_report_path):
    with open(json_report_path, "r") as json_report_file:
        report_data = json.load(json_report_file)
    
    active_scan_vulnerabilities = []

    # Extract active scan vulnerabilities
    for site in report_data['site']:
        for alert in site.get('alerts', []):
            if alert.get('sourceid', '') == '3':  # Assuming '3' is the source ID for active scan vulnerabilities
                vulnerability = {
                    "name": alert.get('name', ''),
                    "risk": alert.get('riskdesc', ''),
                    "count": len(alert.get('instances', [])),
                    # Add more details as needed
                }
                active_scan_vulnerabilities.append(vulnerability)
    
    return active_scan_vulnerabilities

def perform_ajax_spider_scan(target_url):
    global ajax_spider_status, spider_completed

    zap.ajaxSpider.scan(target_url)

    while zap.ajaxSpider.status == "running":
        ajax_spider_status = f"Spider progress: {zap.ajaxSpider.status}"
        socketio.emit('update_status', {
                      'status': ajax_spider_status}, namespace='/')
        time.sleep(5)

    ajax_spider_results = zap.ajaxSpider.results(target_url)
    # with open("ajax_spider_results.txt", "w") as f:
    #     f.write(str(ajax_spider_results))

    ajax_spider_status = "Spider completed"
    spider_completed = True
    socketio.emit('update_status', {
                  'status': ajax_spider_status, 'completed': spider_completed}, namespace='/')

    report_path = generate_report(target_url)
    return report_path
def generate_report(target_url):
    report_title = "report"
    json_report_path = f"reports/{report_title}.json"
    html_report_path = f"reports/{report_title}.html"

    # Generate the JSON report
    json_report_content = zap.core.jsonreport(apikey=API_KEY)
    with open(json_report_path, "w") as json_report_file:
        json_report_file.seek(0)
        json_report_file.write(json_report_content)

    # Generate the HTML report
    html_report_content = zap.core.htmlreport(apikey=API_KEY)
    with open(html_report_path, "w") as html_report_file:
        html_report_file.seek(0)
        html_report_file.write(html_report_content)

    return json_report_path, html_report_path

def extract_top_vulnerability_details(json_report_path):
    with open(json_report_path, "r") as json_report_file:
        report_data = json.load(json_report_file)
    
    top_vulnerability = None
    top_vulnerability_details = None
    max_riskcode = -1
    
    # Find the top most severe vulnerability
    for site in report_data['site']:
        for alert in site.get('alerts', []):
            riskcode = int(alert.get('riskcode', 0))
            if riskcode > max_riskcode:
                max_riskcode = riskcode
                top_vulnerability = alert.get('name')
                top_vulnerability_details = {
                    "risk": alert.get('riskdesc', ''),
                    "confidence": alert.get('confidence', ''),
                    "page": alert.get('instances', [{}])[0].get('uri', ''),
                    # Add more details as needed
                }
    
    return top_vulnerability, top_vulnerability_details


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/report')
def report():
    return render_template('result.html')


@app.route('/show_report')
def show_report():
    target_url = request.args.get('target_url')
    scan_type = request.args.get('scan_type')  # Assuming you are passing the scan type as a query parameter
    json_report_path, _ = generate_report(target_url)
    with open(json_report_path, "r") as json_report_file:
        report_data = json.load(json_report_file)

    # Initialize counters for different vulnerability levels
    total_vulnerabilities = 0
    high_vulnerabilities = 0
    medium_vulnerabilities = 0
    low_vulnerabilities = 0
    informational_vulnerabilities = 0
    confidence_values, risk_values = extract_confidence_and_risk(json_report_path)
    # Extract data from the report
    for site in report_data['site']:
        for alert in site.get('alerts', []):
            riskcode = int(alert.get('riskcode', 0))
            if riskcode == 3:  # High risk
                high_vulnerabilities += 1
            elif riskcode == 2:  # Medium risk
                medium_vulnerabilities += 1
            elif riskcode == 1:  # Low risk
                low_vulnerabilities += 1
            elif riskcode == 0:  # Informational risk
                informational_vulnerabilities += 1
            total_vulnerabilities += 1
    active_scan_vulnerabilities = extract_active_scan_vulnerabilities(json_report_path)
    top_vulnerability, top_vulnerability_details = extract_top_vulnerability_details(json_report_path)

    return render_template('result.html', 
                           scan_type=scan_type,  # Pass the scan ty-pe to the template
                           total_vulnerabilities=total_vulnerabilities, 
                           high_vulnerabilities=high_vulnerabilities, 
                           medium_vulnerabilities=medium_vulnerabilities, 
                           low_vulnerabilities=low_vulnerabilities, 
                           informational_vulnerabilities=informational_vulnerabilities,
                           confidence_values=confidence_values, 
                           risk_values=risk_values,
                           top_vulnerability=top_vulnerability, 
                           top_vulnerability_details=top_vulnerability_details,
                           active_scan_vulnerabilities=active_scan_vulnerabilities)  # P

@app.route('/download_html_report')
def download_html_report():
    target_url = request.args.get('target_url')
    _, html_report_path = generate_report(target_url)
    return send_file(html_report_path, as_attachment=True)

# SocketIO event handler for starting the Spider scan
@socketio.on('start_spider', namespace='/')
def start_spider(message):
    target_url = message['target_url']

    spider_thread = threading.Thread(
        target=perform_ajax_spider_scan, args=(target_url,))
    spider_thread.start()

    ajax_spider_status = "Spider started"
    socketio.emit('update_status', {
                  'status': ajax_spider_status}, namespace='/')


if __name__ == '__main__':
    socketio.run(app, debug=True)
