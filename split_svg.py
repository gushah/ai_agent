import re, os

with open("agent_flow_diagram.svg") as f:
    content = f.read()

# Arrow defs (moved to top of each section file so they're always available)
defs = """\
  <defs>
    <marker id="a-blue"   markerWidth="7" markerHeight="7" refX="5" refY="2.5" orient="auto"><path d="M0,0 L0,5 L7,2.5 z" fill="#58a6ff"/></marker>
    <marker id="a-green"  markerWidth="7" markerHeight="7" refX="5" refY="2.5" orient="auto"><path d="M0,0 L0,5 L7,2.5 z" fill="#3fb950"/></marker>
    <marker id="a-purple" markerWidth="7" markerHeight="7" refX="5" refY="2.5" orient="auto"><path d="M0,0 L0,5 L7,2.5 z" fill="#d2a8ff"/></marker>
    <marker id="a-orange" markerWidth="7" markerHeight="7" refX="5" refY="2.5" orient="auto"><path d="M0,0 L0,5 L7,2.5 z" fill="#ffa657"/></marker>
    <marker id="a-sdk"    markerWidth="7" markerHeight="7" refX="5" refY="2.5" orient="auto"><path d="M0,0 L0,5 L7,2.5 z" fill="#79c0ff"/></marker>
  </defs>"""

# Strip outer <svg> wrapper (keep all inner content including original defs —
# browsers use the first matching ID, so our new defs block at top takes precedence)
inner = re.sub(r'^<svg[^>]*>\n?', '', content)
inner = re.sub(r'\n?</svg>\s*$', '', inner)

print("Inner content lines:", inner.count('\n'))

# Section definitions: (filename, title, y_start, height)
sections = [
    ("01-agent-flow",
     "Agent Flow — POST /chat",
     0, 582),
    ("02-rag-flow",
     "RAG Flow — POST /documents/rag-chat",
     580, 487),
    ("03-comparison-code",
     "Agent vs RAG Comparison + Code Structure",
     1058, 410),
    ("04-mcp-flow",
     "MCP Flow — POST /mcp-chat",
     1453, 530),
    ("05-multi-agent",
     "Multi-Agent Flow — POST /multi-agent-chat",
     1955, 530),
]

os.makedirs("docs/diagrams", exist_ok=True)

for fname, title, y0, h in sections:
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg"',
        ' viewBox="0 ' + str(y0) + ' 980 ' + str(h) + '"',
        ' width="980" height="' + str(h) + '"',
        ' font-family="Segoe UI, Arial, sans-serif">',
        '\n  <!-- ' + title + ' -->',
        '\n' + defs,
        '\n  <rect x="0" y="' + str(y0) + '" width="980" height="' + str(h) + '" fill="#0f1117"/>',
        '\n' + inner,
        '\n</svg>',
    ]
    svg_text = ''.join(parts)
    path = "docs/diagrams/" + fname + ".svg"
    with open(path, "w") as f:
        f.write(svg_text)
    size = os.path.getsize(path)
    lines = svg_text.count('\n')
    print(fname + ".svg  —  " + str(lines) + " lines, " + str(size) + " bytes")

print("\nDone.")
