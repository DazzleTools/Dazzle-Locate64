"""Add hfcroot.props import to all vcxproj files in Locate subdirectories."""
import os
import glob

locate_dir = os.path.dirname(os.path.abspath(__file__))
props_path = os.path.join(locate_dir, "hfcroot.props")

for vcxproj in glob.glob(os.path.join(locate_dir, "*", "*.vcxproj")):
    with open(vcxproj, "r", encoding="utf-8-sig") as f:
        content = f.read()

    if "hfcroot.props" in content:
        print(f"  SKIP: {os.path.basename(vcxproj)} (already has import)")
        continue

    target = '<Import Project="$(VCTargetsPath)\\Microsoft.Cpp.props" />'
    if target not in content:
        print(f"  WARN: {os.path.basename(vcxproj)} (target string not found)")
        continue

    proj_dir = os.path.dirname(vcxproj)
    rel = os.path.relpath(props_path, proj_dir)
    replacement = target + '\n  <Import Project="' + rel + '" />'
    content = content.replace(target, replacement)

    with open(vcxproj, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  OK: {os.path.basename(vcxproj)} (rel: {rel})")
