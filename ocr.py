from paddleocr import PaddleOCR,draw_ocr

ocr = PaddleOCR(use_angle_cls=True, lang='en') # need to run only once to download and load model into memory
img_path = '/projects/khanhnt/Vaseline_Drug_Facts.jpg' 
def get_iou(bb1, bb2):
    """
    Calculate the Intersection over Union (IoU) of two bounding boxes.

    Parameters
    ----------
    bb1 : dict
        Keys: {'x1', 'x2', 'y1', 'y2'}
        The (x1, y1) position is at the top left corner,
        the (x2, y2) position is at the bottom right corner
    bb2 : dict
        Keys: {'x1', 'x2', 'y1', 'y2'}
        The (x1, y1) position is at the top left corner,
        the (x2, y2) position is at the bottom right corner

    Returns
    -------
    float
        in [0, 1]
    """

    assert bb1['x1'] < bb1['x2']
    assert bb1['y1'] < bb1['y2']
    assert bb2['x1'] < bb2['x2']
    assert bb2['y1'] < bb2['y2']

    # determine the coordinates of the intersection rectangle
    x_left = max(bb1['x1'], bb2['x1'])
    y_top = max(bb1['y1'], bb2['y1'])
    x_right = min(bb1['x2'], bb2['x2'])
    y_bottom = min(bb1['y2'], bb2['y2'])

    if x_right < x_left or y_bottom < y_top:
        return 0.0

    # The intersection of two axis-aligned bounding boxes is always an
    # axis-aligned bounding box
    intersection_area = (x_right - x_left) * (y_bottom - y_top)

    # compute the area of both AABBs
    bb1_area = (bb1['x2'] - bb1['x1']) * (bb1['y2'] - bb1['y1'])
    bb2_area = (bb2['x2'] - bb2['x1']) * (bb2['y2'] - bb2['y1'])

    # compute the intersection over union by taking the intersection
    # area and dividing it by the sum of prediction + ground-truth
    # areas - the interesection area
    iou = intersection_area / float(bb1_area + bb2_area - intersection_area)
    assert iou >= 0.0
    assert iou <= 1.0
    return iou

def ocr_drug(img_path):
    predict = ocr.ocr(img_path, cls=True)
    dt_boxes, rec_res = [], []
    for line in predict[0]:
        dt_boxes.append(line[0])
        rec_res.append(line[1]) 
    results = []
    coodinates = []
    count = 1000000

    for i in range(len(rec_res)):
        try:
            # quantity = int(rec_res[i][0][0:-2])
            symbols = [z for z in rec_res[i][0]]
            assert len(symbols) < 9
            for j in range(len(symbols)):
                if (symbols[j] == 'm' and symbols[j+1] == 'g') or symbols[j] == '%':
                # if quantity <= 1000: # If the quantity is too large => it's not quantity but may be tax code, etc.
                    # print(quantity)
                    point1 = [dt_boxes[i][0][0],dt_boxes[i][0][1]]
                    # point2 = [dt_boxes[i][1][0],dt_boxes[i][1][1]]
                    # point3 = [dt_boxes[i][2][0],dt_boxes[i][2][1]]
                    point4 = [dt_boxes[i][3][0],dt_boxes[i][3][1]]
                    coodinates.append([point1, point4])


        except:
            pass
    if coodinates:
        for i in range(len(coodinates)):
            for j in range(len(dt_boxes)):
                if dt_boxes[j][1][0] < coodinates[i][0][0]:
                    bb1 = {'x1':0,'x2':coodinates[i][1][0],'y1':coodinates[i][0][1],'y2':coodinates[i][1][1]}
                    bb2 = {'x1':0,'x2':dt_boxes[j][2][0],'y1': dt_boxes[j][0][1],'y2': dt_boxes[j][2][1]}
                    iou = get_iou(bb1,bb2)
                    if iou >= 0.1:
                        index = j
                elif coodinates[i][0][1] > dt_boxes[j][3][1] and (coodinates[i][0][1] - dt_boxes[j][3][1] < count): 
                    count = coodinates[i][0][1] - dt_boxes[j][3][1]
                    index = j
                    # print(count, index, rec_res[index][0])
            results.append([dt_boxes[index],rec_res[index]])
        return results
        
    else:
        for i in range(len(rec_res)):
            try:
                if len(rec_res[i][0]) <= 50:
                    texts = rec_res[i][0]
                    for j in range(len(texts)):
                        if (texts[j] == 'm' and texts[j+1] == 'g') or texts[j] == '%':
                            results.append([dt_boxes[i],rec_res[i]])
            except:    
                pass
        return results

# result = ocr_drug(img_path)

# for i in result:
#     print("Day la ket qua",i)
# # # draw result
# from PIL import Image
# image = Image.open(img_path).convert('RGB')
# boxes = [line[0] for line in result]
# txts = [line[1][0] for line in result]
# scores = [line[1][1] for line in result]
# im_show = draw_ocr(image, boxes, txts, scores, font_path='/projects/khanhnt/PaddleOCR/StyleText/fonts/en_standard.ttf')
# im_show = Image.fromarray(im_show)
# im_show.save('/projects/khanhnt/anh_kq.jpg')
# print(boxes)