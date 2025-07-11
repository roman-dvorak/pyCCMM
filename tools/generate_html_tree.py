import zipfile
import os
import xml.etree.ElementTree as ET

CCMM_PATH = "../src/pyccmm/schemas/CCMM/"
HTML_PATH = "xsd_dataset_full.html"

# ==== Najdi všechny XSD ====
xsd_files = {}
for root_dir, dirs, files in os.walk(CCMM_PATH):
    for file in files:
        if file == "schema.xsd":
            path = os.path.join(root_dir, file)
            key = os.path.basename(os.path.dirname(path))
            # Mapuj složky s pomlčkami na typy s podtržítky
            type_name = key.replace("-", "_")
            xsd_files[type_name] = path
            # Zachováme i původní klíč pro kompatibilitu
            xsd_files[key] = path

# ==== Načti všechny XSD ====
parsed_xsds = {}
for key, path in xsd_files.items():
    with open(path, "r", encoding="utf-8") as f:
        parsed_xsds[key] = ET.parse(f).getroot()

def find_xsd_for_type(type_name):
    typ = type_name.split(":")[-1]
    if typ in xsd_files:
        return parsed_xsds[typ]
    if typ.startswith("xs") or typ in ["string", "boolean", "gYear", "anyURI"]:
        return None
    return None

def get_complex_type(xsd_root, type_name):
    for ctype in xsd_root.findall("{http://www.w3.org/2001/XMLSchema}complexType"):
        if ctype.attrib.get("name") == type_name:
            return ctype
    return None

def get_simple_type(xsd_root, type_name):
    for stype in xsd_root.findall("{http://www.w3.org/2001/XMLSchema}simpleType"):
        if stype.attrib.get("name") == type_name:
            return stype
    return None

def get_group(xsd_root, group_name):
    for group in xsd_root.findall("{http://www.w3.org/2001/XMLSchema}group"):
        if group.attrib.get("name") == group_name:
            return group
    return None

def get_attributes(ctype):
    attrs = []
    for attr in ctype.findall("{http://www.w3.org/2001/XMLSchema}attribute"):
        name = attr.attrib.get("name")
        typ = attr.attrib.get("type")
        use = attr.attrib.get("use", "optional")
        annotation = attr.find("{http://www.w3.org/2001/XMLSchema}annotation")
        doc = None
        if annotation is not None:
            documentation = annotation.find("{http://www.w3.org/2001/XMLSchema}documentation")
            if documentation is not None and documentation.text:
                doc = documentation.text.strip()
        attrs.append({
            "name": name,
            "type": typ,
            "use": use,
            "doc": doc
        })
    return attrs

all_enums = {}

