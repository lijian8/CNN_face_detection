import numpy as np
import cv2
import time
from operator import itemgetter
from load_model_functions import *
from face_detection_functions import *

# ==================  caffe  ======================================
caffe_root = '/home/anson/caffe-master/'  # this file is expected to be in {caffe_root}/examples
import sys
sys.path.insert(0, caffe_root + 'python')
import caffe
# ==================  load models  ======================================
net_12c_full_conv, net_12_cal, net_24c, net_24_cal, net_48c, net_48_cal = \
    load_face_models(signalQuantize=True)

def cal_face_12c(net_12_cal, caffe_img, rectangles):
    '''
    :param caffe_image: image in caffe style to detect faces
    :param rectangles:  rectangles in form [x11, y11, x12, y12, confidence, current_scale]
    :return:    rectangles after calibration
    '''

    height, width, channels = caffe_img.shape
    result = []
    for cur_rectangle in rectangles:

        original_x1 = cur_rectangle[0]
        original_y1 = cur_rectangle[1]
        original_x2 = cur_rectangle[2]
        original_y2 = cur_rectangle[3]
        original_w = original_x2 - original_x1
        original_h = original_y2 - original_y1

        cropped_caffe_img = caffe_img[original_y1:original_y2, original_x1:original_x2] # crop image

        caffe_img_resized = cv2.resize(cropped_caffe_img, (12, 12))
        caffe_img_resized_CHW = caffe_img_resized.transpose((2, 0, 1))
        net_12_cal.blobs['data'].reshape(1, *caffe_img_resized_CHW.shape)
        net_12_cal.blobs['data'].data[...] = caffe_img_resized_CHW
        net_12_cal.forward()
        output = net_12_cal.blobs['prob'].data

        # output = net_12_cal.predict([cropped_caffe_img])   # predict through caffe

        prediction = output[0]      # (44, 1) ndarray

        threshold = 0.1
        indices = np.nonzero(prediction > threshold)[0]   # ndarray of indices where prediction is larger than threshold

        number_of_cals = len(indices)   # number of calibrations larger than threshold

        if number_of_cals == 0:     # if no calibration is needed, check next rectangle
            result.append(cur_rectangle)
            continue

        total_s_change = 0
        total_x_change = 0
        total_y_change = 0

        for current_cal in range(number_of_cals):       # accumulate changes, and calculate average
            cal_label = int(indices[current_cal])   # should be number in 0~44
            if (cal_label >= 0) and (cal_label <= 8):       # decide s change
                total_s_change += 0.83
            elif (cal_label >= 9) and (cal_label <= 17):
                total_s_change += 0.91
            elif (cal_label >= 18) and (cal_label <= 26):
                total_s_change += 1.0
            elif (cal_label >= 27) and (cal_label <= 35):
                total_s_change += 1.10
            else:
                total_s_change += 1.21

            if cal_label % 9 <= 2:       # decide x change
                total_x_change += -0.17
            elif (cal_label % 9 >= 6) and (cal_label % 9 <= 8):     # ignore case when 3<=x<=5, since adding 0 doesn't change
                total_x_change += 0.17

            if cal_label % 3 == 0:       # decide y change
                total_y_change += -0.17
            elif cal_label % 3 == 2:     # ignore case when 1, since adding 0 doesn't change
                total_y_change += 0.17

        s_change = total_s_change / number_of_cals      # calculate average
        x_change = total_x_change / number_of_cals
        y_change = total_y_change / number_of_cals

        cur_result = cur_rectangle      # inherit format and last two attributes from original rectangle
        cur_result[0] = int(max(0, original_x1 - original_w * x_change / s_change))
        cur_result[1] = int(max(0, original_y1 - original_h * y_change / s_change))
        cur_result[2] = int(min(width, cur_result[0] + original_w / s_change))
        cur_result[3] = int(min(height, cur_result[1] + original_h / s_change))

        result.append(cur_result)

    result = sorted(result, key=itemgetter(4), reverse=True)    # sort rectangles according to confidence
                                                                        # reverse, so that it ranks from large to small
    return result
