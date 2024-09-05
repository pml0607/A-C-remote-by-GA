
from time import sleep
import RPi.GPIO as GPIO
from datetime import datetime

#Setup GPIO connection
GPIO.setmode(GPIO.BOARD)

# Create a hardware sensor class
class Receiver:
    """Create a hardware sensor object."""

    def __init__(self,pin):
        self.sensorPin = pin # Note: this program uses the GPIO.BOARD numbering scheme
        GPIO.setup(self.sensorPin,GPIO.IN)
        self.remotes = []

    # ----------------- #
    # Add a remote object to this receiver
    def addRemote(self,remote):
        self.remotes.append(remote)
    
    # ----------------- #
    # Wait for data to be received then return it
    def getRAW(self):
        num1s = 0 # Number of consecutive 1s
        command = [] # Pulses and their timings
        previousValue = 0 # The previous pin state

        value = GPIO.input(self.sensorPin) # Current pin state
        
        while value: # Waits until pin is pulled low
            sleep(0.0001)
            value = GPIO.input(self.sensorPin)
        
        startTime = datetime.now() # Sets start time
        
        while num1s < 10000:
            if value != previousValue: # Waits until change in state occurs
                now = datetime.now() # Records the current time
                pulseLength = now - startTime # Calculate time in between pulses
                startTime = now # Resets the start time
                command.append((previousValue, pulseLength.microseconds)) # Adds pulse time to array (previous val acts as an alternating 1 / 0 to show whether time is the on time or off time)
            
            # Interrupts code if an extended high period is detected (End Of Command)	
            if value:
                num1s += 1
            else:
                num1s = 0
            
            # Reads values again
            previousValue = value
            value = GPIO.input(self.sensorPin)
        
        return command # Returns the raw information about the high and low pulses (HIGH/LOW, time µs)

    # ----------------- #
    # Listen for incoming data and identify button
    def listen(self,remotes=[]):
        if remotes == []:
            remotes = self.remotes

        while True:
            raw = self.getRAW()
            for remote in remotes:
                match = remote.identifyButton(remote.getIntegerCode(raw))
                if match != -1:
                    return match

# ========================================= #
#^ Information for functions relating to the NEC IR Protocol ^#
class NEC:
    # ----------------- #
    # Take the data about the times of pulses and convert to a binary data string according to NEC protocol
    def getIntegerCode(self,rawDATA):
        binary = 1 # Decoded binary command
        
        # Covers data to binary
        for (typ, tme) in rawDATA:
            if typ == 1: # Ignore the LOW periods, these should be consitant and thus irrelevant
                if tme > 1000: # According to NEC protocol a gap of 1687.5 microseconds represents a logical 1 so over 1000 should make a big enough distinction
                    binary = binary * 10 + 1
                else:
                    binary *= 10
                    
        if len(str(binary)) > 34: # Sometimes the binary has two rouge characters on the end
            binary = int(str(binary)[:34])
        
        return int(str(binary),2)
    
    def getRawFromIntegerCode(self, integer_code):
        """
        Convert an integer code back to raw data for NEC protocol.
        """
        binary_string = bin(integer_code)[2:].zfill(32)  # Convert to binary and pad with zeros
        raw_data = []
        
        # Generate raw data based on NEC protocol timing
        for bit in binary_string:
            if bit == '1':
                raw_data.append((1, 560))  # Timing for HIGH (logical 1)
                raw_data.append((0, 560))  # Timing for LOW
            else:
                raw_data.append((1, 560))
                raw_data.append((0, 1680))  # Timing for LOW (logical 0)

        return raw_data

    
    def getClassName(self):
        return "NEC"

