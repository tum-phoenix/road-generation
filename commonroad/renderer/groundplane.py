import cairo
# have to use pycairo instead of cairocffi as Rsvg bindings don't work with the latter
#import cairocffi as cairo
import math
from commonroad import utils
from os import path
import os
import hashlib
from tqdm import tqdm
import numpy as np
from enum import Enum
from collections import namedtuple
import gi
gi.require_version('Rsvg', '2.0')
from gi.repository import Rsvg

PIXEL_PER_UNIT = 500
TILE_SIZE = 2048
PADDING = 3


class MarkerImage(Enum):
    TURN_LEFT = 'commonroad/renderer/street_markings/Fahrbahnmarkierung_Pfeil_L.svg'
    TURN_RIGHT = 'commonroad/renderer/street_markings/Fahrbahnmarkierung_Pfeil_R.svg'

StreetMarking = namedtuple('StreetMarking', ['marker_image', 'marker_text', 'crossed'])


ROADMARKING_TYPE_TO_VISUAL = {
    "10_zone_beginn": StreetMarking(marker_image=None, marker_text='10', crossed=False),
    "20_zone_beginn": StreetMarking(marker_image=None, marker_text='20', crossed=False),
    "stvo-274.1": StreetMarking(marker_image=None, marker_text='30', crossed=False),
    "40_zone_beginn": StreetMarking(marker_image=None, marker_text='40', crossed=False),
    "50_zone_beginn": StreetMarking(marker_image=None, marker_text='50', crossed=False),
    "60_zone_beginn": StreetMarking(marker_image=None, marker_text='60', crossed=False),
    "70_zone_beginn": StreetMarking(marker_image=None, marker_text='70', crossed=False),
    "80_zone_beginn": StreetMarking(marker_image=None, marker_text='80', crossed=False),
    "90_zone_beginn": StreetMarking(marker_image=None, marker_text='90', crossed=False),
    "ende_10_zone": StreetMarking(marker_image=None, marker_text='10', crossed=True),
    "ende_20_zone": StreetMarking(marker_image=None, marker_text='20', crossed=True),
    "stvo-274.2": StreetMarking(marker_image=None, marker_text='30', crossed=True),
    "ende_40_zone": StreetMarking(marker_image=None, marker_text='40', crossed=True),
    "ende_50_zone": StreetMarking(marker_image=None, marker_text='50', crossed=True),
    "ende_60_zone": StreetMarking(marker_image=None, marker_text='60', crossed=True),
    "ende_70_zone": StreetMarking(marker_image=None, marker_text='70', crossed=True),
    "ende_80_zone": StreetMarking(marker_image=None, marker_text='80', crossed=True),
    "ende_90_zone": StreetMarking(marker_image=None, marker_text='90', crossed=True),
    "turn_left": StreetMarking(marker_image=MarkerImage.TURN_LEFT, marker_text=None, crossed=False),
    "turn_right": StreetMarking(marker_image=MarkerImage.TURN_RIGHT, marker_text=None, crossed=False),
}


def draw_boundary(ctx, boundary):
    if boundary.lineMarking is None:
        return
    ctx.set_line_width (0.02)
    if boundary.lineMarking == "dashed":
        ctx.set_dash([0.2, 0.2])
    else:
        ctx.set_dash([])

    ctx.move_to(boundary.point[0].x, boundary.point[0].y)
    for p in boundary.point[1:]:
        ctx.line_to(p.x, p.y)
    ctx.stroke()

def draw_stop_line(ctx, lanelet):
    ctx.save()
    p1 = lanelet.leftBoundary.point[-1]
    p2 = lanelet.rightBoundary.point[-1]

    if lanelet.stopLine:
        lineWidth = 0.04
        segmentLength = 0.08
        segmentGap = 0.06
        if lanelet.stopLine == "dashed":
            if lanelet.stopLineAttributes:
                lineWidth = lanelet.stopLineAttributes.lineWidth
                segmentLength = lanelet.stopLineAttributes.segmentLength
                segmentGap = lanelet.stopLineAttributes.segmentGap
            ctx.set_dash([segmentLength, segmentGap])
        else:
            ctx.set_dash([])
            ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        ctx.set_line_width(lineWidth)
        ctx.move_to(p1.x, p1.y)
        ctx.line_to(p2.x, p2.y)
        ctx.stroke()
    ctx.restore()

def draw_rectangle(ctx, rectangle):
    ctx.save()
    ctx.translate(rectangle.centerPoint.x, rectangle.centerPoint.y)
    ctx.rotate(-rectangle.orientation)
    ctx.rectangle(- rectangle.length / 2, - rectangle.width / 2,
        rectangle.length, rectangle.width)
    ctx.fill()
    ctx.restore()

