from enum import Enum, auto

import cv2
import numpy as np
from PIL import Image, ImageDraw

def test(path):
    img = cv2.imread(path)
    annotated_img = img.copy()
    h, w = img.shape[:2]

    cv2.circle(annotated_img, (90, 120), 3, (255, 0, 0), thickness=-1)
    cv2.circle(annotated_img, (170, 200), 3, (255, 0, 0), thickness=-1)
    # mat_img = cv2.addWeighted(annotated_img, 0.4, img, 0.6, 0)
    # cv2.imshow('output', mat_img)
    # cv2.imshow('output', annotated_img)
    # cv2.waitKey(0)
    # cv2.destroyWindow()
    cv2.imwrite('otuput.png', annotated_img)
    

def test2(path):
    org = cv2.imread('image16_20241104110542.png')
    org_rgba = cv2.cvtColor(org, cv2.COLOR_BGR2BGRA)
    src = cv2.imread(path)
    dst = cv2.cvtColor(src, cv2.COLOR_BGR2BGRA)

    for i in range(257):
        for j in range(257):
            arr = dst[i, j]
            if arr[0] == 255 and arr[1] == 0 and arr[2] == 0:
                org_rgba[i, j][3] = 50
    
    cv2.imwrite('output3.png', org_rgba)


def test3(path):
    im_bgr = cv2.imread(path)
    im_rgb = im_bgr[:, :, ::-1]

    # add_arr = np.array([255] * 257 * 257).reshape(257, 257, 1)
    # arr = np.appens(im_rgb, add_arr, axis=2)

    arr = np.insert(im_rgb, 3, 255, axis=2)
    img = Image.fromarray(arr)


    # img = Image.open(path)
    draw = ImageDraw.Draw(img)

    draw.ellipse((90, 120, 95, 125), fill=(255, 0, 0))
    draw.ellipse((100, 140, 110, 150), fill=(255, 0, 0))
    img = np.array(img)

    for i in range(257):
        for j in range(257):
            temp = img[i, j]
            if temp[0] == 255 and temp[1] == 0 and temp[2] == 0:
                arr[i, j][3] = 50

    Image.fromarray(arr).save('draw_4.png', quality=90)


def add_alpha(output_name, org_img, src_img, alpha=50):
    org_bgr = cv2.imread(org_img)
    src_bgr = cv2.imread(src_img)
    org_bgra = np.insert(org_bgr, 3, 255, axis=2)

    for i in range(129):
        for j in range(129):
            arr = src_bgr[i, j]
            # if arr[0] == 0 and arr[1] == 255 and arr[2] == 0:
            if arr[0] == 0 and arr[1] == 0 and arr[2] == 255:
                org_bgra[i, j][3] = alpha
                # src_bgr[i, j] = org_bgr[i, j] 

    cv2.imwrite(output_name, org_bgra)
    # cv2.imwrite(output_name, src_bgr)


def del_shape(output_name, org_img, src_img):
    org_bgr = cv2.imread(org_img)
    src_bgr = cv2.imread(src_img)
    # org_bgra = np.insert(org_bgr, 3, 255, axis=2)

    for i in range(129):
        for j in range(129):
            arr = src_bgr[i, j]
            if arr[0] == 255 and arr[1] == 0 and arr[2] == 0:
            # if arr[0] == 237 and arr[1] == 36 and arr[2] == 28:
                # org_bgra[i, j][3] = alpha
                src_bgr[i, j] = org_bgr[i, j] 

    # cv2.imwrite(output_name, org_bgra)
    cv2.imwrite(output_name, src_bgr)


def get_coords(path):
    def mouse_event(event, x, y, flags, param):
        print(event, x, y, flags, param)
        if event == cv2.EVENT_LBUTTONUP:
            print(f'x: {x}, y: {y}')
            cv2.circle(img, (x, y), 5, (255, 0, 0), -1)

    img = cv2.imread(path)
    cv2.namedWindow("window", cv2.WINDOW_KEEPRATIO)
    ("window", mouse_event)

    while True:
        cv2.imshow("window", img)
        if cv2.waitKey(1) & 0xFF == ord("z"):
            break

    cv2.destroyAllWindows()


