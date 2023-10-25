from PIL import Image
from pyzbar.pyzbar import decode
from pylibdmtx.pylibdmtx import decode as pyl_decode
import cv2 as cv
import numpy as np
import os
import time


qcd = cv.QRCodeDetector()

def count_detects(img, decoded_list, points, color):
    count = 0
    for code in decoded_list:
        count += 1
        img = cv.polylines(img, points, True, color, 8)
    return count

def flip_y(y, mid):
    return (mid-y)+mid

def calc_ocv_qr(img):
    #detect qr with opencv
    detect_start = time.time()
    retval, ocv_decoded, points, _ = qcd.detectAndDecodeMulti(img)
    detect_end = time.time()
    tot_time = detect_end - detect_start

    #draw box, add count
    if retval:
        return tot_time, count_detects(img, ocv_decoded, np.int32(points), (255, 0, 0)) 
    return tot_time, 0

def calc_pyz_qr(img):
    #detect qr with pyzbar
    detect_start = time.time()
    pyz_decoded = decode(img)
    detect_end = time.time()
    tot_time = detect_end - detect_start

    #draw box, add count
    if pyz_decoded:
        points_pyz = []
        for i in range(0, len(pyz_decoded)):
            points_pyz += [np.array(pyz_decoded[i].polygon, np.int32)]
        return tot_time, count_detects(img, pyz_decoded, points_pyz, (0, 255, 0))
    return tot_time, 0

def calc_pyl_dm(img):
    #detect dm; lower quality for faster processing
    detect_start = time.time()
    pyl_decoded  = pyl_decode(img, shrink=3, threshold=6)
    detect_end = time.time()
    tot_time = detect_end - detect_start

    #format points, draw, add count
    if pyl_decoded:
        img_mid = img.shape[0]/2
        points_pyl = []
        for i in range(0, len(pyl_decoded)):
            left, top, width, height = pyl_decoded[i].rect
            top_left = [left, flip_y(top, img_mid)]
            btm_left = [left, flip_y(top + height, img_mid)]
            top_right = [left + width, flip_y(top, img_mid)]
            btm_right = [left + width, flip_y(top + height, img_mid)]
            points_pyl += [np.array([top_left, btm_left, btm_right, top_right], np.int32)]
        return tot_time, count_detects(img, pyl_decoded, points_pyl, (0, 0, 255))
    return tot_time, 0

def calc_aruco(img):
    #setup dictionary and params
    aru_dict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_4X4_250)
    aru_params = cv.aruco.DetectorParameters()
    detector = cv.aruco.ArucoDetector(aru_dict, aru_params)

    #detect aruco markers
    detect_start = time.time()
    aru_points, aru_decoded, rejected_marker = detector.detectMarkers(img)
    detect_end = time.time()
    tot_time = detect_end - detect_start

    #draw box and add count
    if aru_decoded.any():
        return tot_time, count_detects(img, aru_decoded, np.int32(aru_points), (255,0,255))
    return tot_time, 0

def main():
    test_dir_name = 'Sprint3/img_test_dir'
    test_img = 'v3_far.jpg'
    img = cv.imread(os.path.join(test_dir_name, test_img))


    #blue opencv QR
    ocv_time, ocv_count = calc_ocv_qr(img)
    #green pyzbar QR
    pyz_time, pyz_count = calc_pyz_qr(img)
    #red pyl DataMatrix
    pyl_time, pyl_count = calc_pyl_dm(img)
    #purple OpenCV ArUco marker
    aru_time, aru_count = calc_aruco(img)

    print(f'\t\tOCV (QR)\tPYZ (QR)\tPYL (DM)\tARU (MARK)')
    print(f'COUNT\t\t{ocv_count}\t\t{pyz_count}\t\t{pyl_count}\t\t{aru_count}')
    print('DUR (SEC)\t%.2f\t\t%.2f\t\t%.2f\t\t%.2f' % (ocv_time, pyz_time, pyl_time, aru_time))
    
    img = cv.resize(img, (960, 540))  
    cv.imshow("img",img)

    cv.waitKey(0)
    cv.destroyAllWindows()
main()
