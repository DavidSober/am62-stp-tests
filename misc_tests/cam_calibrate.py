import numpy as np
import cv2
import glob
import os
class calibration:
    def __init__(self):
        self.chessboard_size = (9, 6)  # Number of internal corners
        self.calibration_folder = '/home/davidsober/Desktop/am62-stp-tests/misc_tests/calibration'
        self.cam1_folder = os.path.join(self.calibration_folder, 'camera1')
        os.makedirs(self.cam1_folder, exist_ok=True)
        self.cap1 = cv2.VideoCapture(4)
        self.cam1_matrix = None
        self.cam1_dist = None
        self.rvecs = None
        self.tvecs = None
        self.setup_calibration()
    def setup_calibration(self):
        print("HI")
        """Setup the calibration process"""
        need_capture = len(glob.glob(os.path.join(self.cam1_folder, '*.jpg'))) == 0
        if need_capture:
            print("No calibration images found. Starting capture process...")
            if not self.capture_images():
                raise Exception("Failed to capture calibration images")
        if not self.calibrate_camera():
            raise Exception("Calibration failed")
    def capture_images(self):
        if len(glob.glob(os.path.join(self.cam1_folder, '*.jpg'))) > 0:
            print("Calibration images already exist. Skipping capture.")
            return True
        print("Starting calibration image capture. Press 'c' to capture, 'q' to quit when done.")
        image_count = 0
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        while True:
            ret, frame = self.cap1.read()
            if not ret:
                print("Failed to grab frame")
                return False
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            ret, corners = cv2.findChessboardCorners(gray, self.chessboard_size, None)
            display_frame = frame.copy()
            if ret:
                corners2 = cv2.cornerSubPix(gray, corners, (11,11), (-1,-1), criteria)
                cv2.drawChessboardCorners(display_frame, self.chessboard_size, corners2, ret)
            cv2.putText(display_frame, f"Captures: {image_count}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow('Camera Calibration', display_frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c') and ret:
                cv2.imwrite(os.path.join(self.cam1_folder, f'cal_{image_count}.jpg'), frame)
                print(f"Saved calibration image {image_count}")
                image_count += 1
        cv2.destroyAllWindows()
        return image_count > 0
    def calibrate_camera(self):
        """Perform camera calibration using saved images"""
        objp = np.zeros((self.chessboard_size[0] * self.chessboard_size[1], 3), np.float32)
        objp[:, :2] = np.mgrid[0:self.chessboard_size[0], 0:self.chessboard_size[1]].T.reshape(-1, 2)
        objpoints = []
        imgpoints = []
        images = glob.glob(os.path.join(self.cam1_folder, '*.jpg'))
        if not images:
            print("No calibration images found!")
            return False
        for fname in sorted(images):
            img = cv2.imread(fname)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            ret, corners = cv2.findChessboardCorners(gray, self.chessboard_size, None)
            if ret:
                objpoints.append(objp)
                corners2 = cv2.cornerSubPix(gray, corners, (11,11), (-1,-1),
                                        (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))
                imgpoints.append(corners2)
                cv2.drawChessboardCorners(img, self.chessboard_size, corners2, ret)
                cv2.imshow("Calibration", img)
                #cv2.waitKey(500)
        cv2.destroyAllWindows()
        ret, self.cam1_matrix, self.cam1_dist, self.rvecs, self.tvecs = cv2.calibrateCamera(
            objpoints, imgpoints, gray.shape[::-1], None, None)
        if ret:
            print("Camera calibration completed")
        else:
            print("Camera calibration failed")
        return ret
    def undisort(self):
        image = cv2.imread('/home/davidsober/Desktop/am62-stp-tests/misc_tests/distorted/')
        h, w = image.shape[:2]
        newcameramtx, roi = cv2.getOptimalNewCameraMatrix(self.cam1_matrix, self.cam1_dist, (w,h), 1, (w,h))
        # undistort
        dst = cv2.undistort(image, self.cam1_matrix, self.cam1_dist, None, newcameramtx)
        # crop the image
        x, y, w, h = roi
        dst = dst[y:y+h, x:x+w]
        cv2.imwrite('/home/davidsober/Desktop/am62-stp-tests/misc_tests/distorted/cal_2.jpg', dst)
        print(f"Values: {self.cam1_matrix}")
    def draw(self, img, corners, imgpts):
        corner = tuple(corners[0].ravel().astype("int32"))
        imgpts = imgpts.astype("int32")
        img = cv2.line(img, corner, tuple(imgpts[0].ravel()), (255,0,0), 5)
        img = cv2.line(img, corner, tuple(imgpts[1].ravel()), (0,255,0), 5)
        img = cv2.line(img, corner, tuple(imgpts[2].ravel()), (0,0,255), 5)
        return img
    def cam_pose(self):
        vid = cv2.VideoCapture(0)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        objp = np.zeros((6*7,3), np.float32)
        objp[:,:2] = np.mgrid[0:7,0:6].T.reshape(-1,2)
        axis = np.float32([[3,0,0], [0,3,0], [0,0,-3]]).reshape(-1,3)
        while(True):
            ret, img = self.cap1.read()
            if not ret:
                print("Failed to grab frame")
                return False
            gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
            ret, corners = cv2.findChessboardCorners(gray, (7,6),None)
            if ret == True:
                print("CHESS")
                corners2 = cv2.cornerSubPix(gray,corners,(11,11),(-1,-1),criteria)
                # Find the rotation and translation vectors.
                ret,rvecs, tvecs = cv2.solvePnP(objp, corners2, self.cam1_matrix, self.cam1_dist)
                # project 3D points to image plane
                imgpts, jac = cv2.projectPoints(axis, rvecs, tvecs, self.cam1_matrix, self.cam1_dist)
                img = self.draw(img,corners2,imgpts)
            cv2.imshow('img', img)
            k = cv2.waitKey(1) & 0xFF
            if k == ord('q'):
                cv2.destroyAllWindows()
                break
def main():
    cali = calibration()
    cali.undisort()
    # cali.cam_pose()
if __name__ == "__main__":
    main()