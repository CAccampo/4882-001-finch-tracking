from PIL import Image
from pyzbar.pyzbar import decode
from pylibdmtx.pylibdmtx import decode as pyl_decode
import cv2 as cv
import numpy as np
import os
from matplotlib import pyplot as plt



qcd = cv.QRCodeDetector()

def count_detects(count, img, decoded_list, points, color):
    for code in decoded_list:
        count += 1
        img = cv.polylines(img, points, True, color, 8)
    return count
def flip_y(y, mid):
    return (mid-y)+mid

def calc_ocv_qr(img, ocv_count):
    #detect qr with opencv
    retval, ocv_decoded, points, _ = qcd.detectAndDecodeMulti(img)

    #draw box, add count
    if retval:
        return count_detects(ocv_count, img, ocv_decoded, np.int32(points), (255, 0, 0)) 

def calc_pyz_qr(img, pyz_count):
    #detect qr with pyzbar
    pyz_decoded = decode(img, pyz_count)

    #draw box, add count
    if pyz_decoded:
        points_pyz = []
        for i in range(0, len(pyz_decoded)):
            points_pyz += [np.array(pyz_decoded[i].polygon, np.int32)]
        return count_detects(pyz_count, img, pyz_decoded, points_pyz, (0, 255, 0))

def calc_pyl_dm(img, pyl_count):
    #detect dm; lower quality for faster processing
    pyl_decoded  = pyl_decode(img, shrink=3, threshold=6)
    
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
        return count_detects(pyl_count, img, pyl_decoded, points_pyl, (0, 0, 255))

def calc_aruco(img, aru_count):
    #setup dictionary and params
    aru_dict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_4X4_250)
    aru_params = cv.aruco.DetectorParameters()
    detector = cv.aruco.ArucoDetector(aru_dict, aru_params)

    #detect aruco markers
    aru_points, aru_decoded, rejected_marker = detector.detectMarkers(img)

    #draw box and add count
    if aru_decoded.any():
        return count_detects(aru_count, img, aru_decoded, np.int32(aru_points), (255,0,255))

def main():
    test_dir_name = 'Sprint3/img_test_dir'
    test_img = 'v3_far.jpg'
    img = cv.imread(os.path.join(test_dir_name, test_img))


    #blue opencv QR
    ocv_count = calc_ocv_qr(img, 0)
    #green pyzbar QR
    pyz_count = calc_pyz_qr(img, 0)
    #red pyl DataMatrix
    pyl_count = calc_pyl_dm(img, 0)
    #purple OpenCV ArUco marker
    aru_count = calc_aruco(img, 0)

    print(f'OCV (QR)\tPYZ (QR)\tPYL (DM)\tARU (MARK)')
    print(f'{ocv_count}\t\t{pyz_count}\t\t{pyl_count}\t\t{aru_count}')
    
    img = cv.resize(img, (960, 540))  
    cv.imshow("img",img)
    
    cv.waitKey(0)
    cv.destroyAllWindows()
main()