def draw_circle(ctx, circle):
    ctx.arc(circle.centerPoint.x, circle.centerPoint.y, circle.radius, 0, 2*math.pi)
    ctx.fill()

def draw_polygon(ctx, polygon):
    ctx.move_to(polygon.point[0].x, polygon.point[1].y)
    for point in polygon.point[1:]:
        ctx.line_to(point.x, point.y)
    ctx.fill()

def draw_shape(ctx, shape):
    for rect in shape.rectangle:
        draw_rectangle(ctx, rect)
    for circ in shape.circle:
        draw_circle(ctx, circ)
    for poly in shape.polygon:
        draw_polygon(ctx, poly)

def draw_island_junction(ctx, island):
    ctx.save()
    ctx.set_dash([])
    ctx.set_line_width (0.02)
    for i in range(0, len(island.point), 2):
        ctx.move_to(island.point[i].x, island.point[i].y)
        ctx.line_to(island.point[i+1].x, island.point[i+1].y)
    ctx.stroke()
    ctx.restore()

def draw_road_marking(ctx, marking):
    marking_visual = ROADMARKING_TYPE_TO_VISUAL[marking.type]
    if marking_visual.marker_text:
        ctx.save()
        ctx.set_dash([])
        font = "DIN 1451 Std"
        font_size = 0.4
        text = '30'
        font_args = [cairo.FONT_SLANT_NORMAL]
        ctx.translate(marking.centerPoint.x, #- 0.145*math.cos(marking.orientation),
                      marking.centerPoint.y) #- 0.145*math.sin(marking.orientation))
        ctx.rotate(marking.orientation)
        # mirror text
        ctx.transform(cairo.Matrix(1.0, 0, 0, -1, 0, 0))
        ctx.translate(-0.145, 0.29)
        ctx.select_font_face(font, *font_args)
        ctx.set_font_size(font_size)
        ctx.text_path(marking_visual.marker_text)
        ctx.set_line_width(0.01)
        (x_bearing, y_bearing, text_width, text_height,
         x_advance, y_advance) = ctx.text_extents(text)
        ctx.fill_preserve()
        ctx.stroke()
        ctx.restore()
    if marking_visual.crossed:
        ctx.save()
        ctx.move_to(marking.centerPoint.x + 0.145 * math.cos(marking.orientation),
                    marking.centerPoint.y + 0.145 * math.sin(marking.orientation))
        ctx.line_to(marking.centerPoint.x + 0.145 * math.cos(marking.orientation)
                    - text_height * math.cos(marking.orientation) + text_width * math.sin(marking.orientation),
                    marking.centerPoint.y + 0.145 * math.sin(marking.orientation)
                    - text_height * math.sin(marking.orientation) - text_width * math.cos(marking.orientation))
        ctx.move_to(marking.centerPoint.x + (0.145 - text_height) * math.cos(marking.orientation),
                    marking.centerPoint.y + (0.145 - text_height) * math.sin(marking.orientation))
        ctx.line_to(marking.centerPoint.x + 0.145 * math.cos(marking.orientation)
                    + text_width * math.sin(marking.orientation),
                    marking.centerPoint.y + 0.145 * math.sin(marking.orientation)
                    - text_width * math.cos(marking.orientation))
        ctx.set_line_width(0.05)
        ctx.stroke()
        ctx.restore()

    if marking_visual.marker_image:
        ctx.save()
        handle = Rsvg.Handle()
        svg = handle.new_from_file(marking_visual.marker_image.value)
        ctx.translate(marking.centerPoint.x, marking.centerPoint.y)
        ctx.rotate(marking.orientation)
        ctx.scale(0.001, 0.001)
        svg.render_cairo(ctx)
        ctx.restore()


def draw_stripes_rect(ctx, rectangle):
    ctx.save()
    ctx.translate(rectangle.centerPoint.x, rectangle.centerPoint.y)
    ctx.rotate(-rectangle.orientation)

    ctx.set_line_width (0.02)
    sheering = rectangle.width / 2
    ctx.move_to(- rectangle.length / 2, - rectangle.width / 2)
    ctx.line_to(rectangle.length / 2, - rectangle.width / 2)
    ctx.line_to(rectangle.length / 2 - sheering, rectangle.width / 2)
    ctx.line_to(- rectangle.length / 2 + sheering, rectangle.width / 2)
    ctx.close_path()
    ctx.clip_preserve()
    ctx.stroke()

    start_x = - rectangle.length / 2 - rectangle.width
    end_x = rectangle.length / 2
    y_bottom = - rectangle.width / 2
    y_top = rectangle.width / 2
    ctx.set_line_width (0.02)
    for x in np.arange(start_x, end_x, 0.08):
        ctx.move_to(x, y_bottom)
        ctx.line_to(x + rectangle.width, y_top)
    ctx.stroke()

    ctx.restore()

