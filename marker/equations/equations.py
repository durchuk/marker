from marker.schema.bbox import rescale_bbox, expand_bbox, do_bboxes_overlap
from marker.schema.block import find_insert_block
from marker.settings import settings

def find_equation_blocks(page):
    equation_blocks = []
    equation_regions = [l.bbox for l in page.layout.bboxes if l.label in ["Formula"]]

    filtered_regions = []
    for eq in equation_regions:
        if not any(do_bboxes_overlap(eq, filtered_eq) for filtered_eq in filtered_regions):
            filtered_regions.append(eq)

    equation_regions = [expand_bbox(rescale_bbox(page.layout.image_bbox, page.bbox, b)) for b in filtered_regions]

    insert_points = {}
    for region_idx, region in enumerate(equation_regions):
        for block_idx, block in enumerate(page.blocks):
            for line_idx, line in enumerate(block.lines):
                if line.intersection_pct(region) > settings.BBOX_INTERSECTION_THRESH:
                    line.spans = []  # We will remove this line from the block

                    if region_idx not in insert_points:
                        insert_points[region_idx] = (block_idx, line_idx)

    # Account for regions with no detected lines
    for region_idx, region in enumerate(equation_regions):
        if region_idx in insert_points:
            continue

        insert_points[region_idx] = (find_insert_block(page.blocks, region), 0)

    for region_idx, equation_region in enumerate(equation_regions):
        equation_insert = insert_points[region_idx]
        equation_blocks.append([equation_insert[0], equation_insert[1], equation_region])

    return equation_blocks
