from bs4 import BeautifulSoup
import datetime
import time
import configparser
import ast
import pathlib
from paho.mqtt import client as mqtt_client
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

config_path = pathlib.Path(__file__).parent.absolute() / "config" / "config.cfg"
config = configparser.ConfigParser()
config.read(config_path, encoding='utf-8')

broker = str(config.get('CONFIG', 'broker'))
port = int(config.get('CONFIG', 'port'))
username = str(config.get('CONFIG', 'username'))
password = str(config.get('CONFIG', 'password'))
selenium_server = ast.literal_eval(config.get('CONFIG', 'selenium_server'))
freq = int(config.get('CONFIG', 'freq'))

service = Service()
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--disable-search-engine-choice-screen')
options.add_argument('--disable-gpu')
options.add_argument("--disable-cache")
options.add_argument("--disable-crash-reporter");
options.add_argument("--no-crash-upload");
options.add_argument('--no-sandbox')
options.add_argument('--ignore-certificate-errors')
options.add_argument('--incognito')
options.add_argument('--disable-dev-shm-usage')

url = "https://ndc.niggg.bas.bg/"
client_id = f'mqttzemetresenie'
topic0 = "homeassistant/sensor/zemetresenie/availability"
topic1 = "homeassistant/sensor/zemetresenie/startdata"
topic2 = "homeassistant/sensor/zemetresenie/startchas"
topic3 = "homeassistant/sensor/zemetresenie/magnitud"
topic4 = "homeassistant/sensor/zemetresenie/lat"
topic5 = "homeassistant/sensor/zemetresenie/lon"
topic6 = "homeassistant/sensor/zemetresenie/googlemapslink"
topic7 = "homeassistant/sensor/zemetresenie/dulbochina"
#topic8 = "homeassistant/sensor/zemetresenie/karta"
availability = 0
startdata = 'unknown'
startchas = 'unknown'
magnitud = 'unknown'
lat = 'unknown'
lon = 'unknown'
googlemapslink = 'unknown'
dulbochina = 'unknown'
#karta = 'unknown'

while True:
    print('Starting new cycle! '+str(datetime.datetime.now())[0:-7]+'\n')
    if selenium_server == "":
        browser = webdriver.Chrome(service=service, options=options)
        print("No external Selenium server is used.")
    else:
        browser = webdriver.Remote(command_executor=selenium_server, options=options)
        print("Selenium server: "+selenium_server)
    browser.get(url)
    time.sleep(3)
    html = browser.page_source
    soup = BeautifulSoup(html.encode('utf-8'), 'html.parser')
    #print(soup)

    for td in soup.find_all('tr', {'class': 'event_list', 'id': 'row0'},limit = 1):
    #for td in soup.find_all('td', {'class': 'tdBottomRowSeperator'},limit = 100):
        td = str(td).replace('" target="_blank"><img src="img/download.png" style="width:20px;height:20px;"/></a></td></tr>','').replace('<tr class="event_list" id="row0"><td>1</td><td class="text-center">','').replace('</td><td class="text-center">','&').replace('</td><td><a href="','&').replace('</td><td><img src="img/download.png" style="filter: grayscale(100%) brightness(1.50);;width:20px;height:20px;"/></td></tr>','')
        #print(str(td)+'\n\n')
        if '/' in td:
            availability = 1
            startdata = str((td).split("&")[0].split(" ")[1]).strip().replace('/','.')
            startchas = str((td).split("&")[0].split(" ")[0]).strip()+":00"
            magnitud = str((td).split("&")[1]).strip().replace('M=','')
            lat = str((td).split("&")[2]).strip().replace('°N','')
            lon = str((td).split("&")[3]).strip().replace('°E','')
            googlemapslink = str('https://www.google.bg/maps/place/')+str(lat+','+lon)+str('/@')+str(lat+','+lon)+str(',7.7z')
            dulbochina = str((td).split("&")[4]).strip().replace(' км.','')
            '''
            try:
                karta = str('https://ndc.niggg.bas.bg/')+str((td).split("&")[5]).strip()
                print('Карта: '+karta+'\n\n')
            except:
                print('Картата не е налична.')
                karta = 'unknown'
            '''

            print('Дата: '+startdata)
            print('Час (GMT): '+startchas)
            print('Магнитуд: '+magnitud)
            print('Lat°: '+lat)
            print('Lon°: '+lon)
            print('Google Maps Link: '+googlemapslink)
            print('Дълбочина: '+dulbochina)
        else:
            availability = 0
            location = 'unknown'
            typeofevent = 'unknown'
            description = 'unknown'
            start = 'unknown'
            end = 'unknown'
            print('Дата: '+startdata)
            print('Час (GMT): '+startchas)
            print('Магнитуд: '+magnitud)
            print('Lat°: '+lat)
            print('Lon°: '+lon)
            print('Google Maps Link: '+googlemapslink)
            print('Дълбочина: '+dulbochina)
            #print('Карта: '+karta+'\n\n')
            
    # Generate a Client ID with the publish prefix.
    msg0 = availability
    msg1 = startdata
    msg2 = startchas
    msg3 = magnitud
    msg4 = lat
    msg5 = lon
    msg6 = googlemapslink
    msg7 = dulbochina
    #msg8 = karta

    browser.close()
    browser.quit()

    def connect_mqtt():
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("Connected to MQTT Broker!")
            else:
                print("Failed to connect, return code %d\n", rc)

        client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1, client_id)
        client.username_pw_set(username, password)
        client.on_connect = on_connect
        client.connect(broker, port)
        return client

    def publish(client):
        client.publish(topic0, msg0, retain=False)
        client.publish(topic1, msg1)
        client.publish(topic2, msg2)
        client.publish(topic3, msg3)
        client.publish(topic4, msg4)
        client.publish(topic5, msg5)
        client.publish(topic6, msg6)
        client.publish(topic7, msg7)
        #client.publish(topic8, msg8)

    def on_disconnect(client, userdata, rc):
        logging.info("Disconnected with result code: %s", rc)
        reconnect_count, reconnect_delay = 9, FIRST_RECONNECT_DELAY
        while reconnect_count < MAX_RECONNECT_COUNT:
            logging.info("Reconnecting in %d seconds...", reconnect_delay)
            time.sleep(reconnect_delay)

            try:
                client.reconnect()
                logging.info("Reconnected successfully!")
                return
            except Exception as err:
                logging.error("%s. Reconnect failed. Retrying...", err)

            reconnect_delay *= RECONNECT_RATE
            reconnect_delay = min(reconnect_delay, MAX_RECONNECT_DELAY)
            reconnect_count += 1
        logging.info("Reconnect failed after %s attempts. Exiting...", reconnect_count)
        global FLAG_EXIT
        FLAG_EXIT = True

    def run():
        try:
            client = connect_mqtt()
            publish(client)
            client.on_disconnect = on_disconnect
        except:
            return

    if __name__ == '__main__':
        run()
        

    print('Cycle done! '+str(datetime.datetime.now())[0:-7]+'\n\n\n')
    for i in range(freq):
        time.sleep(1)