def detect_face_24c(net_24c, caffe_img, rectangles):
    '''
    :param caffe_img: image in caffe style to detect faces
    :param rectangles:  rectangles in form [x11, y11, x12, y12, confidence, current_scale]
    :return:    rectangles after calibration
    '''
    result = []
    for cur_rectangle in rectangles:

        x1 = cur_rectangle[0]
        y1 = cur_rectangle[1]
        x2 = cur_rectangle[2]
        y2 = cur_rectangle[3]

        cropped_caffe_img = caffe_img[y1:y2, x1:x2]     # crop image

        caffe_img_resized = cv2.resize(cropped_caffe_img, (24, 24))
        caffe_img_resized_CHW = caffe_img_resized.transpose((2, 0, 1))
        net_24c.blobs['data'].reshape(1, *caffe_img_resized_CHW.shape)
        net_24c.blobs['data'].data[...] = caffe_img_resized_CHW
        net_24c.forward()
        prediction = net_24c.blobs['prob'].data

        confidence = prediction[0][1]

        if confidence > 0.05:
            cur_rectangle[4] = confidence
            result.append(cur_rectangle)

    return result
def cal_face_24c(net_24_cal, caffe_img, rectangles):
    '''
    :param caffe_image: image in caffe style to detect faces
    :param rectangles:  rectangles in form [x11, y11, x12, y12, confidence, current_scale]
    :return:    rectangles after calibration
    '''
    height, width, channels = caffe_img.shape
    result = []
    for cur_rectangle in rectangles:

        original_x1 = cur_rectangle[0]
        original_y1 = cur_rectangle[1]
        original_x2 = cur_rectangle[2]
        original_y2 = cur_rectangle[3]
        original_w = original_x2 - original_x1
        original_h = original_y2 - original_y1

        cropped_caffe_img = caffe_img[original_y1:original_y2, original_x1:original_x2] # crop image

        caffe_img_resized = cv2.resize(cropped_caffe_img, (24, 24))
        caffe_img_resized_CHW = caffe_img_resized.transpose((2, 0, 1))
        net_24_cal.blobs['data'].reshape(1, *caffe_img_resized_CHW.shape)
        net_24_cal.blobs['data'].data[...] = caffe_img_resized_CHW
        net_24_cal.forward()
        output = net_24_cal.blobs['prob'].data

        prediction = output[0]      # (44, 1) ndarray

        threshold = 0.1
        indices = np.nonzero(prediction > threshold)[0]   # ndarray of indices where prediction is larger than threshold

        number_of_cals = len(indices)   # number of calibrations larger than threshold

        if number_of_cals == 0:     # if no calibration is needed, check next rectangle
            result.append(cur_rectangle)
            continue

        total_s_change = 0
        total_x_change = 0
        total_y_change = 0

        for current_cal in range(number_of_cals):       # accumulate changes, and calculate average
            cal_label = int(indices[current_cal])   # should be number in 0~44
            if (cal_label >= 0) and (cal_label <= 8):       # decide s change
                total_s_change += 0.83
            elif (cal_label >= 9) and (cal_label <= 17):
                total_s_change += 0.91
            elif (cal_label >= 18) and (cal_label <= 26):
                total_s_change += 1.0
            elif (cal_label >= 27) and (cal_label <= 35):
                total_s_change += 1.10
            else:
                total_s_change += 1.21

            if cal_label % 9 <= 2:       # decide x change
                total_x_change += -0.17
            elif (cal_label % 9 >= 6) and (cal_label % 9 <= 8):     # ignore case when 3<=x<=5, since adding 0 doesn't change
                total_x_change += 0.17

            if cal_label % 3 == 0:       # decide y change
                total_y_change += -0.17
            elif cal_label % 3 == 2:     # ignore case when 1, since adding 0 doesn't change
                total_y_change += 0.17

        s_change = total_s_change / number_of_cals      # calculate average
        x_change = total_x_change / number_of_cals
        y_change = total_y_change / number_of_cals

        cur_result = cur_rectangle      # inherit format and last two attributes from original rectangle
        cur_result[0] = int(max(0, original_x1 - original_w * x_change / s_change))
        cur_result[1] = int(max(0, original_y1 - original_h * y_change / s_change))
        cur_result[2] = int(min(width, cur_result[0] + original_w / s_change))
        cur_result[3] = int(min(height, cur_result[1] + original_h / s_change))

        result.append(cur_result)

    return result
