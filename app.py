# from flask import Flask, render_template, request
# import requests
# from zapv2 import ZAPv2

# app = Flask(__name__)

# @app.route('/', methods=['GET', 'POST'])
# def index():
#     if request.method == 'POST':
#         website_url = request.form['website_url']
#         zap_proxy_url = 'http://localhost:8080'

#         # Create ZAP API client
#         zap = ZAPv2(apikey='your-api-key', proxies={'http': zap_proxy_url, 'https': zap_proxy_url})

#         # Define the target URL
#         target_url = 'http://example.com'

#         # Perform the Ajax Spider scan
#         zap.ajaxSpider.scan(target_url)

#         # Wait for the scan to complete (you might want to implement polling logic)
#         while int(zap.ajaxSpider.status) < 100:
#             print(f"Spider progress: {zap.ajaxSpider.status}%")
#             time.sleep(5)

#         # Retrieve the Ajax Spider results
#         ajax_spider_results = zap.ajaxSpider.results(target_url)

#         # Display the results
#         print("Ajax Spider Results:")
#         print(ajax_spider_results)
#         # Launch ZAP proxy and start active scan
#         # zap_url = 'http://localhost:8080'
#         # start_scan_url = f'{zap_url}/JSON/spider/action/scan/?url={website_url}'
#         # response = requests.get(start_scan_url)
#         # zapv2.ajaxSpider(response.text)

#         # # Add code to wait for the scan to complete (optional)
#         # # You may want to poll ZAP API for scan status and completion

#         # # Retrieve ZAP report
#         # report_url = f'{zap_url}/OTHER/core/other/htmlreport/'
#         # report = requests.get(report_url).text

#         return render_template('result.html', report=report)

#     return render_template('index.html')

# if __name__ == '__main__':
#     app.run(debug=True)
from flask import Flask, render_template, request
from zapv2 import ZAPv2
import time

app = Flask(__name__)

# Set the ZAP proxy URL
zap_proxy_url = 'http://localhost:8080'

# Create ZAP API client
zap = ZAPv2(apikey='up41v4rs2e3fnucl1ctfs27djn', proxies={'http': zap_proxy_url, 'https': zap_proxy_url})

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        target_url = request.form['website_url']

        # Perform the Ajax Spider scan
        zap.ajaxSpider.scan(target_url)

        # Wait for the scan to complete (you might want to implement polling logic)
        while int(zap.ajaxSpider.status) < 100:
            print(f"Spider progress: {zap.ajaxSpider.status}%")
            time.sleep(5)

        # Retrieve the Ajax Spider results
        ajax_spider_results = zap.ajaxSpider.results(target_url)

        return render_template('result.html', results=ajax_spider_results)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