# ========================================= #
#^ Remote control objects ^#
class Remote:
    """All functions related to a remote are stored here"""

    def __init__(self,name,protocol):
        self.nickname = name
        self.buttons = []
        self.protcol = protocol()
    
    # Return the binary value from raw data using the remote's protocol's method
    def getIntegerCode(self, raw):
        return self.protcol.getIntegerCode(raw)

    # Reccord a new button using sensor capture
    def recordButton(self,sensor : Receiver, buttonNickname):
        print("Ready to record data. Press the button on your remote! ")
        rawData = sensor.getRAW()
        
        self.buttons.append(Button(buttonNickname,rawData))

    # Pint out a table that shows all of the buttons in the current remote
    def displayButtons(self):
        NICKNAME_CELL_LENGTH = 15
        HEX_CELL_LENGTH = 20
        ROW_SEPARATOR = "+-" + "-"*NICKNAME_CELL_LENGTH + "-+-" + "-"*HEX_CELL_LENGTH +"-+"

        print(ROW_SEPARATOR)
        print("| Nickname        | Hex Code             |")
        print(ROW_SEPARATOR)
        for button in self.buttons:
            print("| " + button.getNickname() + (NICKNAME_CELL_LENGTH-len(button.getNickname()))*" " + " | " + button.getHex() + (HEX_CELL_LENGTH-len(button.getHex()))*" "+" |")
            print(ROW_SEPARATOR)
    
    # Save remote data to a file
    def saveRemote(self,filename):
        with open(filename,'w') as file:
            # Save properties of the class
            file.writelines("nickname:"+self.nickname+"\n")
            file.writelines("protocol:"+self.protcol.getClassName()+"\n")

            # Save buttons to file separated by '|'
            file.writelines("buttons:")
            for button in self.buttons:
                file.writelines(button.getData()+"|")
    
    # Add a button with given name and binary
    def addButton(self,name,integerValue):
        self.buttons.append(Button(name,integerValue))

    # Return button object based on given binary value
    def identifyButton(self,code):
        for button in self.buttons:
            if button.getIntegerCode() == code:
                return button
    def identifyButtonByName(self, name):
        for button in self.buttons:
            if button.getNickname() == name:
                return button
        return -1
    
# ========================================= #
#^ Class for each button ^#
class Button:
    """An individual button object"""

    def __init__(self,name,code):
        self.nickname = name
        self.integerCode = code

    # ----------------- #
    # Simple getter and setter methods #
    def getNickname(self):
        return self.nickname
    
    def getIntegerCode(self):
        return self.integerCode
    
    def getHex(self):
        return hex(self.integerCode)
    
    def getData(self): # Get data in format that can be written to data file
        return ";".join([self.nickname,str(self.integerCode)])

# ========================================= #
#^ Create a remote object from an information file ^#
# Load remote data from file into object
def loadRemote(filename):
    # Open file and read data
    with open(filename) as file:
        data = file.readlines()

    # Load all properties from file into dictionary
    remoteInfo = {}
    for line in data:
        propertyName, dataValue = line.split(":")
        remoteInfo[propertyName] = dataValue

    try:
        newRemote = Remote(remoteInfo["nickname"],eval(remoteInfo["protocol"])) # Create remote object from dictionary

        # Handle all buttons that were specified in the save
        for button in remoteInfo["buttons"].split("|"): # Different buttons separated by '|'
            if button != "":
                buttonDat = button.split(",") # Button information separated by commas
                newRemote.addButton(buttonDat[0],int(buttonDat[1]))
        
        return newRemote

    except KeyError:
        print("File Invalid! Not all properties present.")
    
    """Class to handle sending IR signals via GPIO."""
class Transmitter:
    """Class for transmitting IR signals using the NEC protocol."""
    
    def __init__(self, pin):
        """Initialize the transmitter with the specified GPIO pin."""
        self.transmitPin = pin
        GPIO.setup(self.transmitPin, GPIO.OUT)
    
    def sendSignal(self, raw_data):
        """Send an IR signal based on raw NEC data."""
        for (typ, duration) in raw_data:
            GPIO.output(self.transmitPin, GPIO.HIGH if typ == 1 else GPIO.LOW)
            sleep(duration / 1_000_000)  # Convert microseconds to seconds
        GPIO.output(self.transmitPin, GPIO.LOW)  # Ensure pin is low after transmission

    def cleanup(self):
        """Clean up GPIO settings."""
        GPIO.cleanup()