def detect_face_48c(net_48c, caffe_img, rectangles):
    '''
    :param caffe_img: image in caffe style to detect faces
    :param rectangles:  rectangles in form [x11, y11, x12, y12, confidence, current_scale]
    :return:    rectangles after calibration
    '''
    result = []
    for cur_rectangle in rectangles:

        x1 = cur_rectangle[0]
        y1 = cur_rectangle[1]
        x2 = cur_rectangle[2]
        y2 = cur_rectangle[3]

        cropped_caffe_img = caffe_img[y1:y2, x1:x2]     # crop image

        caffe_img_resized = cv2.resize(cropped_caffe_img, (48, 48))
        caffe_img_resized_CHW = caffe_img_resized.transpose((2, 0, 1))
        net_48c.blobs['data'].reshape(1, *caffe_img_resized_CHW.shape)
        net_48c.blobs['data'].data[...] = caffe_img_resized_CHW
        net_48c.forward()
        prediction = net_48c.blobs['prob'].data

        confidence = prediction[0][1]

        if confidence > 0.1:
            cur_rectangle[4] = confidence
            result.append(cur_rectangle)

    result = sorted(result, key=itemgetter(4), reverse=True)    # sort rectangles according to confidence
                                                                        # reverse, so that it ranks from large to small
    return result
def cal_face_48c(net_48_cal, caffe_img, rectangles):
    '''
    :param caffe_image: image in caffe style to detect faces
    :param rectangles:  rectangles in form [x11, y11, x12, y12, confidence, current_scale]
    :return:    rectangles after calibration
    '''
    height, width, channels = caffe_img.shape
    result = []
    for cur_rectangle in rectangles:

        original_x1 = cur_rectangle[0]
        original_y1 = cur_rectangle[1]
        original_x2 = cur_rectangle[2]
        original_y2 = cur_rectangle[3]
        original_w = original_x2 - original_x1
        original_h = original_y2 - original_y1

        cropped_caffe_img = caffe_img[original_y1:original_y2, original_x1:original_x2] # crop image
        caffe_img_resized = cv2.resize(cropped_caffe_img, (48, 48))
        caffe_img_resized_CHW = caffe_img_resized.transpose((2, 0, 1))
        net_48_cal.blobs['data'].reshape(1, *caffe_img_resized_CHW.shape)
        net_48_cal.blobs['data'].data[...] = caffe_img_resized_CHW
        net_48_cal.forward()
        output = net_48_cal.blobs['prob'].data

        prediction = output[0]      # (44, 1) ndarray

        threshold = 0.1
        indices = np.nonzero(prediction > threshold)[0]   # ndarray of indices where prediction is larger than threshold

        number_of_cals = len(indices)   # number of calibrations larger than threshold

        if number_of_cals == 0:     # if no calibration is needed, check next rectangle
            result.append(cur_rectangle)
            continue

        total_s_change = 0
        total_x_change = 0
        total_y_change = 0

        for current_cal in range(number_of_cals):       # accumulate changes, and calculate average
            cal_label = int(indices[current_cal])   # should be number in 0~44
            if (cal_label >= 0) and (cal_label <= 8):       # decide s change
                total_s_change += 0.83
            elif (cal_label >= 9) and (cal_label <= 17):
                total_s_change += 0.91
            elif (cal_label >= 18) and (cal_label <= 26):
                total_s_change += 1.0
            elif (cal_label >= 27) and (cal_label <= 35):
                total_s_change += 1.10
            else:
                total_s_change += 1.21

            if cal_label % 9 <= 2:       # decide x change
                total_x_change += -0.17
            elif (cal_label % 9 >= 6) and (cal_label % 9 <= 8):     # ignore case when 3<=x<=5, since adding 0 doesn't change
                total_x_change += 0.17

            if cal_label % 3 == 0:       # decide y change
                total_y_change += -0.17
            elif cal_label % 3 == 2:     # ignore case when 1, since adding 0 doesn't change
                total_y_change += 0.17

        s_change = total_s_change / number_of_cals      # calculate average
        x_change = total_x_change / number_of_cals
        y_change = total_y_change / number_of_cals

        cur_result = cur_rectangle      # inherit format and last two attributes from original rectangle
        cur_result[0] = int(max(0, original_x1 - original_w * x_change / s_change))
        cur_result[1] = int(max(0, original_y1 - 1.1 * original_h * y_change / s_change))
        cur_result[2] = int(min(width, cur_result[0] + original_w / s_change))
        cur_result[3] = int(min(height, cur_result[1] + 1.1 * original_h / s_change))

        result.append(cur_result)

    return result


