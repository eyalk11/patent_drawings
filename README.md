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
- **Zero dependencies**: no pip install needed

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


## How It Works

1. **Parse SVG**: Extracts flowchart node information (rectangles, circles, polygons). It includes 
2. **Sort Nodes**: Orders nodes top-to-bottom, then left-to-right
3. **Smart Placement**:
   - Determines optimal side (left/right) based on diagram layout
   - Calculates label position with 15px clearance from all elements
   - Can switch sides if it results in a shorter, collision-free leader line
4. **Generate Annotations**: Creates text labels and S-curved leader lines
5. **Output SVG**: Writes annotated SVG with professional patent-style references

### Tips

- Start without overrides and let the automatic placement work
- Only add overrides for problematic nodes that need manual adjustment
- Use `force_side` when automatic side selection isn't optimal
- Use `curve_width` to fine-tune leader line length for aesthetic consistency
- The tool can be run multiple times - it removes existing annotations before adding new ones

## Workflow Example

### Stage 1: Write Your Flowchart in Mermaid

Create your flowchart using [Mermaid](https://mermaid.js.org/) syntax. **Important**: The node IDs you assign in Mermaid (e.g., `id200`, `id201`, `id203`) are what you'll reference in override files to customize annotation placement for specific nodes.

<details>
<summary>Example: Euclid's Algorithm Flowchart (euclid.mmd)</summary>

```
---
config:
  layout: dagre
  flowchart:
    curve: cardinal
    fontFamily: Arial, sans-serif
    fontSize: 14pt
    nodeSpacing: 50
    rankSpacing: 50
    stroke: '#000000'
    arrowMarkerAbsolute: false
---
flowchart TB
    id200("Start") --> id201[/"Input two positive integers a, b"/]
    id201 --> id202{"Is b > a?"}
    id202 -- Yes --> id203["SWAP a and b"]
    id202 -- No --> id204{"Is b ≠ 0?"}
    id203 --> id204
    id204 -- Yes --> id205["remainder ← a MOD b"]
    id205 --> id206["a ← b"]
    id206 --> id207["b ← remainder"]
    id207 --> id204
    id204 -- No --> id208[/"RETURN a"/]
    id208 --> id209("End")
```

**Note**: Each node has an explicit ID (id200-id209). These IDs are used by the annotation tool to identify nodes and can be referenced in override files.

**Override file for this diagram**:
```json
{
  "203": {
    "force_side": "right"
  }
}
```
The override references node `id203` by its numeric portion (`"203"`), forcing the SWAP annotation to the right side.

</details>

### Stage 2: Export Your Mermaid Diagram as SVG

After creating your flowchart in Mermaid, export it as an SVG file. For example, exporting the Euclid algorithm flowchart creates `euclid.svg`:

<img width="392" height="595" alt="Original Mermaid Flowchart" src="https://github.com/user-attachments/assets/aee5c36f-20ed-48e1-af70-6f24b57f5d51" />

### Stage 3: Run the Annotation Tool

Run the script to automatically add numbered annotations:

```bash
python add_references.py euclid.svg
```

This creates `euclid_annotated.svg` with automatic annotation placement:

<img width="389" height="605" alt="First automated annotation" src="https://github.com/user-attachments/assets/cd933a43-920f-40d2-a86b-07fd9c63ab05" />

### Stage 4: (Optional) Create Override File for Fine-Tuning

If some annotations need adjustment (like node 203 in the example above), create an override JSON file:

```json
{
  "203": {
    "force_side": "right"
  }
}
```

Then run with the override:

```bash
python add_references.py euclid.svg --overrides overrides.json
```

Final result with improved placement:

<img width="377" height="601" alt="Final output with override" src="https://github.com/user-attachments/assets/9935f693-8533-4fa6-9e2b-8db34a50160a" />

### Stage 5: Use the Annotated SVG

Use the final annotated SVG in your patent application.



## Technical Details

### Annotation System

- **Leader Line Style**: S-shaped cubic Bézier curves with perpendicular offsets at 1/3 and 2/3 control points
- **Clearance**: 15px minimum clearance maintained between all elements
- **Font**: Arial 11pt for labels
- **Line Width**: 0.8px stroke width for leader lines
- **Node Detection**: Supports rectangles, circles, and polygons (diamonds, hexagons)

### Recommended Mermaid Configuration

For Mermaid flowcharts, use this configuration for best results:
```
---
config:
  layout: dagre
  flowchart:
    curve: stepAfter
    fontFamily: Arial, sans-serif
    fontSize: 11pt
    nodeSpacing: 50
    rankSpacing: 50
    stroke: '#000000'
    arrowMarkerAbsolute: false
---

```

### Files

- **add_references.py** - Main script
- **overrides_example.json** - Sample override file with defaults
- **OVERRIDE_FORMAT.md** - Complete override file documentation
- **euclid.svg** - Example input diagram
- **euclid_annotated.svg** - Example output with annotations


### Override File Format

Create a JSON file to customize placement for specific nodes. See [OVERRIDE_FORMAT.md](OVERRIDE_FORMAT.md) for complete documentation.


#### Available Override Options

- **`force_side`**: Force label to "left" or "right" side
- **`curve_width`**: Set fixed horizontal distance for leader line (in pixels)
- **`label_text`**: Override default label text
- **`base_pad_left`** / **`base_pad_right`**: Adjust padding distance
- **`max_extra`**: Maximum additional spacing for collision avoidance

See `OVERRIDE_FORMAT.md` for more details.



## Reference 

I took inspiration from [blog](https://blog.patentology.com.au/2025/08/can-you-turn-ai-chatbot-into-patent.html)
which suggests to do it using AI.

## Disclaimer 
No responsibility is taken for the correctness or suitability of this tool for any specific patent application. Always verify compliance with the relevant patent office guidelines.
As the license suggests, this tool is provided "as is" without warranty of any kind. 

