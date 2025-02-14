import cv2
import os

def encrypt_message(image_path, output_path, message, password):
    img = cv2.imread(image_path)
    
    if img is None:
        print("Error: Image not found!")
        return

    d = {chr(i): i for i in range(255)}

    n, m, z = 0, 0, 0

    for char in message:
        img[n, m, z] = d[char]
        n += 1
        m += 1
        z = (z + 1) % 3

    cv2.imwrite(output_path, img)
    print(f"Message encrypted successfully! Encrypted image saved as {output_path}")
    os.system(f"start {output_path}")


image_path = "mypic.jpg"
output_path = "encryptedImage.jpg"
message = input("Enter secret message: ")
password = input("Enter a passcode: ")

with open("password.txt", "w") as f:
    f.write(password)

encrypt_message(image_path, output_path, message, password)
