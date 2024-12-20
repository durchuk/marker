from typing import List

from pydantic import BaseModel, field_validator


def should_merge_blocks(box1, box2, tol=5):
    # Within tol y px, and to the right within tol px
    merge = [
        box2[0] > box1[0], # After in the x coordinate
        abs(box2[1] - box1[1]) < tol, # Within tol y px
        abs(box2[3] - box1[3]) < tol, # Within tol y px
        abs(box2[0] - box1[2]) < tol, # Within tol x px
    ]
    return all(merge)


def merge_boxes(box1, box2):
    return (min(box1[0], box2[0]), min(box1[1], box2[1]), max(box2[2], box1[2]), max(box1[3], box2[3]))


def boxes_intersect(box1, box2):
    # Box1 intersects box2
    return box1[0] < box2[2] and box1[2] > box2[0] and box1[1] < box2[3] and box1[3] > box2[1]


def box_intersection_pct(box1, box2):
    # determine the coordinates of the intersection rectangle
    x_left = max(box1[0], box2[0])
    y_top = max(box1[1], box2[1])
    x_right = min(box1[2], box2[2])
    y_bottom = min(box1[3], box2[3])

    if x_right < x_left or y_bottom < y_top:
        return 0.0

    intersection_area = (x_right - x_left) * (y_bottom - y_top)
    bb1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])

    if bb1_area == 0:
        return 0.0
    iou = intersection_area / bb1_area
    return iou


def multiple_boxes_intersect(box1, boxes):
    for box2 in boxes:
        if boxes_intersect(box1, box2):
            return True
    return False


def unnormalize_box(bbox, width, height):
    return [
        width * (bbox[0] / 1000),
        height * (bbox[1] / 1000),
        width * (bbox[2] / 1000),
        height * (bbox[3] / 1000),
    ]


def get_center(bbox):
    return [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2]


class BboxElement(BaseModel):
    bbox: List[float]

    @field_validator('bbox')
    @classmethod
    def check_4_elements(cls, v: List[float]) -> List[float]:
        if len(v) != 4:
            raise ValueError('bbox must have 4 elements')
        return v

    @property
    def height(self):
        return self.bbox[3] - self.bbox[1]

    @property
    def width(self):
        return self.bbox[2] - self.bbox[0]

    @property
    def x_start(self):
        return self.bbox[0]

    @property
    def y_start(self):
        return self.bbox[1]

    @property
    def area(self):
        return self.width * self.height

    def intersection_pct(self, other_bbox: List[float]):
        if self.area == 0:
            return 0.0
        return box_intersection_pct(self.bbox, other_bbox)

    def distance(self, other_bbox: List[float]):
        bbox_center = get_center(self.bbox)
        other_center = get_center(other_bbox)
        return ((bbox_center[0] - other_center[0]) ** 2 + (bbox_center[1] - other_center[1]) ** 2) ** 0.5


def rescale_bbox(orig_dim, new_dim, bbox):
    page_width, page_height = new_dim[2] - new_dim[0], new_dim[3] - new_dim[1]
    detected_width, detected_height = orig_dim[2] - orig_dim[0], orig_dim[3] - orig_dim[1]
    width_scaler = detected_width / page_width
    height_scaler = detected_height / page_height

    new_bbox = [bbox[0] / width_scaler, bbox[1] / height_scaler, bbox[2] / width_scaler, bbox[3] / height_scaler]
    return new_bbox

def expand_bbox(bbox, expand_x=50, expand_y=15):
    x0, y0, x1, y1 = bbox
    return x0 - expand_x, y0 - expand_y, x1 + expand_x, y1 + expand_y

def do_bboxes_overlap(bbox1, bbox2):
    x0_1, y0_1, x1_1, y1_1 = bbox1
    x0_2, y0_2, x1_2, y1_2 = bbox2

    overlap_x = not (x1_1 < x0_2 or x1_2 < x0_1)
    overlap_y = not (y1_1 < y0_2 or y1_2 < y0_1)

    return overlap_x and overlap_y
