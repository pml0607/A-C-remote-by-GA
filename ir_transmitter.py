from pyIR import loadRemote

# Tải lại remote từ file đã lưu
my_remote = loadRemote('my_remote.txt')

# Giả sử bạn có lớp Transmitter để phát tín hiệu IR
transmitter = Transmitter(pin=12)

while True:
    # Nhận tên nút từ người dùng
    button_name = input("Enter the button name to send (or 'exit' to quit): ").strip()
    
    if button_name.lower() == 'exit':
        break
    
    # Tìm nút tương ứng với tên được nhập
    button = next((btn for btn in my_remote.buttons if btn.getNickname() == button_name), None)
    
    if button:
        # Gửi tín hiệu IR tương ứng với nút bấm
        transmitter.send(button.getIntegerCode())
        print(f"Sent IR signal for '{button_name}' with code {button.getHex()}.")
    else:
        print(f"No button found with the name '{button_name}'. Please try again.")
