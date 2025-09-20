import cv2
cam = cv2.VideoCapture(0)

while True:
    b, img = cam.read()
    if b:
        cv2.imshow("Window", img)
        cv2.waitKey(1)
    else:
        print("The camera is not working.")
        break

cam.release()
cv2.destroyAllWindows()