class DrawShape:

    def __init__(self, img):
        self.img = img
        self.ix = None
        self.iy = None
        # True if mouse if pressed.
        self.drawing = False
        # If True, draw circle. Press 'm' to toggle to rectangle.
        self.mode = True
        self.center_x = None
        self.center_y = None
        self.radius = 0

    def draw(self, event, x, y, flags, param):
        match event:
            case cv2.EVENT_LBUTTONDOWN:
                self.radius = 1  # 3
                self.drawing = True
                self.ix = x
                self.iy = y

            case cv2.EVENT_MOUSEMOVE:
                if self.drawing:
                    if self.mode:
                        pass
                        # cv2.circle(self.img, (x, y), self.radius, (255, 0, 0), -1)
                        # cv2.circle(self.img, (self.ix, self.iy), self.radius, (0, 255, 0), -1)
                    else:
                        cv2.rectangle(self.img, (self.ix, self.iy), (x, y), (0, 255, 0), -1)

            case cv2.EVENT_LBUTTONUP:
                self.drawing = False
                if not self.drawing:
                    if self.mode:
                        # cv2.circle(self.img, (x, y), self.radius, (0, 0, 255), -1)
                        cv2.circle(self.img, (x, y), self.radius, (0, 255, 0), -1)
                        # cv2.circle(self.img, (x, y), self.radius, (255, 0, 0), -1)
                        # アンチエイリアスあり
                        # cv2.circle(self.img, (x, y), self.radius, (0, 255, 0), cv2.FILLED, lineType=cv2.LINE_AA)
                        # cv2.circle(self.img, (x, y), self.radius, (255, 0, 0), 5, lineType=cv2.LINE_AA)

                       
                        self.center_x = x
                        self.center_y = y
                        print(f'center_x: {self.center_x}, center_y: {self.center_y}')
                    else:
                        cv2.rectangle(self.img, (self.ix, self.iy), (x, y), (0, 255, 0), -1)

    def increment_radius(self):
        if self.mode:
            # cv2.circle(self.img, (self.center_x, self.center_y), self.radius, (0, 0, 255), -1)
            cv2.circle(self.img, (self.center_x, self.center_y), self.radius, (0, 255, 0), -1)
            # cv2.circle(self.img, (self.center_x, self.center_y), self.radius, (255, 0, 0), -1)
            # cv2.circle(self.img, (self.center_x, self.center_y), self.radius, (0, 255, 0), cv2.FILLED, lineType=cv2.LINE_AA)
            # cv2.circle(self.img, (self.center_x, self.center_y), self.radius, (255, 0, 0), 5, lineType=cv2.LINE_AA)
            self.radius += 1


def draw_shape(path, output_file):
    # def mouse_event(event, x, y, flags, param):
    #     print(event, x, y, flags, param)
    #     if event == cv2.EVENT_LBUTTONUP:
    #         print(f'x: {x}, y: {y}')
    #         cv2.circle(img, (x, y), 5, (255, 0, 0), -1)

    img = cv2.imread(path)
    drawer = DrawShape(img)
    cv2.namedWindow("window", cv2.WINDOW_KEEPRATIO)
    cv2.setMouseCallback("window", drawer.draw)

    while True:
        cv2.imshow("window", img)

        match cv2.waitKey(1) & 0xFF:
            case 122:   # ord('z'):
                break
            case 109:   # ord('m'):
                drawer.mode = not drawer.mode
            case 97:   # ord('a')
                drawer.increment_radius()

    cv2.imwrite(output_file, img)
    cv2.destroyAllWindows()



def overlay(org_path, src_path):
    org_bgr = cv2.imread(org_path)
    org_rgb = org_bgr[:, :, ::-1]

    src_bgr = cv2.imread(src_path)
    src_rgb = src_bgr[:, :, ::-1]

    result = src_rgb * 0.5 + org_rgb * 0.5

    # org_rgb = org_rgb / 255
    # src_rgb = src_rgb / 255
    # # import pdb; pdb.set_trace()
    # result = np.zeros(org_rgb.shape)
    # dark = org_rgb < 0.5
    # org_inverse = 1 - org_rgb
    # src_inverse = 1 - src_rgb

    # result[dark] = org_rgb[dark] * src_rgb[dark] * 2
    # result[~dark] = 1 - org_inverse[~dark] * src_inverse[~dark] * 2

    # result = result.clip(0, 1)
    cv2.imwrite('result.png', result)


def inverse(img_path):
    img = cv2.imread(img_path)
    img = 255 - img
    cv2.imwrite('inverse.png', img)



if __name__ == '__main__':
    # test('image16_20241104110542.png')
    # test2('output.png')
    # test3('image8_1.png')
    # get_coords('image8_1.png')
    # draw_shape('top_terrain_src_new200.png', 'top_terrain_src_new200.png')
    # del_shape('top_terrain_src_new200.png', 'top_terrain_org.png', 'top_terrain_src_new2.png')
    add_alpha('mid_terrain.png', 'mid_terrain_org.png', 'top_ground_src2.png', alpha=50)
    # overlay('image16_20241108221215.png', 'image16_20241108221228.png')
    # inverse('image8_cellular.png')