# ==== Hlavní strom ====
def render_expanded_html(type_name, indent=0, path=None):
    if path is None:
        path = []
    typ = type_name.split(":")[-1]
    ns = "{http://www.w3.org/2001/XMLSchema}"
    safe = lambda s: (s or "").replace("<", "&lt;").replace(">", "&gt;")
    # Cykly: povol 1. výskyt, další už ne
    if typ in path:
        return f'<li><span class="cyclic">{safe(typ)} ↺ cyklický odkaz (obsah viz výše)</span></li>'
    new_path = path + [typ]
    xsd_root = find_xsd_for_type(typ)
    if xsd_root is None:
        return f'<li><span class="primitive">{safe(type_name)}</span></li>'
    ctype = get_complex_type(xsd_root, typ)
    stype = get_simple_type(xsd_root, typ)
    html = ""
    if ctype is not None:
        label = f'<span class="nodename">📄 {safe(typ)} <span class="type">(komplexní typ)</span></span>'
        attrs = get_attributes(ctype)
        attrs_html = ""
        if attrs:
            attrs_html += '<ul class="attributes">'
            for attr in attrs:
                attr_label = f'<span class="attrname">🔑 @{safe(attr["name"])}</span>'
                if attr.get("type"):
                    attr_label += f' <span class="type">{safe(attr["type"])}</span>'
                if attr.get("use") == "required":
                    attr_label += f' <span class="required">(povinný)</span>'
                else:
                    attr_label += f' <span class="optional">(volitelný)</span>'
                if attr.get("doc"):
                    attr_label += f' <span class="doc" title="{safe(attr["doc"])}">🛈 {safe(attr["doc"])}</span>'
                attrs_html += f'<li>{attr_label}</li>'
            attrs_html += '</ul>'
        children_html = ""
        for sub in ctype:
            if sub.tag == ns + "sequence":
                children_html += f'<li><span class="group sequence" title="Sekvence: prvky musí být uvedeny v přesném pořadí">🧩 sekvence</span><ul class="nested active">'
                for elem in sub.findall(ns + "element"):
                    el_name = elem.attrib.get("name")
                    el_type = elem.attrib.get("type")
                    mino = elem.attrib.get("minOccurs", "1")
                    maxo = elem.attrib.get("maxOccurs", "1")
                    annotation = elem.find(ns + "annotation")
                    doc = None
                    if annotation is not None:
                        documentation = annotation.find(ns + "documentation")
                        if documentation is not None and documentation.text:
                            doc = documentation.text.strip()
                    occurs = f'[{mino}..{maxo}]'
                    label2 = f'<span class="nodename">📄 {safe(el_name)}</span>'
                    if el_type:
                        label2 += f' <span class="type">{safe(el_type)}</span>'
                    if maxo == "unbounded" or (maxo.isdigit() and int(maxo) > 1):
                        label2 += f' <span class="occurs repeat" title="Vícenásobný výskyt">🔁 {occurs}</span>'
                    else:
                        label2 += f' <span class="occurs">{occurs}</span>'
                    if mino == "0":
                        label2 += f' <span class="optional">(volitelné)</span>'
                    elif mino == "1":
                        label2 += f' <span class="required">(povinné)</span>'
                    if doc:
                        label2 += f' <span class="doc" title="{safe(doc)}">🛈 {safe(doc)}</span>'
                    if el_type and not el_type.startswith("xs:"):
                        children_html += f'<li><span class="caret">{label2}</span><ul class="nested">{render_expanded_html(el_type, indent+3, new_path)}</ul></li>'
                    else:
                        children_html += f'<li>{label2}</li>'
                children_html += "</ul></li>"
            elif sub.tag == ns + "choice":
                children_html += f'<li><span class="group choice" title="Volba: může být použit pouze jeden z uvedených prvků">🔀 volba</span><ul class="nested active">'
                for elem in sub.findall(ns + "element"):
                    el_name = elem.attrib.get("name")
                    el_type = elem.attrib.get("type")
                    mino = elem.attrib.get("minOccurs", "1")
                    maxo = elem.attrib.get("maxOccurs", "1")
                    annotation = elem.find(ns + "annotation")
                    doc = None
                    if annotation is not None:
                        documentation = annotation.find(ns + "documentation")
                        if documentation is not None and documentation.text:
                            doc = documentation.text.strip()
                    occurs = f'[{mino}..{maxo}]'
                    label2 = f'<span class="nodename">📄 {safe(el_name)}</span>'
                    if el_type:
                        label2 += f' <span class="type">{safe(el_type)}</span>'
                    if maxo == "unbounded" or (maxo.isdigit() and int(maxo) > 1):
                        label2 += f' <span class="occurs repeat">🔁 {occurs}</span>'
                    else:
                        label2 += f' <span class="occurs">{occurs}</span>'
                    if mino == "0":
                        label2 += f' <span class="optional">(volitelné)</span>'
                    elif mino == "1":
                        label2 += f' <span class="required">(povinné)</span>'
                    if doc:
                        label2 += f' <span class="doc" title="{safe(doc)}">🛈 {safe(doc)}</span>'
                    if el_type and not el_type.startswith("xs:"):
                        children_html += f'<li><span class="caret">{label2}</span><ul class="nested">{render_expanded_html(el_type, indent+3, new_path)}</ul></li>'
                    else:
                        children_html += f'<li>{label2}</li>'
                children_html += "</ul></li>"
            elif sub.tag == ns + "all":
                children_html += f'<li><span class="group all" title="Všechny: všechny prvky musí být uvedeny, ale v libovolném pořadí">📦 všechny</span><ul class="nested active">'
                for elem in sub.findall(ns + "element"):
                    el_name = elem.attrib.get("name")
                    el_type = elem.attrib.get("type")
                    mino = elem.attrib.get("minOccurs", "1")
                    maxo = elem.attrib.get("maxOccurs", "1")
                    annotation = elem.find(ns + "annotation")
                    doc = None
                    if annotation is not None:
                        documentation = annotation.find(ns + "documentation")
                        if documentation is not None and documentation.text:
                            doc = documentation.text.strip()
                    occurs = f'[{mino}..{maxo}]'
                    label2 = f'<span class="nodename">📄 {safe(el_name)}</span>'
                    if el_type:
                        label2 += f' <span class="type">{safe(el_type)}</span>'
                    if maxo == "unbounded" or (maxo.isdigit() and int(maxo) > 1):
                        label2 += f' <span class="occurs repeat">🔁 {occurs}</span>'
                    else:
                        label2 += f' <span class="occurs">{occurs}</span>'
                    if mino == "0":
                        label2 += f' <span class="optional">(volitelné)</span>'
                    elif mino == "1":
                        label2 += f' <span class="required">(povinné)</span>'
                    if doc:
                        label2 += f' <span class="doc" title="{safe(doc)}">🛈 {safe(doc)}</span>'
                    if el_type and not el_type.startswith("xs:"):
                        children_html += f'<li><span class="caret">{label2}</span><ul class="nested">{render_expanded_html(el_type, indent+3, new_path)}</ul></li>'
                    else:
                        children_html += f'<li>{label2}</li>'
                children_html += "</ul></li>"
            elif sub.tag == ns + "group":
                group_ref = sub.attrib.get("ref")
                group_typ = group_ref.split(":")[-1]
                group_xsd = find_xsd_for_type(group_typ)
                if group_xsd:
                    group = get_group(group_xsd, group_typ)
                    if group is not None:
                        children_html += f'<li><span class="group group" title="Skupina: reference na pojmenovanou skupinu prvků definovanou jinde">🗂️ skupina {safe(group_typ)}</span><ul class="nested active">'
                        children_html += render_expanded_html(group_typ, indent+2, new_path)
                        children_html += "</ul></li>"
                    else:
                        children_html += f'<li><span class="group group">🗂️ skupina {safe(group_typ)} (nenalezena)</span></li>'
        html += f'<li><span class="caret">{label}</span>{attrs_html}<ul class="nested">{children_html}</ul></li>'
    elif stype is not None:
        enums = []
        restrictions = stype.findall(".//{http://www.w3.org/2001/XMLSchema}enumeration")
        for res in restrictions:
            val = res.attrib.get("value")
            enums.append(val)
        if enums:
            all_enums[typ] = enums
            label = f'<span class="nodename simple">{safe(typ)} <span class="enum">(výčet hodnot)</span></span>'
            html += f'<li>{label}<ul class="attributes">'
            for val in enums:
                html += f'<li><span class="enum">🎯 {safe(val)}</span></li>'
            html += '</ul></li>'
        else:
            label = f'<span class="nodename simple">{safe(typ)} <span class="primitive">(jednoduchý typ)</span></span>'
            restr = stype.find(".//{http://www.w3.org/2001/XMLSchema}pattern")
            if restr is not None:
                label += f' <span class="pattern">(pattern: {safe(restr.attrib.get("value"))})</span>'
            html += f'<li>{label}</li>'
    else:
        html += f'<li><span>{safe(typ)} (definice nenalezena)</span></li>'
    return html

