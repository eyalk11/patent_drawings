# Override File Format

The override file is a JSON file that allows you to customize the placement of reference labels for specific nodes in your patent drawing.

## File Format

The JSON file should contain an object where each key is a node ID (without the "id" prefix) and the value is an object with override options.

### Example

```json
{
  "512b": {
    "force_side": "right",
    "curve_width": 32.0
  },
  "506": {
    "force_side": "right",
    "curve_width": 30.0
  },
  "209": {
    "force_side": "right",
    "curve_width": 80
  },
  "203": {
    "force_side": "right"
  }
}
```

## Available Override Options

### `force_side`
- **Type:** String
- **Values:** `"left"` or `"right"`
- **Description:** Forces the label to appear on a specific side of the node, regardless of the automatic placement algorithm.

### `curve_width`
- **Type:** Number (float or integer)
- **Values:** Positive number representing pixels
- **Description:** Sets a fixed horizontal distance for the leader line. When set, this overrides the automatic collision-avoidance calculation and uses the exact width specified.
- **Aliases:** `length`, `fixed_length` (all work the same way)

### `label_text`
- **Type:** String
- **Description:** Overrides the default label text (which is the node ID). Use this to display custom text instead of the numeric ID.

### `base_pad_left`
- **Type:** Number
- **Values:** Positive number representing pixels
- **Description:** Overrides the default left-side padding distance (default: 60px)

### `base_pad_right`
- **Type:** Number
- **Values:** Positive number representing pixels
- **Description:** Overrides the default right-side padding distance (default: 60px)

### `max_extra`
- **Type:** Number
- **Values:** Positive number representing pixels
- **Description:** Overrides the maximum additional spacing the algorithm can add to avoid collisions (default: 300px)

## Usage

```bash
python add_references.py input.svg --overrides my_overrides.json
```

## Tips

1. **Start Simple:** Only add overrides for nodes that need special handling
2. **Test Incrementally:** Add one override at a time to see the effect
3. **Use `curve_width` Carefully:** Fixed curve widths bypass collision detection, so make sure the width is sufficient to avoid overlaps
4. **Combine Options:** You can use multiple options together, e.g., force a side AND set a fixed width
