from flask import Flask, request, jsonify
from pyIR import loadRemote, Transmitter, NEC
import board
import adafruit_dht
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Initialize the IR transmitter on GPIO pin 12 (or another pin)
transmitter = Transmitter(pin=12)

# Load the remote configuration from a file
loaded_remote = loadRemote('my_remote.txt')

# Initialize NEC protocol
nec_protocol = NEC()

def transmitSignal(button_name):
    """
    Transmit the IR signal for a given button name.
    """
    button = loaded_remote.identifyButton(loaded_remote.getIntegerCode(button_name))
    
    if button != -1:
        # Convert the integer code to raw data using NEC protocol
        rawData = nec_protocol.getRawFromIntegerCode(button.getIntegerCode())
        transmitter.sendSignal(rawData)
        return f"Transmitted signal for button '{button_name}'"
    else:
        return f"No button found with the name '{button_name}'"

@app.route('/transmit', methods=['POST'])
def transmit():
    """
    Endpoint to handle transmit requests.
    """
    data = request.json
    button_name = data.get('button_name', '').strip()

    if button_name:
        result = transmitSignal(button_name)
        return jsonify({'status': 'success', 'message': result})
    else:
        return jsonify({'status': 'error', 'message': 'No button name provided'}), 400

@app.route('/')
def index():
    return "IR Transmitter API is running."


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

@app.route('/infor', methods=['POST'])
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
    
    elif action == 'transmit_signal':
        button_name = req.get('queryResult').get('parameters').get('button_name')
        result = transmitSignal(button_name)
        response = {
            "fulfillmentText": result
        }
        return jsonify(response)
    

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)  # Adjust the port if needed
