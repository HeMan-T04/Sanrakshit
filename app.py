from flask import Flask, render_template, request
import requests

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        website_url = request.form['website_url']

        # Launch ZAP proxy and start active scan
        zap_url = 'http://localhost:8080'
        start_scan_url = f'{zap_url}/JSON/spider/action/scan/?url={website_url}'
        response = requests.get(start_scan_url)

        # Add code to wait for the scan to complete (optional)
        # You may want to poll ZAP API for scan status and completion

        # Retrieve ZAP report
        report_url = f'{zap_url}/OTHER/core/other/htmlreport/'
        report = requests.get(report_url).text

        return render_template('result.html', report=report)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