def draw_zebra_crossing(ctx, lanelet):
    left = boundary_to_equi_distant(lanelet.leftBoundary, 0.04, 0.02)
    right = boundary_to_equi_distant(lanelet.rightBoundary, 0.04, 0.02)
    flag = True
    ctx.save()
    for (l, r) in zip(left, right):
        if flag:
            ctx.move_to(l[0], l[1])
            ctx.line_to(r[0], r[1])
            flag = False
        else:
            ctx.line_to(r[0], r[1])
            ctx.line_to(l[0], l[1])
            ctx.close_path()
            ctx.fill()
            flag = True
    ctx.restore()

def distance_points(p1, p2):
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    return math.sqrt(dx*dx + dy*dy)

def boundary_length(boundary):
    length = 0
    for (p1, p2) in zip(boundary.point, boundary.point[1:]):
        length += distance_points(p1, p2)
    return length

def boundary_point_lengths(boundary):
    result = [0]
    len = 0
    for (p1, p2) in zip(boundary.point, boundary.point[1:]):
        len += distance_points(p1, p2)
        result.append(len)
    return result

def boundary_to_equi_distant(boundary, step_width, offset):
    lengths = boundary_point_lengths(boundary)
    x = list(map(lambda p: p.x, boundary.point))
    y = list(map(lambda p: p.y, boundary.point))
    eval_marks = np.arange(offset, lengths[-1], step_width)
    xinterp = np.interp(eval_marks, lengths, x)
    yinterp = np.interp(eval_marks, lengths, y)
    return map(lambda i: (i[0],i[1]), zip(xinterp, yinterp))

def draw_obstacle(ctx, obstacle):
    if obstacle.type == "blockedArea":
        for rect in obstacle.shape.rectangle:
            draw_stripes_rect(ctx, rect)
    # uncomment if you want white boxes under the obstacles
    #else:
    #    draw_shape(ctx, obstacle.shape)

def draw_all_boundaries(ctx, lanelet_list, boundary_name):
    all_ids = [lanelet.id for lanelet in lanelet_list
        if getattr(lanelet, boundary_name).lineMarking is not None]
    while len(all_ids) > 0:
        current_id = all_ids[0]
        suc = expand_boundary(lanelet_list, get_lanelet_by_id(lanelet_list, current_id), boundary_name, "successor")
        pred = expand_boundary(lanelet_list, get_lanelet_by_id(lanelet_list, current_id), boundary_name, "predecessor")
        ids_in_run = pred[::-1] + [current_id] + suc

        for id in ids_in_run:
            all_ids.remove(id)

        lanelets = list(map(lambda x: get_lanelet_by_id(lanelet_list, x), ids_in_run))

        ctx.save()
        ctx.set_line_width (0.02)
        line_marking = getattr(lanelets[0], boundary_name).lineMarking
        if line_marking == "dashed":
            ctx.set_dash([0.2, 0.2])
        elif line_marking == "solid" :
            ctx.set_dash([])

        ctx.move_to(getattr(lanelets[0], boundary_name).point[0].x,
            getattr(lanelets[0], boundary_name).point[0].y)

        for lanelet in lanelets:
            for p in getattr(lanelet, boundary_name).point:
                ctx.line_to(p.x, p.y)
        ctx.stroke()
        ctx.restore()

def get_lanelet_by_id(lanelet_list, id):
    for lanelet in lanelet_list:
        if lanelet.id == id:
            return lanelet
    return None

def expand_boundary(lanelet_list, lanelet, boundary_name, direction):
    ids = []
    original_line_type = getattr(lanelet, boundary_name).lineMarking
    found = True
    while found:
        found = False
        if getattr(lanelet, direction) is not None:
            for next in getattr(lanelet, direction).lanelet:
                next_lanelet = get_lanelet_by_id(lanelet_list, next.ref)
                if getattr(next_lanelet, boundary_name).lineMarking == original_line_type:
                    lanelet = next_lanelet
                    ids.append(lanelet.id)
                    found = True
                    break
    return ids

