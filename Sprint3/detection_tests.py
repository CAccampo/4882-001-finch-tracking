from PIL import Image
from pyzbar.pyzbar import decode
from pylibdmtx.pylibdmtx import decode as pyl_decode
import cv2 as cv
import numpy as np
import os
from matplotlib import pyplot as plt



qcd = cv.QRCodeDetector()
test_dir_name = 'img_test_dir'
test_dir = os.listdir(test_dir_name)
test_img = 'v3_far.jpg'

def count_detects(count, img, decoded_list, points, color):
    for code in decoded_list:
        count += 1
        img = cv.polylines(img, points, True, color, 8)
    return count
def flip_y(y, mid):
    return (mid-y)+mid

def main():
    pyz_count, ocv_count, pyl_count, aru_count = 0, 0, 0, 0
    img = cv.imread(os.path.join(test_dir_name, test_img))

    retval, ocv_decoded, points, _ = qcd.detectAndDecodeMulti(img)
    pyz_decoded = decode(img)
    pyl_decoded  = pyl_decode(img, shrink=3, threshold=6)

    aru_dict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_4X4_250)
    aru_params = cv.aruco.DetectorParameters()
    detector = cv.aruco.ArucoDetector(aru_dict, aru_params)
    aru_points, aru_decoded, rejected_marker = detector.detectMarkers(img)

    #blue opencv QR
    if retval:
        ocv_count = count_detects(ocv_count, img, ocv_decoded, np.int32(points), (255, 0, 0)) 
    #green pyzbar QR
    if pyz_decoded:
        points_pyz = []
        for i in range(0, len(pyz_decoded)):
            points_pyz += [np.array(pyz_decoded[i].polygon, np.int32)]
        pyz_count = count_detects(pyz_count, img, pyz_decoded, points_pyz, (0, 255, 0))
    #red pyl DataMatrix
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
        pyl_count = count_detects(pyl_count, img, pyl_decoded, points_pyl, (0, 0, 255))
    #purple OpenCV ArUco marker
    if aru_decoded.any():
        aru_count = count_detects(aru_count, img, aru_decoded, np.int32(aru_points), (255,0,255))

    print(f'OCV (QR)\tPYZ (QR)\tPYL (DM)\tARU (MARK)')
    print(f'{ocv_count}\t\t{pyz_count}\t\t{pyl_count}\t\t{aru_count}')
    img = cv.resize(img, (960, 540))  
    cv.imshow("img",img)
    cv.waitKey(0)
    cv.destroyAllWindows()
main()