tree_html_full = render_expanded_html("dataset")

# Výpis všech enumů na konec
enums_section = '<h3>Seznam všech výčtů (enumů) v XSD:</h3><ul>'
for t, vals in all_enums.items():
    enums_section += f'<li><b>{t}</b><ul>'
    for v in vals:
        enums_section += f'<li><span class="enum">🎯 {v}</span></li>'
    enums_section += '</ul></li>'
enums_section += '</ul>'

enums_section = ""

# ===== HTML kód =====
html_code_full = f"""
<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <title>XSD Tree - Kompletní in-place strom</title>
  <style>
    body {{ font-family: Segoe UI, Arial, sans-serif; background: #f9f9f9; color: #222; }}
    .treeview ul, .treeview li {{ list-style-type: none; }}
    .treeview {{ margin: 2em; }}
    .treeview ul {{ margin-left: 1.5em; padding-left: 1em; border-left: 1px dotted #ccc; }}
    .caret {{ cursor: pointer; user-select: none; }}
    .caret::before {{ content: "\\25B6"; color: #888; display: inline-block; margin-right: 6px; transition: 0.1s; }}
    .caret-down::before {{ transform: rotate(90deg); }}
    .nested {{ display: none; }}
    .active {{ display: block; }}
    .nodename {{ font-weight: bold; color: #28507a; }}
    .nodename.simple {{ color: #777; font-weight: normal; }}
    .attrname {{ color: #a77d08; font-weight: bold; }}
    .group.sequence {{ color: #2986cc; font-weight: bold; }}
    .group.choice {{ color: #bd3800; font-weight: bold; }}
    .group.all {{ color: #18871b; font-weight: bold; }}
    .group.group {{ color: #533; font-weight: bold; }}
    .enum {{ color: #804b2b; font-weight: bold; }}
    .type {{ color: #468; font-size: 0.95em; margin-left: 0.4em; }}
    .occurs {{ color: #666; font-size: 0.95em; margin-left: 0.4em; }}
    .repeat {{ color: #a21c1c; font-weight: bold; }}
    .required {{ color: #0e730a; font-size: 0.92em; margin-left: 0.2em; }}
    .optional {{ color: #888; font-size: 0.92em; margin-left: 0.2em; font-style: italic; }}
    .doc {{ color: #18871b; font-size: 0.96em; margin-left: 0.5em; }}
    .pattern {{ color: #2b537c; font-size: 0.95em; margin-left: 0.5em; }}
    .cyclic {{ color: #a21c1c; font-size: 0.95em; margin-left: 0.5em; font-style: italic; }}
    .primitive {{ color: #2d2043; font-size: 0.98em; }}
    .attributes {{ margin-left: 2.5em; margin-bottom: 0.2em; padding-left: 0.7em; border-left: 1px dashed #eee; }}
    li {{ margin-bottom: 0.4em; }}
    .toolbar {{ margin: 1em 0; }}
    .toolbar button {{
        background: #28507a; color: #fff; font-weight: bold;
        border: none; border-radius: 6px; padding: 6px 16px; margin-right: 12px;
        cursor: pointer; box-shadow: 0 1px 3px #0001;
        transition: background 0.2s;
    }}
    .toolbar button:hover {{ background: #18871b; }}
    .legend {{ margin: 1em 0; padding: 1.5em; background: #f8f9fa; border-radius: 8px; border: 1px solid #e9ecef; }}
    .legend h3 {{ margin-top: 0; color: #28507a; text-align: center; }}
    .legend-section {{ margin-bottom: 1.5em; }}
    .legend-section:last-child {{ margin-bottom: 0; }}
    .legend-section h4 {{ margin: 0 0 0.8em 0; color: #495057; font-size: 1em; border-bottom: 1px solid #dee2e6; padding-bottom: 0.3em; }}
    .legend-row {{ display: flex; align-items: flex-start; gap: 1em; margin-bottom: 0.6em; padding: 0.4em 0; }}
    .legend-row:last-child {{ margin-bottom: 0; }}
    .legend-desc {{ color: #666; font-size: 0.9em; flex: 1; line-height: 1.4; }}
    .legend-term {{ font-family: monospace; background: #e9ecef; padding: 0.2em 0.4em; border-radius: 3px; color: #495057; font-weight: bold; }}
  </style>
</head>
<body>
<h2>XSD strom: CCMM dataset</h2>
<div class="toolbar">
    <button onclick="expandAll()">Expand All</button>
    <button onclick="collapseAll()">Collapse All</button>
</div>
<div class="legend">
  <h3>📝 Legenda symbolů</h3>
  
  <div class="legend-section">
    <h4>🏗️ Strukturální prvky</h4>
    <div class="legend-row">
      <span class="nodename">📄 element</span>
      <span class="legend-desc">XML element/pole</span>
    </div>
    <div class="legend-row">
      <span class="attrname">🔑 @atribut</span>
      <span class="legend-desc">XML atribut</span>
    </div>
    <div class="legend-row">
      <span class="legend-term">iri</span>
      <span class="legend-desc">Internationalized Resource Identifier - jedinečný identifikátor zdroje</span>
    </div>
  </div>
  
  <div class="legend-section">
    <h4>🎯 Skupiny prvků</h4>
    <div class="legend-row">
      <span class="group sequence">🧩 sekvence</span>
      <span class="legend-desc">Prvky musí být uvedeny v přesném pořadí</span>
    </div>
    <div class="legend-row">
      <span class="group choice">🔀 volba</span>
      <span class="legend-desc">Pouze jeden z uvedených prvků</span>
    </div>
    <div class="legend-row">
      <span class="group all">📦 všechny</span>
      <span class="legend-desc">Všechny prvky, libovolné pořadí</span>
    </div>
    <div class="legend-row">
      <span class="group group">🗂️ skupina</span>
      <span class="legend-desc">Reference na pojmenovanou skupinu prvků</span>
    </div>
  </div>
  
  <div class="legend-section">
    <h4>🔢 Výskyty a omezení</h4>
    <div class="legend-row">
      <span class="occurs repeat">🔁 [1..n]</span>
      <span class="legend-desc">Vícenásobný výskyt prvku</span>
    </div>
    <div class="legend-row">
      <span class="required">(povinné)</span>
      <span class="legend-desc">Prvek musí být vždy přítomen</span>
    </div>
    <div class="legend-row">
      <span class="optional">(volitelné)</span>
      <span class="legend-desc">Prvek může být vynechán</span>
    </div>
    <div class="legend-row">
      <span class="enum">🎯 výčet</span>
      <span class="legend-desc">Seznam předdefinovaných hodnot</span>
    </div>
  </div>
  
  <div class="legend-section">
    <h4>ℹ️ Doplňující informace</h4>
    <div class="legend-row">
      <span class="doc">🛈 dokumentace</span>
      <span class="legend-desc">Popis a vysvětlení prvku</span>
    </div>
    <div class="legend-row">
      <span class="cyclic">↺ cyklický</span>
      <span class="legend-desc">Odkaz na již zobrazený typ (zamezuje nekonečnému zanoření)</span>
    </div>
  </div>
</div>
<p>(Klikni na název pro rozbalení/zbalení větve. <span class="repeat">🔁</span>)</p>
<div class="treeview">
  <ul id="tree-root">
    {tree_html_full}
  </ul>
</div>
{enums_section}
<script>
function expandAll() {{
    document.querySelectorAll('.nested').forEach(el => el.classList.add('active'));
    document.querySelectorAll('.caret').forEach(el => el.classList.add('caret-down'));
}}
function collapseAll() {{
    document.querySelectorAll('.nested').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.caret').forEach(el => el.classList.remove('caret-down'));
}}
document.querySelectorAll('.caret').forEach(function(el) {{
    el.addEventListener('click', function() {{
        var ul = this.parentElement.querySelector('.nested');
        if(ul) {{ ul.classList.toggle('active'); }}
        this.classList.toggle('caret-down');
    }});
}});
document.querySelectorAll('.treeview > ul > li > .caret').forEach(function(el) {{
    el.click(); // Otevři první úroveň automaticky
}});
</script>
</body>
</html>
"""

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html_code_full)

print(f"✅ Hotovo! Výsledek je v souboru: {HTML_PATH}")