# ========================================================
total_time = 0
total_images = 0

# load and open files to read and write
for current_file in range(1, 11):

    print 'Processing file ' + str(current_file) + ' ...'

    read_file_name = './FDDB-fold/FDDB-fold-' + str(current_file).zfill(2) + '.txt'
    write_file_name = './detections/fold-' + str(current_file).zfill(2) + '-out.txt'
    write_file = open(write_file_name, "w")

    with open(read_file_name, "r") as ins:
        array = []
        for line in ins:
            array.append(line)      # list of strings

    number_of_images = len(array)

    for current_image in range(number_of_images):
        if current_image % 10 == 0:
            print 'Processing image : ' + str(current_image)
        # load image and convert to gray
        read_img_name = '/home/anson/FDDB/originalPics/' + array[current_image].rstrip() + '.jpg'
        img = cv2.imread(read_img_name)     # BGR

        min_face_size = 40
        stride = 5

        start = time.clock()

        img_forward = np.array(img, dtype=np.float32)
        img_forward -= np.array((104.00698793, 116.66876762, 122.67891434))

        rectangles = detect_face_12c(net_12c_full_conv, img_forward, min_face_size, stride, True)     # detect faces
        rectangles = cal_face_12c(net_12_cal, img_forward, rectangles)      # calibration
        rectangles = localNMS(rectangles)      # apply local NMS
        rectangles = detect_face_24c(net_24c, img_forward, rectangles)
        rectangles = cal_face_24c(net_24_cal, img_forward, rectangles)      # calibration
        rectangles = localNMS(rectangles)      # apply local NMS
        rectangles = detect_face_48c(net_48c, img_forward, rectangles)
        rectangles = globalNMS(rectangles)      # apply global NMS
        rectangles = cal_face_48c(net_48_cal, img_forward, rectangles)      # calibration

        end = time.clock()
        total_time += (end - start)
        total_images += 1

        number_of_faces = len(rectangles)
        # for rectangle in rectangles:    # draw rectangles
        #     cv2.rectangle(img, (rectangle[0], rectangle[1]), (rectangle[2], rectangle[3]), (255, 0, 0), 2)

        # write to file
        write_file.write(array[current_image])
        write_file.write("{}\n".format( str(number_of_faces) ) )
        for i in range(number_of_faces):
            write_file.write( "{} {} {} {} {}\n".format(str(rectangles[i][0]), str(rectangles[i][1]),
                                                        str(rectangles[i][2] - rectangles[i][0]),
                                                        str(rectangles[i][3] - rectangles[i][1]),
                                                        str(rectangles[i][4])))

    write_file.close()
    print 'Average time spent on one image : ' + str(total_time / total_images) + ' s'
