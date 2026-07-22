import cv2


for i in range(5):

    cap=cv2.VideoCapture(
        i,
        cv2.CAP_DSHOW
    )


    if cap.isOpened():

        print(
            "摄像头编号:",
            i
        )

        cap.release()
