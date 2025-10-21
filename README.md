# Patent Drawings - Reference Annotation Tool

A Python tool that automatically adds numbered references and leader lines to patent drawing SVG files in a professional, patent-office-compliant format.

**Recommended for use with SVG files generated from [Mermaid](https://mermaid.js.org/) flowcharts.** The tool has been developed and tested specifically with Mermaid-generated SVG diagrams.

## Features

- **Automatic Annotation**: Adds numbered reference labels with S-curved leader lines to flowchart nodes
- **Smart Placement**: Automatically positions labels to avoid collisions with other elements
- **Collision Avoidance**: Maintains 15px clearance between labels, leader lines, and diagram elements
- **Customizable Overrides**: Use JSON files to override automatic placement for specific elements
- **Patent-Style Leader Lines**: Creates professional S-curved leader lines using cubic Bézier curves
- **Command-Line Interface**: Full argument parsing with flexible options

## Installation

Requires Python 3.6+ with standard library only (no external dependencies).

```bash
git clone <repository-url>
cd patent_drawings
```

## Quick Start

### Basic Usage

```bash
# Annotate an SVG file (creates input_annotated.svg)
python add_references.py input.svg

# Specify custom output file
python add_references.py input.svg -o output.svg

# Use custom placement overrides
python add_references.py input.svg --overrides my_overrides.json
```

### Example

See the included example files demonstrating the before and after:

#### Input: euclid.svg (Original Mermaid Flowchart)
<img width="392" height="595" alt="image" src="https://github.com/user-attachments/assets/aee5c36f-20ed-48e1-af70-6f24b57f5d51" />



#### First try with the script 

<img width="389" height="605" alt="image" src="https://github.com/user-attachments/assets/cd933a43-920f-40d2-a86b-07fd9c63ab05" />

#### Final Output (After simple manual override) 
<img width="377" height="601" alt="image" src="https://github.com/user-attachments/assets/9935f693-8533-4fa6-9e2b-8db34a50160a" />







To recreate the annotated example:
```bash
python add_references.py euclid.svg
```

## Command-Line Options

```
usage: add_references.py [-h] [-o OUTPUT] [--overrides OVERRIDES] input_file

positional arguments:
  input_file            Input SVG file path

options:
  -h, --help            Show help message and exit
  -o OUTPUT, --output OUTPUT
                        Output SVG file path (default: input_annotated.svg)
  --overrides OVERRIDES
                        JSON file with special placement overrides
```

## Override File Format

Create a JSON file to customize placement for specific nodes. See [OVERRIDE_FORMAT.md](OVERRIDE_FORMAT.md) for complete documentation.

### Example Override File

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
  }
}
```

### Available Override Options

- **`force_side`**: Force label to "left" or "right" side
- **`curve_width`**: Set fixed horizontal distance for leader line (in pixels)
- **`label_text`**: Override default label text
- **`base_pad_left`** / **`base_pad_right`**: Adjust padding distance
- **`max_extra`**: Maximum additional spacing for collision avoidance

See `overrides_example.json` and `OVERRIDE_FORMAT.md` for more details.

## How It Works

1. **Parse SVG**: Extracts flowchart node information (rectangles, circles, polygons)
2. **Sort Nodes**: Orders nodes top-to-bottom, then left-to-right
3. **Smart Placement**:
   - Determines optimal side (left/right) based on diagram layout
   - Calculates label position with 15px clearance from all elements
   - Can switch sides if it results in a shorter, collision-free leader line
4. **Generate Annotations**: Creates text labels and S-curved leader lines
5. **Output SVG**: Writes annotated SVG with professional patent-style references

## Technical Details

- **Leader Line Style**: S-shaped cubic Bézier curves with perpendicular offsets at 1/3 and 2/3 control points
- **Clearance**: 15px minimum clearance maintained between all elements
- **Font**: Arial 11pt for labels
- **Line Width**: 0.8px stroke width for leader lines
- **Node Detection**: Supports rectangles, circles, and polygons (diamonds, hexagons)

## Files

- **add_references.py** - Main script
- **overrides_example.json** - Sample override file with defaults
- **OVERRIDE_FORMAT.md** - Complete override file documentation
- **euclid.svg** - Example input diagram
- **euclid_annotated.svg** - Example output with annotations

## Workflow Example

1. Create your flowchart diagram in Mermaid or another tool
2. Export as SVG
3. Run the annotation tool:
   ```bash
   python add_references.py diagram.svg
   ```
4. If needed, create an override file for specific nodes:
   ```bash
   python add_references.py diagram.svg --overrides custom.json
   ```
5. Use the annotated SVG in your patent application

## Tips

- Start without overrides and let the automatic placement work
- Only add overrides for problematic nodes that need manual adjustment
- Use `force_side` when automatic side selection isn't optimal
- Use `curve_width` to fine-tune leader line length for aesthetic consistency
- The tool can be run multiple times - it removes existing annotations before adding new ones

## License

[Add your license information here] 
