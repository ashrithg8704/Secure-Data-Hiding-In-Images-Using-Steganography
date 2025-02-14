import cv2

def decrypt_message(image_path, password):
    img = cv2.imread(image_path)
    
    if img is None:
        print("Error: Encrypted image not found!")
        return

    c = {i: chr(i) for i in range(255)}

    try:
        with open("password.txt", "r") as f:
            correct_password = f.read().strip()
    except FileNotFoundError:
        print("Error: Password file not found!")
        return

    pas = input("Enter passcode for decryption: ")
    if password != correct_password:
        print("YOU ARE NOT AUTHORIZED")
        return

    message = ""
    n, m, z = 0, 0, 0

    try:
        while True:
            char = c[img[n, m, z]]
            if char == '\x00':
                break
            message += char
            n += 1
            m += 1
            z = (z + 1) % 3
    except KeyError:
        print("Decryption error: Invalid encoding")
        return

    print("Decryption successful! Secret message:", message)

image_path = "encryptedImage.jpg"

with open("password.txt", "r") as f:
    stored_password = f.read().strip()

decrypt_message(image_path, stored_password)
