#!/usr/bin/env python3
import sys
import argparse
import json
import xml.etree.ElementTree as ET
import re
import math
PROD= 1
OFF=15.0*PROD

# Geometry helpers for clearance
def rect_distance(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    dx = max(bx - (ax + aw), ax - (bx + bw), 0.0)
    dy = max(by - (ay + ah), ay - (by + bh), 0.0)
    if dx == 0.0 and dy == 0.0:
        return 0.0
    return math.hypot(dx, dy)

def point_rect_distance(px, py, r):
    rx, ry, rw, rh = r
    cx = min(max(px, rx), rx + rw)
    cy = min(max(py, ry), ry + rh)
    return math.hypot(px - cx, py - cy)

def rect_clearance_ok(rect, boxes, min_clear, ignore_ids=None):
    if ignore_ids is None:
        ignore_ids = set()
    for b in boxes:
        if b['id'] in ignore_ids:
            continue
        if rect_distance(rect, b['bbox']) < min_clear:
            return False
    return True

def point_clearance_ok(px, py, boxes, min_clear, ignore_ids=None):
    if ignore_ids is None:
        ignore_ids = set()
    for b in boxes:
        if b['id'] in ignore_ids:
            continue
        if point_rect_distance(px, py, b['bbox']) < min_clear:
            return False
    return True


def parse_svg_file(file_path):
    """Parse SVG file and extract flowchart nodes."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse XML
    root = ET.fromstring(content)

    # Remove namespace prefix for easier parsing
    for elem in root.iter():
        if elem.tag.startswith('{'):
            elem.tag = elem.tag.split('}', 1)[1]

    return content, root

def find_nodes_section(root):
    """Find the nodes section in the Mermaid SVG."""
    # Look for g elements with class="nodes" or containing nodes
    for g in root.findall('.//g'):
        class_attr = g.get('class', '')
        if 'nodes' in class_attr:
            return g

    # Alternative: look for g elements that contain node groups
    for g in root.findall('.//g'):
        child_groups = g.findall('g[@data-id]')
        if len(child_groups) > 3:  # If it contains multiple node groups
            return g

    return None

def extract_node_info_from_content(content):
    """Extract node information directly from SVG content using regex, accounting for group transforms."""
    nodes = []

    # Pattern to find node groups with data-id and data-et="node" (capture the opening tag attrs for transform)
    node_pattern = r'<g(?P<attrs>[^>]*)\bdata-id="(id\d+[a-z]*)"[^>]*\bdata-et="node"[^>]*>'
    node_matches = re.finditer(node_pattern, content)

    for match in node_matches:
        tag_open = match.group(0)
        attrs = match.group('attrs') if 'attrs' in match.groupdict() else ''
        node_id = match.group(2)
        # Parse translate(...) from the group transform, if present (search whole opening tag)
        tx = ty = 0.0
        tmatch = re.search(r'transform="translate\(([^,\)]+),\s*([^\)]+)\)"', tag_open)
        if tmatch:
            try:
                tx = float(tmatch.group(1))
                ty = float(tmatch.group(2))
            except ValueError:
                tx = ty = 0.0

        start_pos = match.end()

        # Find the end of this group
        depth = 1
        pos = start_pos
        while depth > 0 and pos < len(content):
            if content[pos:pos+3] == '<g ':
                depth += 1
            elif content[pos:pos+4] == '</g>':
                depth -= 1
            pos += 1

        if depth == 0:
            node_content = content[start_pos:pos-4]

            # Extract rect/shape information (add group translate)
            rect_match = re.search(r'<rect[^>]+x="([^"]+)"[^>]+y="([^"]+)"[^>]+width="([^"]+)"[^>]+height="([^"]+)"', node_content)
            if rect_match:
                x, y, width, height = map(float, rect_match.groups())
                # Optional rect-local translate transform inside the node group
                r_t = re.search(r'<rect[^>]*transform="translate\(([^,\)]+),\s*([^\)]+)\)"', node_content)
                rtx = rty = 0.0
                if r_t:
                    try:
                        rtx = float(r_t.group(1))
                        rty = float(r_t.group(2))
                    except ValueError:
                        rtx = rty = 0.0
                ax = x + tx + rtx
                ay = y + ty + rty
                nodes.append({
                    'id': node_id,
                    'x': ax, 'y': ay, 'width': width, 'height': height,
                    'cx': ax + width/2, 'cy': ay + height/2
                })
                continue

            # Extract circle information
            circle_match = re.search(r'<circle[^>]+cx="([^"]+)"[^>]+cy="([^"]+)"[^>]+r="([^"]+)"', node_content)
            if circle_match:
                cx, cy, r = map(float, circle_match.groups())
                # Optional circle-local translate transform
                c_t = re.search(r'<circle[^>]*transform="translate\(([^,\)]+),\s*([^\)]+)\)"', node_content)
                ctx = cty = 0.0
                if c_t:
                    try:
                        ctx = float(c_t.group(1))
                        cty = float(c_t.group(2))
                    except ValueError:
                        ctx = cty = 0.0
                acx = cx + tx + ctx
                acy = cy + ty + cty
                nodes.append({
                    'id': node_id,
                    'x': acx - r, 'y': acy - r, 'width': 2*r, 'height': 2*r,
                    'cx': acx, 'cy': acy
                })
                continue

            # Extract polygon information (for diamonds, hexagons)
            polygon_match = re.search(r'<polygon[^>]+points="([^"]+)"', node_content)
            if polygon_match:
                points_str = polygon_match.group(1)
                # Optional polygon-local translate transform (common for diamonds)
                p_t = re.search(r'<polygon[^>]*transform="translate\(([^,\)]+),\s*([^\)]+)\)"', node_content)
                ptx = pty = 0.0
                if p_t:
                    try:
                        ptx = float(p_t.group(1))
                        pty = float(p_t.group(2))
                    except ValueError:
                        ptx = pty = 0.0

                points = []
                coords = points_str.replace(',', ' ').split()
                for i in range(0, len(coords), 2):
                    if i + 1 < len(coords):
                        px = float(coords[i]) + tx + ptx
                        py = float(coords[i+1]) + ty + pty
                        points.append((px, py))

                if points:
                    xs = [p[0] for p in points]
                    ys = [p[1] for p in points]
                    x_min, x_max = min(xs), max(xs)
                    y_min, y_max = min(ys), max(ys)
                    nodes.append({
                        'id': node_id,
                        'x': x_min, 'y': y_min, 'width': x_max-x_min, 'height': y_max-y_min,
                        'cx': (x_min+x_max)/2, 'cy': (y_min+y_max)/2
                    })

    return nodes

def create_subtle_leader_line(start_x, start_y, end_x, end_y):
    """Create a patent-style S-shaped leader line using 1/3 and 2/3 control points with ±15px perpendicular offsets."""
    dx = end_x - start_x
    dy = end_y - start_y

    # Control points at 1/3 and 2/3 along the main vector
    c1x = start_x + dx / 3.0
    c1y = start_y + dy / 3.0
    c2x = start_x + 2.0 * dx / 3.0
    c2y = start_y + 2.0 * dy / 3.0

    # Perpendicular unit vector
    perp_x = -dy
    perp_y = dx
    length = math.hypot(perp_x, perp_y)
    if length > 0:
        perp_x /= length
        perp_y /= length

    # Apply ±15px offsets to produce S-curve that flows toward numerals
    offset = OFF
    c1x += perp_x * offset
    c1y += perp_y * offset
    c2x -= perp_x * offset
    c2y -= perp_y * offset

    return f"M {start_x:.1f} {start_y:.1f} C {c1x:.1f} {c1y:.1f} {c2x:.1f} {c2y:.1f} {end_x:.1f} {end_y:.1f}"

def load_special_overrides(json_file=None):
    """Load special overrides from JSON file if provided, otherwise return defaults."""
    default_overrides = {
        '512b': {
            'force_side': 'right',
            'curve_width': 32.0
        },
        '506': {
            'force_side': 'right',
            'curve_width': 30.0
        },
        '209': {
            'force_side': 'right',
            'curve_width': 80
        },
        '203': {
            'force_side': 'right'
        }
    }

    if json_file:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                loaded_overrides = json.load(f)
                # Merge loaded overrides with defaults (loaded overrides take precedence)
                default_overrides.update(loaded_overrides)
                print(f"Loaded special overrides from {json_file}")
        except FileNotFoundError:
            print(f"Warning: Override file '{json_file}' not found. Using defaults.")
        except json.JSONDecodeError as e:
            print(f"Warning: Error parsing JSON file '{json_file}': {e}. Using defaults.")

    return default_overrides

def add_annotations_to_svg(content, nodes, special_overrides=None):
    """Add annotations ensuring:
    - 15px (OFF) clearance for label boxes and leader endpoints from all other nodes/labels
    - Default side by mid_x, but switch to opposite side if it yields a shorter line while still meeting clearance
    """
    if special_overrides is None:
        special_overrides = {}
    # Sort nodes top-to-bottom, then left-to-right
    nodes.sort(key=lambda n: (n['cy'], n['cx']))

    # Determine viewBox width to decide left/right placement threshold
    vb_match = re.search(r'viewBox="\s*0\s+0\s+([0-9.]+)\s+([0-9.]+)"', content)
    if vb_match:
        try:
            vb_w = float(vb_match.group(1))
        except ValueError:
            vb_w = 700.0
    else:
        vb_w = 700.0
    mid_x = vb_w / 2.0
    # Compute flowchart midpoint from nodes bounding box to decide left/right placement more accurately
    flow_min_x = min((n['x'] for n in nodes), default=0.0)
    flow_max_x = max((n['x'] + n['width'] for n in nodes), default=vb_w)
    flow_mid = (flow_min_x + flow_max_x) / 2.0

    # Find insertion point (before closing container group / svg)
    insertion_point = content.rfind('</g></svg>')
    if insertion_point == -1:
        insertion_point = content.rfind('</svg>')

    anno_items = []
    curve_logs = []
    # Styling per spec
    font_family = 'Arial, sans-serif'
    font_size = 11  # pt
    text_height = 11  # approximate px for baseline offset
    char_w = 6.5      # approx character width at 11pt
    base_pad_left = 60 * PROD     # distance from element on left side
    base_pad_right = 60 * PROD    # distance from element on right side

    # Build list of existing node boxes for clearance checks
    node_boxes = [{'id': n['id'], 'bbox': (n['x'], n['y'], n['width'], n['height'])} for n in nodes]
    placed_labels = []  # accumulate placed labels to enforce inter-label clearance

    for node in nodes:
        label_id = node['id']
        if label_id.startswith('id'):
            label_id=label_id[2:]

        # Apply per-ID overrides if any
        ov = special_overrides.get(label_id, {})
        label = ov.get('label_text', label_id)
        bpl = ov.get('base_pad_left', base_pad_left)
        bpr = ov.get('base_pad_right', base_pad_right)
        local_max_extra = ov.get('max_extra', 300.0)

        default_left = node['cx'] < flow_mid
        # Allow overrides to force a preferred side regardless of shorter alternative
        preferred_left = default_left
        if ov.get('force_side') == 'right':
            preferred_left = False
        elif ov.get('force_side') == 'left':
            preferred_left = True

        # Common text metrics
        text_w = max(10, char_w * len(label))
        text_h = text_height

        # Handle fixed curve width override (ignore all collision/clearance calculations)
        fixed_w = ov.get('curve_width', ov.get('length', ov.get('fixed_length')))
        if fixed_w is not None:
            try:
                fw = float(fixed_w)
            except (TypeError, ValueError):
                fw = None
            if fw is not None:
                place_left = preferred_left
                if ov.get('force_side') == 'right':
                    place_left = False
                elif ov.get('force_side') == 'left':
                    place_left = True

                text_y = node['cy'] + text_height
                if place_left:
                    end_x = node['x'] - 2
                    end_y = node['cy']
                    start_x = end_x - fw
                    start_y = text_y - (text_h / 2.0)
                    text_x = start_x - text_w  # right edge of label at start_x
                    text_anchor = 'start'
                else:
                    end_x = node['x'] + node['width'] + 2
                    end_y = node['cy']
                    start_x = end_x + fw
                    start_y = text_y - (text_h / 2.0)
                    text_x = start_x  # left edge of label at start_x
                    text_anchor = 'start'

                path_d = create_subtle_leader_line(start_x, start_y, end_x, end_y)
                label_bbox = (text_x, text_y - text_h, text_w, text_h)

                text_svg = (
                    f'<text x="{text_x:.1f}" y="{text_y:.1f}" '
                    f'font-family="{font_family}" font-size="{font_size}" fill="black" '
                    f'text-anchor="{text_anchor}">{label}</text>'
                )
                line_svg = f'<path d="{path_d}" stroke="black" stroke-width="0.8" fill="none"/>'

                anno_items.append(text_svg)
                anno_items.append(line_svg)
                placed_labels.append({'id': f'label:{label}', 'bbox': label_bbox})
                curve_logs.append({'id': label, 'width': abs(end_x - start_x), 'start_x': start_x, 'start_y': start_y})
                continue

        def compute_candidate(place_left: bool):
            # Try increasing offset outward until label bbox clears all others (excluding current node)
            step = 5.0 * PROD
            max_extra = local_max_extra
            extra = 0.0

            while extra <= max_extra:
                if place_left:
                    text_x = node['x'] - (bpl + extra)
                    text_y = node['cy'] + text_height
                    text_anchor = 'start'
                    label_bbox = (text_x, text_y - text_h, text_w, text_h)
                else:
                    text_x = node['x'] + node['width'] + (bpr + extra)
                    text_y = node['cy'] + text_height
                    text_anchor = 'start'
                    label_bbox = (text_x, text_y - text_h, text_w, text_h)

                ignore_ids = {node['id']}  # allow proximity to the target node; label being placed is not in boxes yet
                if rect_clearance_ok(label_bbox, node_boxes + placed_labels, OFF, ignore_ids=ignore_ids):
                    break
                extra += step
            else:
                return {'valid': False}

            # Start point at the nearest label corner toward the node
            if place_left:
                start_x = label_bbox[0] + label_bbox[2]  # right edge
                start_y = label_bbox[1] + (label_bbox[3] / 2.0)  # vertical center of label
                end_x = node['x'] - 2
                end_y = node['cy']
                # Adjust termination point outward if it violates clearance vs other boxes
                ex = 0.0
                while ex <= max_extra:
                    if point_clearance_ok(end_x - ex, end_y, node_boxes + placed_labels, OFF, ignore_ids={node['id']}):
                        end_x = end_x - ex
                        break
                    ex += step
                else:
                    return {'valid': False}
            else:
                start_x = label_bbox[0]                 # left edge
                start_y = label_bbox[1] + (label_bbox[3] / 2.0)  # vertical center of label
                end_x = node['x'] + node['width'] + 2
                end_y = node['cy']
                ex = 0.0
                while ex <= max_extra:
                    if point_clearance_ok(end_x + ex, end_y, node_boxes + placed_labels, OFF, ignore_ids={node['id']}):
                        end_x = end_x + ex
                        break
                    ex += step
                else:
                    return {'valid': False}

            # With the label box already OFF-clear, start point should also be OFF-clear to others
            if not point_clearance_ok(start_x, start_y, node_boxes + placed_labels, OFF, ignore_ids={node['id']}):
                # Push label a bit more if a corner is still too close
                bump = 0.0
                ok = False
                while bump <= max_extra:
                    bump += step
                    if place_left:
                        bx = node['x'] - (bpl + extra + bump)
                        by = text_y
                        bb = (bx, by - text_h, text_w, text_h)
                        sx = bx + text_w
                        sy = by - (text_h / 2.0)
                        if rect_clearance_ok(bb, node_boxes + placed_labels, OFF, ignore_ids={node['id']}) and \
                           point_clearance_ok(sx, sy, node_boxes + placed_labels, OFF, ignore_ids={node['id']}):
                            text_x, label_bbox, start_x, start_y = bx, bb, sx, sy
                            ok = True
                            break
                    else:
                        bx = node['x'] + node['width'] + (bpr + extra + bump)
                        by = text_y
                        bb = (bx, by - text_h, text_w, text_h)
                        sx = bx
                        sy = by - (text_h / 2.0)
                        if rect_clearance_ok(bb, node_boxes + placed_labels, OFF, ignore_ids={node['id']}) and \
                           point_clearance_ok(sx, sy, node_boxes + placed_labels, OFF, ignore_ids={node['id']}):
                            text_x, label_bbox, start_x, start_y = bx, bb, sx, sy
                            ok = True
                            break
                if not ok:
                    return {'valid': False}

            path_d = create_subtle_leader_line(start_x, start_y, end_x, end_y)
            line_len = math.hypot(end_x - start_x, end_y - start_y)

            text_svg = (
                f'<text x="{text_x:.1f}" y="{text_y:.1f}" '
                f'font-family="{font_family}" font-size="{font_size}" fill="black" '
                f'text-anchor="{text_anchor}">{label}</text>'
            )
            line_svg = f'<path d="{path_d}" stroke="black" stroke-width="0.8" fill="none"/>'

            return {
                'valid': True,
                'label_bbox': label_bbox,
                'text_svg': text_svg,
                'line_svg': line_svg,
                'length': line_len,
                'start_x': start_x,
                'start_y': start_y,
                'end_x': end_x,
                'width': abs(end_x - start_x),
            }

        # Evaluate default and alternative sides (respect forced side if provided)
        cand_default = compute_candidate(preferred_left)
        cand_alt = compute_candidate(not preferred_left) if ov.get('force_side') is None else {'valid': False}

        chosen = None
        if cand_default.get('valid') and cand_alt.get('valid'):
            # Switch side if the alternative is shorter
            chosen = cand_alt if (cand_alt['length'] + 0.1) < cand_default['length'] else cand_default
        elif cand_default.get('valid'):
            chosen = cand_default
        elif cand_alt.get('valid'):
            chosen = cand_alt
        else:
            # Fallback to naive placement (no clearance enforcement) if both failed
            place_left = preferred_left
            if place_left:
                text_x = node['x'] - bpl
                text_anchor = 'start'
                text_y = node['cy'] + text_height
                start_x = text_x + text_w
                start_y = text_y - (text_h / 2.0)
                end_x = node['x'] - 2
                end_y = node['cy']
            else:
                text_x = node['x'] + node['width'] + bpr
                text_anchor = 'start'
                text_y = node['cy'] + text_height
                start_x = text_x
                start_y = text_y - (text_h / 2.0)
                end_x = node['x'] + node['width'] + 2
                end_y = node['cy']

            path_d = create_subtle_leader_line(start_x, start_y, end_x, end_y)
            label_bbox = (text_x, text_y - text_h, text_w, text_h)
            text_svg = (
                f'<text x="{text_x:.1f}" y="{text_y:.1f}" '
                f'font-family="{font_family}" font-size="{font_size}" fill="black" '
                f'text-anchor="{text_anchor}">{label}</text>'
            )
            line_svg = f'<path d="{path_d}" stroke="black" stroke-width="0.8" fill="none"/>'
            chosen = {
                'valid': True,
                'label_bbox': label_bbox,
                'text_svg': text_svg,
                'line_svg': line_svg,
                'start_x': start_x,
                'start_y': start_y,
                'end_x': end_x,
                'width': abs(end_x - start_x),
            }

        # Emit chosen and record label bbox for subsequent clearance checks
        anno_items.append(chosen['text_svg'])
        anno_items.append(chosen['line_svg'])
        placed_labels.append({'id': f'label:{label}', 'bbox': chosen['label_bbox']})
        curve_logs.append({'id': label, 'width': chosen.get('width', 0.0), 'start_x': chosen.get('start_x', 0.0), 'start_y': chosen.get('start_y', 0.0)})

    # Wrap annotations in a group for easy removal/identification
    annotations_group = (
        '\n  <g id="annotations" data-et="annotation">\n    ' +
        '\n    '.join(anno_items) +
        '\n  </g>\n'
    )

    updated_content = content[:insertion_point] + annotations_group + content[insertion_point:]
    return updated_content, curve_logs

def remove_existing_annotations(content):
    """Remove existing annotations from SVG content."""
    # Remove an entire prior annotation group if present
    content = re.sub(r'<g[^>]*id="annotations"[^>]*>[\s\S]*?</g>', '', content)

    # Also defensively remove free-floating text/paths that look like prior annotations
    content = re.sub(r'<text[^>]*font-family="Arial[^>]*>(?:id\d+|\d+)</text>', '', content)
    content = re.sub(r'<text[^>]*>(?:id\d+|\d+)</text>', '', content)
    content = re.sub(r'<path[^>]*stroke-width="0\.8"[^>]*>', '', content)
    content = re.sub(r'<path[^>]*fill="none"[^>]*stroke="black"[^>]*>', '', content)

    return content

def main():
    parser = argparse.ArgumentParser(
        description='Add numbered references to patent drawing SVG files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s input.svg
  %(prog)s input.svg -o output.svg
  %(prog)s input.svg --overrides custom_overrides.json
        '''
    )

    parser.add_argument('input_file', help='Input SVG file path')
    parser.add_argument('-o', '--output', help='Output SVG file path (default: input_annotated.svg)')
    parser.add_argument('--overrides', help='JSON file with special placement overrides')

    args = parser.parse_args()

    input_file = args.input_file
    output_file = args.output if args.output else input_file.replace('.svg', '_annotated.svg')

    print(f"Input: {input_file}")
    print(f"Output: {output_file}")

    # Load special overrides
    special_overrides = load_special_overrides(args.overrides)

    # Read and parse SVG
    content, root = parse_svg_file(input_file)

    # Remove existing annotations
    content = remove_existing_annotations(content)

    # Extract node information
    nodes = extract_node_info_from_content(content)
    print(f"Found {len(nodes)} flowchart nodes:")

    for node in nodes:
        print(f"  {node['id']}: center=({node['cx']:.0f}, {node['cy']:.0f}), size={node['width']:.0f}x{node['height']:.0f}")

    if nodes:
        # Add annotations with special overrides
        updated_content, curve_logs = add_annotations_to_svg(content, nodes, special_overrides)

        # Write updated SVG
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        print(f"\nUpdated SVG written to {output_file}")
        print(f"Added {len(nodes)} annotations using internal IDs")
        print("\nCurve placements (width and start coordinates):")
        for e in curve_logs:
            print(f"  {e['id']}: width={e['width']:.1f}, start=({e['start_x']:.1f},{e['start_y']:.1f})")
    else:
        print("No nodes found - check SVG structure")

if __name__ == '__main__':
    main()
