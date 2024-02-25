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
        target_url = request.form.get('target_url')
        ScanningType = request.form.get('ScanningType')
        print(target_url, ScanningType)

        # Perform the Ajax Spider scan
        zap.ajaxSpider.scan(target_url)

        # Wait for the scan to complete (you might want to implement polling logic)
        # print(f'status={zap.ajaxSpider.status}')
        while zap.ajaxSpider.status == "running":
            print(f"Spider progress: {zap.ajaxSpider.status}")
            time.sleep(5)

        # Retrieve the Ajax Spider results
        ajax_spider_results = zap.ajaxSpider.results(target_url)
        f=open("ajax_spider_results.txt","w")
        f.write(str(ajax_spider_results))
        f.close()

        return render_template('result.html', results=ajax_spider_results)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
