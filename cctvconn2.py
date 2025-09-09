import cv2

# Replace with actual credentials
rtsp_url = "rtsp://admin:admin%401966@192.168.100.112:554/cam/realmonitor?channel=4&subtype=0"

cap = cv2.VideoCapture(rtsp_url)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to connect to channel D4")
        break
    cv2.imshow("Dahua D4 Feed", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()