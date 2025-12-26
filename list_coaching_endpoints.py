"""
List all coaching system endpoints
"""
from main import app

print("\nCoaching System Endpoints:")
print("=" * 60)
coaching_routes = []
for route in app.routes:
    if hasattr(route, 'path') and '/coaching' in route.path:
        methods = ', '.join(route.methods) if hasattr(route, 'methods') else 'N/A'
        coaching_routes.append((methods, route.path))

# Sort by path
coaching_routes.sort(key=lambda x: x[1])

for methods, path in coaching_routes:
    print(f"  {methods:20} {path}")

print(f"\nTotal coaching endpoints: {len(coaching_routes)}")
print("=" * 60)