def draw(doc, target_dir):
    bounding_box = utils.get_bounding_box(doc)
    bounding_box.x_min -= PADDING
    bounding_box.y_min -= PADDING
    bounding_box.x_max += PADDING
    bounding_box.y_max += PADDING

    width = math.ceil((bounding_box.x_max - bounding_box.x_min) * PIXEL_PER_UNIT)
    height = math.ceil((bounding_box.y_max - bounding_box.y_min) * PIXEL_PER_UNIT)

    width_num = math.ceil(width / TILE_SIZE)
    height_num = math.ceil(height / TILE_SIZE)

    os.makedirs(path.join(target_dir, "materials", "textures"), exist_ok=True)
    os.makedirs(path.join(target_dir, "materials", "scripts"), exist_ok=True)

    models = ""

    for (x, y) in tqdm([(x,y) for x in range(width_num) for y in range(height_num)]):
        surface = cairo.ImageSurface(cairo.FORMAT_RGB24, TILE_SIZE, TILE_SIZE)
        ctx = cairo.Context(surface)

        # fill black
        ctx.set_source_rgb(0, 0, 0)
        ctx.rectangle(0, 0, TILE_SIZE, TILE_SIZE)
        ctx.fill()

        # Inverse y-axis
        ctx.translate(0, TILE_SIZE / 2)
        ctx.scale(1, -1)
        ctx.translate(0, -TILE_SIZE / 2)

        ctx.scale(PIXEL_PER_UNIT, PIXEL_PER_UNIT)
        ctx.translate(-bounding_box.x_min, -bounding_box.y_min)
        ctx.translate(- x * TILE_SIZE / PIXEL_PER_UNIT, - y * TILE_SIZE / PIXEL_PER_UNIT)

        ctx.set_source_rgb(1, 1, 1)
        for lanelet in doc.lanelet:
            draw_stop_line(ctx, lanelet)
            if lanelet.type == "zebraCrossing":
                draw_zebra_crossing(ctx, lanelet)
            #draw_boundary(ctx, lanelet.leftBoundary)
            #draw_boundary(ctx, lanelet.rightBoundary)

        draw_all_boundaries(ctx, doc.lanelet, "leftBoundary")
        draw_all_boundaries(ctx, doc.lanelet, "rightBoundary")

        for obstacle in doc.obstacle:
            draw_obstacle(ctx, obstacle)

        for island_junction in doc.islandJunction:
            draw_island_junction(ctx, island_junction)

        for road_marking in doc.roadMarking:
            draw_road_marking(ctx, road_marking)

        sha_256 = hashlib.sha256()
        sha_256.update(surface.get_data())
        hash = sha_256.hexdigest()

        texture_file = "tile-{0}.png".format(hash)
        material_file = "tile-{0}.material".format(hash)
        surface.write_to_png(
            path.join(target_dir, "materials", "textures", texture_file))

        with open(path.join(target_dir, "materials", "scripts", material_file), "w") as file:
            file.write(ground_plane_material("Tile/" + hash, texture_file))

        models += ground_plane_model(
            bounding_box.x_min + (x + 0.5) * TILE_SIZE / PIXEL_PER_UNIT,
            bounding_box.y_min + (y + 0.5) * TILE_SIZE / PIXEL_PER_UNIT,
            TILE_SIZE / PIXEL_PER_UNIT,
            "Tile/{0}-{1}".format(x, y),
            "Tile/" + hash)

    return models

def ground_plane_material(name, file):
    return """
    material {name}
    {{
        technique
        {{
            pass
            {{
                texture_unit
                {{
                    texture {file} PF_L8
                    filtering anisotropic
                    max_anisotropy 16
                }}
            }}
        }}
    }}
    """.format(name=name, file=file)

def ground_plane_model(x, y, tile_size, name, material):
    return """
    <model name='{name}'>
      <static>1</static>
      <link name='link'>
        <collision name='collision'>
          <geometry>
            <plane>
              <normal>0 0 1</normal>
              <size>{tile_size} {tile_size}</size>
            </plane>
          </geometry>
          <surface>
            <friction>
              <ode>
                <mu>100</mu>
                <mu2>50</mu2>
              </ode>
              <torsional>
                <ode/>
              </torsional>
            </friction>
            <contact>
              <ode/>
            </contact>
            <bounce/>
          </surface>
          <max_contacts>10</max_contacts>
        </collision>
        <visual name='visual'>
          <cast_shadows>0</cast_shadows>
          <geometry>
            <plane>
              <normal>0 0 1</normal>
              <size>{tile_size} {tile_size}</size>
            </plane>
          </geometry>
          <material>
            <script>
              <uri>file://materials/scripts</uri>
              <uri>file://materials/textures</uri>
              <name>{material}</name>
            </script>
          </material>
        </visual>
        <self_collide>0</self_collide>
        <enable_wind>0</enable_wind>
        <kinematic>0</kinematic>
      </link>
      <pose frame=''>{x} {y} 0 0 -0 0</pose>
    </model>
    """.format(x=x, y=y, tile_size=tile_size, name=name, material=material)
