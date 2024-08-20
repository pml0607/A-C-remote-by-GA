from flask import Flask, jsonify, request
import time
import board
import adafruit_dht
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

sensor = adafruit_dht.DHT11(board.D4)

@app.route('/data', methods=['GET'])
def get_sensor_data():
    try:
        temperature_c = sensor.temperature
        temperature_f = temperature_c * (9 / 5) + 32
        humidity = sensor.humidity
        data = {
            "temperature_c": temperature_c,
            "temperature_f": temperature_f,
            "humidity": humidity
        }
        return jsonify(data)
    except RuntimeError as error:
        return jsonify({"error": error.args[0]})
    except Exception as error:
        sensor.exit()
        return jsonify({"error": str(error)})

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    action = req.get('queryResult').get('action')
    if action == 'get_sensor_data':
        try:
            temperature_c = sensor.temperature
            temperature_f = temperature_c * (9 / 5) + 32
            humidity = sensor.humidity
            response = {
                "fulfillmentText": f"The temperature is {temperature_c:.1f}°C ({temperature_f:.1f}°F) and the humidity is {humidity:.1f}%."
            }
        except RuntimeError as error:
            response = {
                "fulfillmentText": f"Error: {error.args[0]}"
            }
        except Exception as error:
            sensor.exit()
            response = {
                "fulfillmentText": f"Error: {str(error)}"
            }
        return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4040)
