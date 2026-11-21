"""Materialize the reviewed module inside an isolated existing admin checkout."""

import argparse
import shutil
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("host_checkout", type=Path)
args = parser.parse_args()
root = Path(__file__).parent
host = args.host_checkout.resolve()
menu = host / "app/_components/adminMenu.ts"
manifest = host / "src/admin/adminNavigationRouteManifest.ts"
if not menu.is_file() or not (host / "src/auth/internalApiGuard.ts").is_file():
    raise SystemExit("Existing administrator app and auth guard required")
updates: dict[Path, str] = {}
text = menu.read_text()
entry = '  { group: "주간 운영", href: "/admin/ai-search-weekly", label: "AI Search 주간 운영표" },\n'
anchor = '  { group: "주간 운영", href: "/weekly", label: "위클리" },\n'
if entry not in text:
    if text.count(anchor) != 1:
        raise SystemExit("Administrator menu changed; inspect before applying")
    updates[menu] = text.replace(anchor, anchor + entry)
if manifest.exists():
    text = manifest.read_text()
    entry = ('  adminRoute("/admin/ai-search-weekly", "server", ["supabase"], "main h1", undefined, '
             '"app/(admin)/admin/ai-search-weekly/weekly-client.tsx"),\n')
    anchor = '  adminRoute("/admin", "server", ["supabase", "local-files"]),\n'
    old_entry = '  adminRoute("/admin/ai-search-weekly", "server", ["supabase"]),\n'
    if old_entry in text:
        text = text.replace(old_entry, entry)
        updates[manifest] = text
    elif entry not in text:
        if text.count(anchor) != 1:
            raise SystemExit("Navigation manifest changed; inspect before applying")
        updates[manifest] = text.replace(anchor, anchor + entry)
menu_test = host / "tests/adminMenuIa.test.ts"
if menu_test.exists():
    text = menu_test.read_text()
    text = text.replace('expect(member).toHaveLength(10)', 'expect(member).toHaveLength(11)')
    text = text.replace('멤버 가시 항목은 10개', '멤버 가시 항목은 11개')
    updates[menu_test] = text
for source in (root / "overlay").rglob("*"):
    if source.is_file():
        destination = host / source.relative_to(root / "overlay")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
migration = root.parents[1] / "supabase/migrations/20261029090000_admin_ai_search_weekly.sql"
destination = host / "supabase/migrations" / migration.name
destination.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(migration, destination)
for path, updated in updates.items():
    path.write_text(updated)
print("PASS: administrator module added; existing menus and pages retained")
