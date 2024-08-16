from pyIR import loadRemote, Transmitter, NEC

# Initialize the IR transmitter on GPIO pin 12 (or another pin)
transmitter = Transmitter(pin=12)

# Load the remote configuration from a file
loaded_remote = loadRemote('my_remote.txt')

# Assuming NEC protocol is used and available in pyIR.py
nec_protocol = NEC()

def transmitRecordedSignal(button_name):
    """
    Transmits the IR signal for a given button name.
    """
    button = loaded_remote.identifyButton(loaded_remote.getIntegerCode(button_name))
    
    if button != -1:
        # Convert the integer code to raw data using NEC protocol
        rawData = nec_protocol.getRawFromIntegerCode(button.getIntegerCode())
        transmitter.sendSignal(rawData)
        print(f"Transmitted signal for button '{button_name}'")
    else:
        print(f"No button found with the name '{button_name}'")

def main():
    """
    Main function to execute the script.
    """
    # Prompt the user for the button name
    button_name = input("Enter the name of the button to transmit: ").strip()
    
    if button_name:
        transmitRecordedSignal(button_name)
    else:
        print("No button name entered. Exiting.")

    # Cleanup
    transmitter.cleanup()

if __name__ == "__main__":
    main()
