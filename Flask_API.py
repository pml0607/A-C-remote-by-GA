from flask import Flask, request, jsonify
from pyIR import loadRemote, Transmitter, NEC
import board
import adafruit_dht
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
loaded_remote = loadRemote('my_remote.txt')
nec_protocol = NEC()
def transmitSignal(button_name):

    transmitter = Transmitter(pin=12)
    
    button = loaded_remote.identifyButtonByName(button_name)
    
    if button != -1:
        button_code = button.getIntegerCode()
        # Convert the integer code to raw data using NEC protocol
        rawData = nec_protocol.getRawFromIntegerCode(button_code)
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


@app.route('/data', methods=['GET'])
def get_sensor_data():
    try:
        sensor = adafruit_dht.DHT11(board.D4)
        temperature_c = sensor.temperature
        temperature_f = temperature_c * (9 / 5) + 32
        humidity = sensor.humidity
        sensor.exit()
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
            # Gọi API /data để lấy nhiệt độ và độ ẩm
            response = requests.get('http://:5000/data')
            sensor_data = response.json()

            if 'error' in sensor_data:
                return jsonify({
                    "fulfillmentText": f"Error: {sensor_data['error']}"
                })

            # Format lại dữ liệu từ API /data
            temperature_c = sensor_data['temperature_c']
            temperature_f = sensor_data['temperature_f']
            humidity = sensor_data['humidity']

            # Phản hồi lại cho Dialogflow
            fulfillment_text = f"The temperature is {temperature_c:.1f}°C ({temperature_f:.1f}°F) and the humidity is {humidity:.1f}%."
            return jsonify({
                "fulfillmentText": fulfillment_text
            })
        except Exception as error:
            logging.error(f"Exception in webhook get_sensor_data: {str(error)}")
            return jsonify({
                "fulfillmentText": f"Error: {str(error)}"
            })

    elif action == 'transmit_signal':
        button_name = req.get('queryResult').get('parameters').get('button_name')
        if button_name:
            # Gọi API /transmit để phát tín hiệu
            transmit_response = requests.post('http://localhost:5000/transmit', json={'button_name': button_name})
            transmit_result = transmit_response.json()
            
            if transmit_response.status_code == 200 and transmit_result.get('status') == 'success':
                return jsonify({
                    "fulfillmentText": transmit_result['message']
                })
            else:
                return jsonify({
                    "fulfillmentText": f"Error: {transmit_result.get('message', 'Unknown error')}"
                })
        else:
            return jsonify({
                "fulfillmentText": "No button name provided."
            })

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug='True')  # Adjust the port if needed
