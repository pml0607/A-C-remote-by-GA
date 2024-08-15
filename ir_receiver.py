# Import classes from pyIR.py
from pyIR import Receiver, Remote, NEC
import threading
import sys

# Initialize the IR receiver on GPIO pin 11
receiver = Receiver(pin=11)

# Create a remote with name 'MyRemote' and NEC protocol
my_remote = Remote(name='MyRemote', protocol=NEC)

# Flag to control the recording loop
stop_flag = threading.Event()

def recordButtons():
    """
    Prompts the user to enter a name for each button and then records the signal from the remote.
    Stops when Enter is pressed.
    """
    while not stop_flag.is_set():
        # Prompt the user to enter a name for the button
        button_name = input("Enter a name for this button (or press Enter to stop): ").strip()
        
        if button_name == '':
            # Stop recording if Enter is pressed
            stop_flag.set()
            break
        
        print("Press the button on the remote that you want to record...")
        
        # Wait for the user to press the button on the remote
        rawData = receiver.getRAW()  # Get raw data from the remote
        print(f"Raw data received: {rawData}")  # Debugging output
        
        if rawData:
            code = my_remote.getIntegerCode(rawData)  # Convert raw data to binary code
            print(f"Decoded code: {code}")  # Debugging output
            
            # Add the button to the remote
            my_remote.addButton(button_name, code)
            
            print(f"Button '{button_name}' has been recorded with code: {hex(code)}")
        else:
            print("No signal detected. Please press the button on the remote again.")

# Start the recording thread
recording_thread = threading.Thread(target=recordButtons)
recording_thread.start()

# Wait for the recording thread to finish
recording_thread.join()

# Display all recorded buttons
my_remote.displayButtons()

# Save the remote configuration to a file
my_remote.saveRemote('my_remote.txt')

print("Remote configuration has been saved to 'my_remote.txt'.")
